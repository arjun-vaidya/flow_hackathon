import asyncio
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from gradient.coordinator import ResearchCoordinator
from gradient.models import ResearchResult, RunLimits, SourceRequest
from gradient.research import EvidenceOrganizer, ResultOrganizer
from gradient.sources.akta import AktaSource
from gradient.sources.github import GitHubSource
from gradient.sources.registry import SourceRegistry


class ResearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    thesis: str = Field(min_length=1, max_length=2000)
    # Explicit queries avoid presenting a raw thesis keyword search as LLM planning.
    github_query: str | None = Field(default=None, min_length=1, max_length=256)
    sources: list[Annotated[str, Field(min_length=1, max_length=64)]] = Field(
        default_factory=lambda: ["github", "akta"],
        min_length=1,
        max_length=6,
    )
    requests: list[SourceRequest] | None = Field(default=None, min_length=1, max_length=8)


def create_app(
    registry: SourceRegistry | None = None,
    limits: RunLimits | None = None,
    organizer_factory: Callable[[], ResultOrganizer] = EvidenceOrganizer,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=6, max_keepalive_connections=6),
        ) as client:
            app.state.registry = registry or SourceRegistry(
                GitHubSource(client, os.getenv("GITHUB_TOKEN")),
                AktaSource(client, os.getenv("AKTA_API_KEY")),
            )
            app.state.run_lock = asyncio.Lock()
            yield

    app = FastAPI(title="Gradient research collection", version="0.1.0", lifespan=lifespan)
    origins = os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins.split(",")],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok", "phase": "collection"}

    @app.get("/api/sources")
    async def sources() -> dict[str, object]:
        return {"sources": app.state.registry.describe()}

    @app.post("/api/research", response_model=ResearchResult)
    async def research(body: ResearchInput) -> JSONResponse:
        known = {source.name for source in app.state.registry.describe()}
        selected = {req.source for req in body.requests} if body.requests else set(body.sources)
        unknown = selected - known
        if unknown:
            raise HTTPException(422, f"Unknown sources: {', '.join(sorted(unknown))}")
        if body.requests:
            work = body.requests
        else:
            work = []
            if "github" in selected:
                query = body.github_query or body.thesis
                if len(query) > 256:
                    raise HTTPException(422, "Provide github_query of at most 256 characters.")
                work.append(SourceRequest(source="github", query=query, limit=6))
            if "akta" in selected:
                work.append(SourceRequest(source="akta", operation="news", query=body.thesis[:500]))
            if selected - {"github", "akta"}:
                raise HTTPException(422, "Custom sources require explicit requests.")
        lock = app.state.run_lock
        if lock.locked():
            raise HTTPException(
                429, "A research run is already active.", headers={"Retry-After": "5"}
            )
        async with lock:
            coordinator = ResearchCoordinator(app.state.registry, limits)
            result = await coordinator.run(body.thesis, work, organizer=organizer_factory())
        # Completion describes evidence collection, not the still-unimplemented agent synthesis.
        result = result.model_copy(
            update={
                "warnings": (
                    *result.warnings,
                    "Collection only: model research, investor briefs, "
                    "Roundtable and PRISM are not connected.",
                )
            }
        )
        code = 504 if result.status == "timed_out" else 502 if result.status == "failed" else 200
        return JSONResponse(status_code=code, content=result.model_dump(mode="json"))

    return app


app = create_app()

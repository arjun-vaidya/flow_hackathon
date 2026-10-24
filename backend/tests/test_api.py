import asyncio

import httpx
from conftest import FakeSource, empty_result, make_evidence

from gradient.main import create_app
from gradient.models import RunLimits, SourceBatch
from gradient.sources.registry import SourceRegistry


async def test_api_contract_statuses_and_input_validation():
    async def healthy(request):
        return SourceBatch(evidence=(make_evidence("github"),))

    async def broken(request):
        raise RuntimeError("credential must not escape")

    app = create_app(SourceRegistry(FakeSource("github", healthy), FakeSource("bad", broken)))
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client,
    ):
        assert (await client.get("/healthz")).json()["phase"] == "collection"
        assert len((await client.get("/api/sources")).json()["sources"]) == 2
        good = await client.post("/api/research", json={"thesis": "agents", "sources": ["github"]})
        assert good.status_code == 200
        assert good.json()["phase"] == "collection"
        assert good.json()["briefs"] == []
        assert good.json()["evidence"][0]["evidence_id"]
        assert good.json()["groups"][0]["evidence_ids"] == [
            good.json()["evidence"][0]["evidence_id"]
        ]
        bad = await client.post(
            "/api/research",
            json={
                "thesis": "x",
                "requests": [
                    {"source": "bad", "query": "x"},
                ],
            },
        )
        assert bad.status_code == 502
        assert "credential must not escape" not in bad.text
        for body in (
            {"thesis": " "},
            {"thesis": "x", "sources": ["not-registered"]},
            {"thesis": "x", "requests": [{"source": "github", "query": "x", "limit": 99}]},
        ):
            assert (await client.post("/api/research", json=body)).status_code == 422


async def test_overlap_returns_429_and_lock_releases_after_completion():
    started, release = asyncio.Event(), asyncio.Event()

    async def slow(request):
        started.set()
        await release.wait()
        return SourceBatch()

    app = create_app(SourceRegistry(FakeSource("github", slow)))
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client,
    ):
        body = {"thesis": "agents", "sources": ["github"]}
        first = asyncio.create_task(client.post("/api/research", json=body))
        await started.wait()
        assert (await client.post("/api/research", json=body)).status_code == 429
        release.set()
        assert (await first).status_code == 200
        assert (await client.post("/api/research", json=body)).status_code == 200


async def test_api_deadline_and_partial_result_status():
    async def stuck(request):
        await asyncio.Event().wait()

    app = create_app(
        SourceRegistry(FakeSource("github", stuck), FakeSource("fast", empty_result)),
        RunLimits(deadline_seconds=0.02, source_timeout_seconds=1),
    )
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client,
    ):
        result = await client.post("/api/research", json={"thesis": "x", "sources": ["github"]})
        assert result.status_code == 504
        partial = await client.post(
            "/api/research",
            json={
                "thesis": "x",
                "requests": [
                    {"source": "github", "query": "x"},
                    {"source": "fast", "query": "x"},
                ],
            },
        )
        assert partial.status_code == 200
        assert partial.json()["status"] == "partial"

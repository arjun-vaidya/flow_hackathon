"""Minimal real-data Scout: literal GitHub search, no model reasoning or demand scoring."""

import os

import httpx

from gradient.integration.contracts import (
    Candidate,
    Citation,
    Finding,
    ModuleContext,
    ModuleOutput,
    ModuleSpec,
)
from gradient.integration.registry import ModuleRegistry, UnavailableModule
from gradient.models import SourceRequest
from gradient.sources.github import GitHubSource


class GitHubScout:
    spec = ModuleSpec(name="scout", label="GitHub Scout · basic search", role="scout")

    def __init__(self, token: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.token = token
        self.transport = transport

    async def run(self, context: ModuleContext) -> ModuleOutput:
        common = {"run_id": context.run_id, "module_id": self.spec.name}
        query = context.thesis.strip()
        if len(query) > 256:
            return ModuleOutput(
                **common,
                status="partial",
                warnings=("Use GitHub search keywords of at most 256 characters for this Scout.",),
            )
        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=False,
            transport=self.transport,
        ) as client:
            try:
                batch = await GitHubSource(client, self.token).collect(
                    SourceRequest(
                        source="github",
                        query=query,
                        limit=3,
                        items_per_repo=3,
                    )
                )
            except httpx.HTTPStatusError as error:
                code = error.response.status_code
                message = (
                    "GitHub access was limited (403/429). Wait before retrying; an optional "
                    "GITHUB_TOKEN may help with public API limits."
                    if code in (403, 429)
                    else "GitHub rejected the request. Check search syntax and token settings."
                )
                return ModuleOutput(**common, status="partial", warnings=(message,))
            except httpx.RequestError:
                return ModuleOutput(
                    **common,
                    status="partial",
                    warnings=(
                        "Could not reach GitHub. Check the backend network connection and retry.",
                    ),
                )
        candidates = []
        findings = []
        citations = []
        for item in batch.evidence:
            citations.append(
                Citation(
                    id=item.evidence_id,
                    candidate_id=item.subject_id,
                    url=item.url,
                    title=item.title,
                    excerpt=item.excerpt,
                    source=f"GitHub {item.kind}",
                    kind="Self-reported",
                    author=f"GitHub account ID {item.author_id}" if item.author_id else None,
                    date=(
                        f"Repository created {item.published_at.date().isoformat()}"
                        if item.kind == "repository"
                        else item.published_at.isoformat()
                    )
                    if item.published_at
                    else None,
                    limitation=" ".join(item.limitations),
                )
            )
            if item.kind != "repository":
                continue
            candidates.append(
                Candidate(
                    candidate_id=item.subject_id,
                    project=item.title,
                    # A repository owner can be an organization; do not invent a founder name.
                    handle=item.title.split("/", 1)[0],
                    category="GitHub project",
                    evidence_ids=(item.evidence_id,),
                )
            )
            findings.append(
                Finding(
                    id=f"{item.evidence_id}:description",
                    candidate_id=item.subject_id,
                    field="description",
                    text=item.excerpt[:4000],
                    evidence_ids=(item.evidence_id,),
                )
            )
            findings.append(
                Finding(
                    id=f"{item.evidence_id}:unknowns",
                    candidate_id=item.subject_id,
                    field="uncertainty",
                    text="Basic keyword match only. Founder identity, thesis fit, customer demand, "
                    "company status and fundraising have not been researched. Issues and comments "
                    "are raw statements awaiting review, not verified demand.",
                )
            )
        warnings = [
            "Basic GitHub search uses your text literally, without thesis interpretation. "
            "Try agent observability or repo:langfuse/langfuse. Up to three repositories "
            "and three discussion items per repository are sampled.",
            *batch.warnings,
        ]
        if not candidates:
            warnings.append(
                "No public repositories matched. Try fewer keywords or repo:owner/name."
            )
        return ModuleOutput(
            **common,
            status=batch.status if batch.status in ("complete", "partial") else "partial",
            candidates=tuple(candidates),
            evidence=tuple(citations),
            findings=tuple(findings),
            warnings=tuple(warnings[:20]),
        )


def build_modules() -> ModuleRegistry:
    return ModuleRegistry(
        GitHubScout(os.getenv("GITHUB_TOKEN")),
        UnavailableModule("market", "Market research", "market", ("scout",)),
        UnavailableModule("verifier", "Evidence review", "verifier", ("scout", "market")),
    )

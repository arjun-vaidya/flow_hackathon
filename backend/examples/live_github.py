"""Small read-only smoke run against this public repo; no sponsor credits are spent."""

import asyncio
import json

import httpx

from gradient.coordinator import ResearchCoordinator
from gradient.models import RunLimits, SourceRequest
from gradient.sources.github import GitHubSource
from gradient.sources.registry import SourceRegistry


async def main() -> None:
    async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
        coordinator = ResearchCoordinator(
            SourceRegistry(GitHubSource(client)),
            RunLimits(deadline_seconds=20, source_timeout_seconds=10),
        )
        result = await coordinator.run(
            "Inspect our public project metadata",
            [
                SourceRequest(
                    source="github",
                    query="repo:arjun-vaidya/flow_hackathon",
                    limit=1,
                    items_per_repo=1,
                )
            ],
        )
        print(
            json.dumps(
                {
                    "status": result.status,
                    "evidence_count": len(result.evidence),
                    "source_statuses": [item.status for item in result.source_results],
                    "warnings": [
                        warning for item in result.source_results for warning in item.warnings
                    ],
                },
                indent=2,
            )
        )
        if not result.evidence:
            raise SystemExit("Live GitHub evidence was not retrieved.")


if __name__ == "__main__":
    asyncio.run(main())

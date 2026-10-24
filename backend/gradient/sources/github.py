import re
from typing import Any, Literal

import httpx
from pydantic import ValidationError

from gradient.models import Evidence, SourceBatch, SourceInfo, SourceRequest


class GitHubSource:
    def __init__(self, client: httpx.AsyncClient, token: str | None = None):
        self.client = client
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    @property
    def info(self) -> SourceInfo:
        return SourceInfo(name="github", operations=("search",), available=True)

    async def _get(self, path: str, params: dict[str, str | int] | None = None) -> Any:
        response = await self.client.get(
            f"https://api.github.com{path}",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    async def collect(self, request: SourceRequest) -> SourceBatch:
        payload = await self._get(
            "/search/repositories",
            {
                "q": f"{request.query} is:public archived:false",
                "per_page": request.limit,
            },
        )
        evidence: list[Evidence] = []
        warnings: list[str] = []
        if payload.get("incomplete_results"):
            warnings.append("GitHub reported incomplete search results.")
        if payload.get("total_count", 0) > request.limit:
            warnings.append("Repository search sampled to the configured limit.")
        for repo in payload["items"][: request.limit]:
            # Do not follow arbitrary provider-supplied API URLs, or include private repositories.
            name = repo.get("full_name", "")
            if repo.get("private", True) or not re.fullmatch(r"[\w.-]+/[\w.-]+", name):
                warnings.append("Skipped a private or invalid repository record.")
                continue
            subject = f"github:repo:{repo['id']}"
            owner = repo.get("owner") or {}
            evidence.append(
                Evidence(
                    source="github",
                    source_item_id=f"repo:{repo['id']}",
                    subject_id=subject,
                    url=repo["html_url"],
                    title=name,
                    excerpt=(repo.get("description") or "Repository has no public description.")[
                        :6000
                    ],
                    kind="repository",
                    attribution="self_reported",
                    author_id=str(owner["id"]) if owner.get("id") else None,
                    published_at=repo.get("created_at"),
                    limitations=(
                        "Repository ownership does not establish founder identity.",
                        "Description is supplied by the project; adoption is unverified.",
                    ),
                )
            )
            try:
                issues = await self._get(
                    f"/repos/{name}/issues",
                    {
                        "state": "all",
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": request.items_per_repo,
                    },
                )
            except httpx.HTTPError:
                warnings.append(
                    f"Issue collection failed for {name}; repository evidence retained."
                )
                continue
            remaining = request.items_per_repo
            for issue in issues:
                if "pull_request" in issue or not remaining:
                    continue
                try:
                    evidence.append(self._discussion(issue, subject, "issue"))
                except (ValidationError, KeyError, TypeError):
                    warnings.append(f"Skipped an invalid issue from {name}.")
                    continue
                remaining -= 1
                if not remaining or not issue.get("comments"):
                    continue
                try:
                    # Validate numbers before interpolating paths, independent of response URLs.
                    number = int(issue["number"])
                    comments = await self._get(
                        f"/repos/{name}/issues/{number}/comments",
                        {
                            "per_page": remaining,
                        },
                    )
                    for comment in comments[:remaining]:
                        try:
                            evidence.append(self._discussion(comment, subject, "comment"))
                            remaining -= 1
                        except (ValidationError, KeyError, TypeError):
                            warnings.append(f"Skipped an invalid comment from {name}.")
                except (httpx.HTTPError, ValueError):
                    warnings.append(f"Comment collection failed for {name}.")
            if len(issues) >= request.items_per_repo or remaining == 0:
                warnings.append(f"Discussion evidence for {name} is a bounded sample.")
        return SourceBatch(
            status="partial" if warnings else "complete",
            evidence=tuple(evidence),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    @staticmethod
    def _discussion(
        item: dict[str, Any], subject: str, kind: Literal["issue", "comment"]
    ) -> Evidence:
        user = item.get("user") or {}
        return Evidence(
            source="github",
            source_item_id=f"{kind}:{item['id']}",
            subject_id=subject,
            url=item["html_url"],
            title=str(item.get("title") or "GitHub comment")[:500],
            excerpt=str(item.get("body") or item.get("title") or "No text supplied.")[:6000],
            kind=kind,
            attribution="self_reported",
            author_id=str(user["id"]) if user.get("id") else None,
            published_at=item.get("created_at"),
            limitations=(
                "A public statement is not verified usage, payment, or company identity.",
            ),
        )

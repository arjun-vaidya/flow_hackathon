from typing import Any

import httpx
from pydantic import ValidationError

from gradient.models import Evidence, SourceBatch, SourceInfo, SourceRequest


class AktaSource:
    """Akta news and company enrichment; no name-based company identity guessing."""

    def __init__(self, client: httpx.AsyncClient, api_key: str | None = None):
        self.client = client
        self._api_key = api_key

    @property
    def info(self) -> SourceInfo:
        return SourceInfo(
            name="akta",
            operations=("news", "company"),
            available=bool(self._api_key),
            reason=None if self._api_key else "AKTA_API_KEY is not configured.",
        )

    async def collect(self, request: SourceRequest) -> SourceBatch:
        if not self._api_key:
            return SourceBatch(status="unavailable", warnings=("AKTA_API_KEY is not configured.",))
        if request.operation == "company":
            return await self._company(request)
        if request.operation != "news":
            return SourceBatch(status="failed", warnings=("Unsupported Akta operation.",))
        response = await self.client.get(
            "https://api.akta.pro/api/v1/news",
            headers={"x-api-key": self._api_key},
            params={"query": request.query, "limit": request.limit},
        )
        response.raise_for_status()
        payload = response.json()
        evidence: list[Evidence] = []
        warnings: list[str] = []
        for article in payload["data"][: request.limit]:
            try:
                evidence.append(self._article(article))
            except (ValidationError, KeyError, TypeError):
                warnings.append("Skipped an Akta article without valid citation data.")
        if payload.get("total", 0) > request.limit:
            warnings.append("Akta news sampled to the configured limit.")
        return SourceBatch(
            status="partial" if warnings else "complete",
            evidence=tuple(evidence),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _article(article: dict[str, Any]) -> Evidence:
        # Keep articles separate; a company mention does not prove a project/company link.
        return Evidence(
            source="akta",
            source_item_id=f"news:{article['id']}",
            subject_id=f"akta:article:{article['id']}",
            url=article["url"],
            title=article["title"][:500],
            excerpt=(article.get("ai_summary") or article["title"])[:6000],
            kind="news",
            attribution="provider_summary",
            published_at=article.get("published_date"),
            limitations=(
                "Akta-supplied summary; original article has not been independently verified.",
                "Author name is not a stable account ID; participant count excludes it.",
            ),
        )

    async def _company(self, request: SourceRequest) -> SourceBatch:
        response = await self.client.get(
            "https://api.akta.pro/api/v1/company/enrichment/",
            headers={"x-api-key": self._api_key or ""},
            params={"company": request.query, "sections": "firmographic"},
        )
        response.raise_for_status()
        data = response.json()["data"]
        company = data["firmographic"]
        # Cite the actual provider record endpoint, not the company's homepage as
        # though it were the source of third-party enrichment claims.
        evidence = Evidence(
            source="akta",
            source_item_id=f"company:{data['uuid']}",
            subject_id=f"akta:company:{data['uuid']}",
            url=str(response.request.url),
            title=company["name"][:500],
            excerpt=(
                company.get("company_description_short")
                or company.get("company_description")
                or company["name"]
            )[:6000],
            kind="company",
            attribution="provider_summary",
            limitations=(
                "Provider-supplied company description; not independently verified.",
                "Citation points to Akta's authenticated API record.",
                "No founder/project relationship is established by name similarity.",
            ),
        )
        return SourceBatch(evidence=(evidence,))

import httpx

from gradient.models import SourceRequest
from gradient.sources.akta import AktaSource
from gradient.sources.github import GitHubSource


def repository(private=False):
    return {
        "id": 123,
        "full_name": "builder/project",
        "private": private,
        "html_url": "https://github.com/builder/project",
        "description": "Agent debugger",
        "owner": {"id": 7},
        "created_at": "2026-10-01T00:00:00Z",
    }


async def test_github_uses_fixed_hosts_excludes_prs_and_honors_combined_discussion_cap():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.host == "api.github.com"
        assert request.headers["Authorization"] == "Bearer test-key"
        if request.url.path == "/search/repositories":
            assert "is:public" in request.url.params["q"]
            return httpx.Response(200, json={"items": [repository()], "total_count": 1})
        if request.url.path.endswith("/issues"):
            return httpx.Response(
                200,
                json=[
                    {"pull_request": {}, "id": 1},
                    {
                        "id": 2,
                        "number": 42,
                        "title": "Hosting?",
                        "body": "Could we pay for hosting?",
                        "comments": 10,
                        "user": {"id": 12},
                        "html_url": "https://github.com/builder/project/issues/42",
                    },
                ],
            )
        assert request.url.params["per_page"] == "1"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 3,
                    "body": "Also interested",
                    "user": {"id": 12},
                    "html_url": "https://github.com/builder/project/issues/42#issuecomment-3",
                }
            ],
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GitHubSource(client, "test-key").collect(
            SourceRequest(source="github", query="agent debugger", items_per_repo=2),
        )
    assert len(calls) == 3
    assert [item.kind for item in result.evidence] == ["repository", "issue", "comment"]
    assert all(item.attribution == "self_reported" for item in result.evidence)


async def test_github_retains_repository_when_issues_fail_and_skips_private_results():
    def handler(request):
        if request.url.path == "/search/repositories":
            return httpx.Response(
                200, json={"items": [repository(True), repository()], "incomplete_results": True}
            )
        return httpx.Response(403, json={"message": "rate limit"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GitHubSource(client).collect(SourceRequest(source="github", query="x"))
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert any("incomplete" in warning for warning in result.warnings)


async def test_akta_news_is_labeled_provider_summary_and_rejects_uncitable_records():
    def handler(request):
        assert request.url.path == "/api/v1/news"
        assert request.headers["x-api-key"] == "test-akta-key"
        assert request.url.params["query"] == "agent monitoring"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 1,
                        "title": "New agent tool",
                        "url": "https://news.example/article",
                        "ai_summary": "Provider-generated summary",
                        "author": "A name, not an ID",
                    },
                    {"id": 2, "title": "No citation"},
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = AktaSource(client, "test-akta-key")
        result = await source.collect(
            SourceRequest(source="akta", operation="news", query="agent monitoring")
        )
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert result.evidence[0].attribution == "provider_summary"
    assert result.evidence[0].author_id is None


async def test_akta_company_cites_provider_record_not_company_homepage():
    def handler(request):
        assert request.url.params["company"] == "known-id"
        assert request.url.params["sections"] == "firmographic"
        return httpx.Response(
            200,
            json={
                "data": {
                    "uuid": "known-id",
                    "firmographic": {
                        "name": "Example",
                        "website": "https://example.test",
                        "company_description_short": "A company description",
                    },
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await AktaSource(client, "test-key").collect(
            SourceRequest(
                source="akta",
                operation="company",
                query="known-id",
            )
        )
    assert result.evidence[0].url.host == "api.akta.pro"
    assert "test-key" not in result.model_dump_json()
    assert result.evidence[0].subject_id == "akta:company:known-id"


async def test_missing_akta_key_does_not_make_a_request():
    def handler(request):
        raise AssertionError("Missing credentials must not trigger HTTP")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await AktaSource(client).collect(SourceRequest(source="akta", query="x"))
    assert result.status == "unavailable"

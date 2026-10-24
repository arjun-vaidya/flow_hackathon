import httpx

from gradient.integration.aggregate import ResultAggregator
from gradient.integration.contracts import ModuleContext
from gradient.modules.github_scout import GitHubScout


def context(thesis="agent observability"):
    return ModuleContext(run_id="test-run", thesis=thesis, outputs=(), module_states={})


def repository():
    return {
        "id": 123,
        "full_name": "example/project",
        "private": False,
        "html_url": "https://github.com/example/project",
        "description": "Agent debugger",
        "owner": {"id": 42, "type": "Organization"},
        "created_at": "2026-01-01T00:00:00Z",
    }


async def test_real_scout_contract_preserves_citations_without_inventing_demand_or_founder():
    def handler(request):
        assert request.url.host == "api.github.com"
        if request.url.path == "/search/repositories":
            assert request.url.params["q"] == "agent observability is:public archived:false"
            assert request.url.params["per_page"] == "3"
            return httpx.Response(200, json={"items": [repository()], "total_count": 1})
        return httpx.Response(
            200,
            json=[
                {
                    "id": 9,
                    "number": 1,
                    "title": "Hosted version?",
                    "body": "Could you host this?",
                    "html_url": "https://github.com/example/project/issues/1",
                    "user": {"id": 77},
                }
            ],
        )

    module = GitHubScout(transport=httpx.MockTransport(handler))
    output = await module.run(context())
    aggregate = ResultAggregator("test-run")
    aggregate.accept(module.spec, output)
    item = aggregate.build()[0][0]
    assert item.project == "example/project"
    assert item.name == "Builder identity unknown"
    assert item.handle == "example"
    assert item.reviewStatus == "pending"
    assert item.recommendation == "Needs validation"
    assert item.demand == "Customer demand has not been established."
    assert len(item.evidence) == 2
    assert str(item.evidence[1].sourceUrl).endswith("/issues/1")
    assert not item.isDemo
    assert not output.reviews
    assert item.participants is None


async def test_issue_failure_retains_repository():
    def handler(request):
        if request.url.path == "/search/repositories":
            return httpx.Response(200, json={"items": [repository()]})
        return httpx.Response(403, json={"message": "rate limit"})

    output = await GitHubScout(transport=httpx.MockTransport(handler)).run(context())
    assert len(output.candidates) == 1
    assert output.status == "partial"
    assert any("Issue collection failed" in warning for warning in output.warnings)


async def test_empty_and_limited_searches_never_fabricate_results_or_leak_errors():
    empty = GitHubScout(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"items": []}))
    )
    output = await empty.run(context())
    assert not output.candidates
    assert any("No public repositories" in warning for warning in output.warnings)
    limited = GitHubScout(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(429, json={"message": "secret-value"})
        )
    )
    output = await limited.run(context())
    assert output.status == "partial"
    assert "GitHub access was limited" in output.warnings[0]
    assert "secret-value" not in output.model_dump_json()
    assert not output.candidates


async def test_long_query_is_rejected_before_network_access():
    def unexpected(request):
        raise AssertionError("Must not call GitHub for an oversized query")

    output = await GitHubScout(transport=httpx.MockTransport(unexpected)).run(context("x" * 257))
    assert not output.candidates
    assert "256" in output.warnings[0]

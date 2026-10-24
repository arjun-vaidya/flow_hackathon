import asyncio

import pytest
from conftest import FakeSource, empty_result, make_evidence

from gradient.coordinator import ResearchCoordinator
from gradient.models import RunLimits, SourceBatch, SourceRequest
from gradient.sources.registry import SourceRegistry


async def test_fast_source_checks_in_before_slow_source_and_can_schedule_followup():
    both_started = asyncio.Event()
    fast_organized = asyncio.Event()
    order = []

    async def fast(request):
        await both_started.wait()
        return SourceBatch(evidence=(make_evidence(),))

    async def slow(request):
        both_started.set()
        await fast_organized.wait()
        return SourceBatch(evidence=(make_evidence("slow"),))

    class Organizer:
        async def on_result(self, thesis, result, evidence):
            order.append(result.source)
            if result.source == "fast":
                assert evidence[0].source == "fast"
                fast_organized.set()
                return (SourceRequest(source="enrichment", query="known-company-id"),)
            return ()

    followup = FakeSource("enrichment", empty_result)
    runner = ResearchCoordinator(
        SourceRegistry(FakeSource("fast", fast), FakeSource("slow", slow), followup)
    )
    result = await asyncio.wait_for(
        runner.run(
            "agents",
            [
                SourceRequest(source="fast", query="agents"),
                SourceRequest(source="slow", query="agents"),
            ],
            organizer=Organizer(),
        ),
        timeout=1,
    )
    assert order[0] == "fast"
    assert result.status == "complete"
    assert len(result.evidence) == 2
    assert followup.calls[0].query == "known-company-id"
    assert len({event.run_id for event in result.events}) == 1
    assert all(item.run_id == result.run_id for item in result.source_results)


async def test_provider_failure_does_not_cancel_other_sources_or_leak_error():
    async def broken(request):
        raise RuntimeError("secret-api-key=never-return-this")

    async def healthy(request):
        return SourceBatch(evidence=(make_evidence("healthy"),))

    runner = ResearchCoordinator(
        SourceRegistry(FakeSource("bad", broken), FakeSource("healthy", healthy))
    )
    result = await runner.run(
        "agents", [SourceRequest(source=name, query="x") for name in ("bad", "healthy")]
    )
    assert result.status == "partial"
    assert result.evidence[0].source == "healthy"
    assert "secret-api-key" not in result.model_dump_json()


async def test_deadline_cancels_work_preserves_results_and_marks_queued_requests():
    cancelled = asyncio.Event()

    async def stuck(request):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def healthy(request):
        return SourceBatch(evidence=(make_evidence("healthy"),))

    runner = ResearchCoordinator(
        SourceRegistry(FakeSource("healthy", healthy), FakeSource("stuck", stuck)),
        RunLimits(deadline_seconds=0.04, source_timeout_seconds=1, max_concurrency=1),
    )
    result = await runner.run(
        "agents",
        [
            SourceRequest(source="healthy", query="x"),
            SourceRequest(source="stuck", query="first"),
            SourceRequest(source="stuck", query="queued"),
        ],
    )
    assert cancelled.is_set()
    assert result.status == "partial"
    assert len(result.evidence) == 1
    assert [r.status for r in result.source_results].count("timed_out") == 2


async def test_source_timeout_is_independent_of_run_deadline():
    async def stuck(request):
        await asyncio.Event().wait()

    runner = ResearchCoordinator(
        SourceRegistry(FakeSource("slow", stuck)), RunLimits(source_timeout_seconds=0.01)
    )
    result = await runner.run("agents", [SourceRequest(source="slow", query="x")])
    assert result.status == "timed_out"
    assert not result.evidence


async def test_cancelling_parent_cleans_up_inflight_sources():
    started, cancelled = asyncio.Event(), asyncio.Event()

    async def stuck(request):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    runner = ResearchCoordinator(SourceRegistry(FakeSource("slow", stuck)))
    task = asyncio.create_task(runner.run("x", [SourceRequest(source="slow", query="x")]))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set()


async def test_followups_cannot_exceed_request_or_repository_budgets():
    source = FakeSource("github", empty_result)

    class Organizer:
        async def on_result(self, thesis, result, evidence):
            return tuple(
                SourceRequest(source="github", query=f"query-{n}", limit=4) for n in range(5)
            )

    runner = ResearchCoordinator(SourceRegistry(source), RunLimits(max_requests=2))
    result = await runner.run(
        "x", [SourceRequest(source="github", query="initial", limit=4)], organizer=Organizer()
    )
    assert [request.limit for request in source.calls] == [4, 2]
    assert result.status == "partial"
    assert any("budget" in warning for warning in result.warnings)


async def test_unknown_unavailable_and_duplicate_sources_do_not_call_provider():
    disabled = FakeSource("disabled", empty_result, available=False)
    runner = ResearchCoordinator(SourceRegistry(disabled))
    result = await runner.run(
        "x",
        [
            SourceRequest(source="disabled", query="x"),
            SourceRequest(source="disabled", query="x"),
            SourceRequest(source="unknown", query="x"),
        ],
    )
    assert not disabled.calls
    assert len(result.source_results) == 2
    assert all(item.status == "unavailable" for item in result.source_results)
    assert result.status == "failed"


async def test_organizer_failure_preserves_evidence_and_run_state_is_isolated():
    async def healthy(request):
        return SourceBatch(evidence=(make_evidence("healthy", request.query),))

    class BrokenOrganizer:
        async def on_result(self, thesis, result, evidence):
            raise ValueError("do not expose this")

    runner = ResearchCoordinator(SourceRegistry(FakeSource("healthy", healthy)))
    first = await runner.run(
        "first", [SourceRequest(source="healthy", query="first")], organizer=BrokenOrganizer()
    )
    second = await runner.run("second", [SourceRequest(source="healthy", query="second")])
    assert first.status == "partial" and len(first.evidence) == 1
    assert second.status == "complete" and len(second.evidence) == 1
    assert first.run_id != second.run_id
    assert second.evidence[0].source_item_id == "second"


async def test_progress_listener_receives_transitions_and_failure_is_contained():
    events = []

    async def listener(event):
        events.append(event.state)
        if event.state == "running":
            raise RuntimeError("listener broken")

    runner = ResearchCoordinator(SourceRegistry(FakeSource("test", empty_result)))
    result = await runner.run("x", [SourceRequest(source="test", query="x")], on_progress=listener)
    assert events == ["queued", "running", "complete"]
    assert result.source_results[0].status == "complete"
    assert any("listener" in warning for warning in result.warnings)


def test_duplicate_registration_fails_loudly():
    with pytest.raises(ValueError, match="Duplicate source"):
        SourceRegistry(FakeSource("same", empty_result), FakeSource("same", empty_result))

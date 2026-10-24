import asyncio
from collections import deque
from collections.abc import Awaitable, Callable, Sequence
from time import monotonic
from uuid import uuid4

import httpx

from gradient.evidence import EvidenceStore
from gradient.models import (
    EventState,
    ResearchResult,
    RunEvent,
    RunLimits,
    SourceBatch,
    SourceRequest,
    SourceResult,
    utcnow,
)
from gradient.research import EvidenceOrganizer, ResultOrganizer
from gradient.sources.registry import SourceRegistry

ProgressListener = Callable[[RunEvent], Awaitable[None]]


class ResearchCoordinator:
    def __init__(self, registry: SourceRegistry, limits: RunLimits | None = None):
        self.registry = registry
        self.limits = limits or RunLimits()

    async def _collect(self, run_id: str, request: SourceRequest) -> SourceResult:
        started = utcnow()
        try:
            source = self.registry.get(request.source)
        except KeyError:
            source = None
        try:
            if source is None:
                batch = SourceBatch(status="unavailable", warnings=("Source is not registered.",))
            elif request.operation not in source.info.operations:
                batch = SourceBatch(status="failed", warnings=("Unsupported source operation.",))
            elif not source.info.available:
                batch = SourceBatch(
                    status="unavailable", warnings=(source.info.reason or "Source not configured.",)
                )
            else:
                async with asyncio.timeout(self.limits.source_timeout_seconds):
                    batch = await source.collect(request)
                if not isinstance(batch, SourceBatch) or any(
                    item.source != request.source for item in batch.evidence
                ):
                    raise ValueError("Invalid adapter result")
        except (TimeoutError, httpx.TimeoutException):
            batch = SourceBatch(status="timed_out", warnings=("Source time budget expired.",))
        except httpx.HTTPStatusError as error:
            # Never send provider bodies, headers, or credential-bearing URLs to the client.
            batch = SourceBatch(
                status="failed", warnings=(f"Provider returned HTTP {error.response.status_code}.",)
            )
        except Exception:
            batch = SourceBatch(status="failed", warnings=("Source request failed.",))
        return SourceResult(
            status=batch.status,
            evidence=batch.evidence,
            warnings=batch.warnings,
            run_id=run_id,
            request_id=request.request_id,
            source=request.source,
            operation=request.operation,
            started_at=started,
        )

    async def run(
        self,
        thesis: str,
        requests: Sequence[SourceRequest],
        *,
        organizer: ResultOrganizer | None = None,
        on_progress: ProgressListener | None = None,
    ) -> ResearchResult:
        run_id = str(uuid4())
        organizer = organizer or EvidenceOrganizer()
        store = EvidenceStore(self.limits.max_evidence)
        deadline = monotonic() + self.limits.deadline_seconds
        waiting: deque[SourceRequest] = deque()
        active: dict[asyncio.Task[SourceResult], SourceRequest] = {}
        seen: set[tuple[str, str, str]] = set()
        request_ids: set[str] = set()
        results: list[SourceResult] = []
        events: list[RunEvent] = []
        warnings: list[str] = []
        repositories_reserved = 0

        async def emit(request: SourceRequest, state: EventState) -> None:
            event = RunEvent(
                run_id=run_id, request_id=request.request_id, source=request.source, state=state
            )
            events.append(event)
            if on_progress:
                try:
                    async with asyncio.timeout(min(1, max(0.001, deadline - monotonic()))):
                        await on_progress(event)
                except Exception:
                    warnings.append("Progress listener failed; collection continued.")

        async def enqueue(request: SourceRequest) -> None:
            nonlocal repositories_reserved
            signature = (request.source, request.operation, request.query)
            if signature in seen or request.request_id in request_ids:
                warnings.append("Duplicate source request omitted.")
                return
            if len(seen) >= self.limits.max_requests:
                warnings.append("Source request budget exhausted; follow-up omitted.")
                return
            if request.source == "github" and request.operation == "search":
                remaining = self.limits.max_repositories - repositories_reserved
                if remaining <= 0:
                    warnings.append("Repository budget exhausted; follow-up omitted.")
                    return
                request = request.model_copy(update={"limit": min(request.limit, remaining)})
                repositories_reserved += request.limit
            seen.add(signature)
            request_ids.add(request.request_id)
            waiting.append(request)
            await emit(request, "queued")

        for request in requests:
            await enqueue(request)

        try:
            while waiting or active:
                if monotonic() >= deadline:
                    break
                while waiting and len(active) < self.limits.max_concurrency:
                    request = waiting.popleft()
                    await emit(request, "running")
                    active[asyncio.create_task(self._collect(run_id, request))] = request
                done, _ = await asyncio.wait(
                    active,
                    timeout=max(0, deadline - monotonic()),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    break
                # Collect all results already available before calling an organizer.
                completed: list[tuple[SourceRequest, SourceResult]] = []
                for task in done:
                    request = active.pop(task)
                    result = task.result()
                    results.append(result)
                    store.add(result.evidence)
                    completed.append((request, result))
                for request, result in completed:
                    await emit(request, result.status)
                    if monotonic() >= deadline:
                        continue
                    try:
                        async with asyncio.timeout(
                            min(self.limits.source_timeout_seconds, deadline - monotonic())
                        ):
                            followups = await organizer.on_result(thesis, result, store.snapshot())
                        for followup in followups:
                            # Revalidate model output before it can become a source request.
                            await enqueue(SourceRequest.model_validate(followup))
                    except Exception:
                        warnings.append(
                            "Organizer failed or timed out; collected evidence retained."
                        )

            # A finished task must not be discarded merely because a callback used up the deadline.
            for task, request in list(active.items()):
                if task.done() and not task.cancelled():
                    result = task.result()
                    results.append(result)
                    store.add(result.evidence)
                    await emit(request, result.status)
                    del active[task]
            unfinished = [*active.values(), *waiting]
            if unfinished:
                warnings.append("Run deadline reached; unfinished sources were cancelled.")
                for request in unfinished:
                    results.append(
                        SourceResult(
                            run_id=run_id,
                            request_id=request.request_id,
                            source=request.source,
                            operation=request.operation,
                            started_at=utcnow(),
                            status="timed_out",
                            warnings=("Run deadline expired before source completion.",),
                        )
                    )
                    await emit(request, "timed_out")
        finally:
            # Also runs if the HTTP request/task is cancelled; never swallow CancelledError.
            for task in active:
                task.cancel()
            if active:
                await asyncio.gather(*active, return_exceptions=True)

        warnings.extend(store.warnings)
        usable = any(r.status in ("complete", "partial") or r.evidence for r in results)
        if not usable:
            status = "timed_out" if any(r.status == "timed_out" for r in results) else "failed"
        elif warnings or any(r.status != "complete" for r in results):
            status = "partial"
        else:
            status = "complete"
        return ResearchResult(
            run_id=run_id,
            thesis=thesis,
            status=status,
            evidence=store.snapshot(),
            groups=store.groups(),
            source_results=tuple(results),
            events=tuple(events),
            warnings=tuple(dict.fromkeys(warnings)),
        )

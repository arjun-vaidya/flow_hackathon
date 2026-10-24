import asyncio
import time
from dataclasses import dataclass, field
from uuid import uuid4

from gradient.integration.aggregate import ResultAggregator
from gradient.integration.contracts import (
    ModuleContext,
    ModuleOutput,
    ModuleProgress,
    RunSnapshot,
    RunState,
)
from gradient.integration.registry import ModuleRegistry


@dataclass
class Run:
    id: str
    thesis: str
    aggregate: ResultAggregator
    progress: dict[str, ModuleProgress]
    status: RunState = "queued"
    created: float = field(default_factory=time.monotonic)
    task: asyncio.Task[None] | None = None


class RunManager:
    """Process-local bounded runner. Modules own research; this owns coordination."""

    def __init__(
        self,
        registry: ModuleRegistry,
        timeout: float = 120,
        module_timeout: float = 60,
        ttl: float = 3600,
        capacity: int = 20,
    ):
        self.registry = registry
        self.timeout = timeout
        self.module_timeout = module_timeout
        self.ttl = ttl
        self.capacity = capacity
        self.runs: dict[str, Run] = {}

    def prune(self) -> None:
        for key, run in list(self.runs.items()):
            if (
                run.status not in ("queued", "running")
                and time.monotonic() - run.created > self.ttl
            ):
                del self.runs[key]

    def start(self, thesis: str) -> Run:
        self.prune()
        if any(run.status in ("queued", "running") for run in self.runs.values()):
            raise RuntimeError("A research run is already active. Wait or cancel it first.")
        while len(self.runs) >= self.capacity:
            del self.runs[next(iter(self.runs))]
        key = str(uuid4())
        run = Run(
            key,
            thesis,
            ResultAggregator(key, demo=self.registry.demo),
            {
                name: ModuleProgress(name=name, label=module.spec.label, role=module.spec.role)
                for name, module in self.registry.modules.items()
            },
        )
        self.runs[key] = run
        run.task = asyncio.create_task(self.execute(run))
        return run

    def get(self, key: str) -> Run:
        self.prune()
        return self.runs[key]

    def snapshot(self, run: Run) -> RunSnapshot:
        opportunities, warnings = run.aggregate.build()
        return RunSnapshot(
            run_id=run.id,
            thesis=run.thesis,
            mode="demo" if self.registry.demo else "live",
            status=run.status,
            modules=tuple(run.progress.values()),
            opportunity_count=len(opportunities),
            warnings=(
                "Runs stay in memory: one hour maximum, lost on restart or capacity eviction.",
                *warnings,
            ),
        )

    async def execute(self, run: Run) -> None:
        run.status = "running"
        done = {name: asyncio.Event() for name in run.progress}

        async def invoke(name: str) -> None:
            module = self.registry.modules[name]

            def update(status, message=None):
                run.progress[name] = run.progress[name].model_copy(
                    update={"status": status, "message": message}
                )

            try:
                for dependency in module.spec.depends_on:
                    await done[dependency].wait()
                if not module.spec.available:
                    update("unavailable", "Peter's research module is not connected yet.")
                    return
                update("running")
                context = ModuleContext(
                    run_id=run.id,
                    thesis=run.thesis,
                    outputs=tuple(
                        output.model_copy(deep=True) for output in run.aggregate.outputs.values()
                    ),
                    module_states={key: progress.status for key, progress in run.progress.items()},
                )
                async with asyncio.timeout(self.module_timeout):
                    result = await module.run(context)
                output = ModuleOutput.model_validate(result.model_dump())
                run.aggregate.accept(module.spec, output)
                update(output.status)
            except TimeoutError:
                update("timed_out", "Module exceeded its time budget.")
            except asyncio.CancelledError:
                update("cancelled", "Run stopped before this module completed.")
                raise
            except Exception:
                # Do not leak provider errors, request headers or secrets into the UI.
                update(
                    "failed",
                    "Module failed or returned an invalid output. Check its implementation.",
                )
            finally:
                done[name].set()

        tasks = [asyncio.create_task(invoke(name)) for name in run.progress]
        try:
            async with asyncio.timeout(self.timeout):
                await asyncio.gather(*tasks)
            statuses = {progress.status for progress in run.progress.values()}
            _, warnings = run.aggregate.build()
            run.status = (
                "complete"
                if statuses == {"complete"} and not warnings
                else ("partial" if run.aggregate.outputs else "failed")
            )
        except TimeoutError:
            run.status = "timed_out"
        except asyncio.CancelledError:
            run.status = "cancelled"
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def cancel(self, run: Run) -> None:
        if run.task and not run.task.done():
            run.task.cancel()
            await asyncio.gather(run.task, return_exceptions=True)
            run.status = "cancelled"
            for name, progress in run.progress.items():
                if progress.status in ("queued", "running"):
                    run.progress[name] = progress.model_copy(update={"status": "cancelled"})

    async def close(self) -> None:
        for run in self.runs.values():
            await self.cancel(run)

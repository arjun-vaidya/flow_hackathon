import asyncio

import pytest
from fastapi.testclient import TestClient

from gradient.integration.aggregate import ResultAggregator
from gradient.integration.contracts import Finding, ModuleContext, ModuleOutput, ModuleSpec, Review
from gradient.integration.fixtures import build_modules
from gradient.integration.registry import ModuleRegistry, load_modules
from gradient.integration.service import RunManager
from gradient.main import create_app


async def fixture_outputs(run_id="run"):
    registry = build_modules()
    outputs = []
    for module in registry.modules.values():
        context = ModuleContext(
            run_id=run_id, thesis="replay", outputs=tuple(outputs), module_states={}
        )
        outputs.append(await module.run(context))
    return registry, outputs


@pytest.mark.asyncio
async def test_order_independent_assembly_review_and_replay():
    registry, outputs = await fixture_outputs()
    first, second = ResultAggregator("run"), ResultAggregator("run")
    for output in outputs:
        first.accept(registry.modules[output.module_id].spec, output)
    for output in reversed(outputs):
        second.accept(registry.modules[output.module_id].spec, output)
        second.accept(registry.modules[output.module_id].spec, output)
    assert first.build() == second.build()
    items, warnings = first.build()
    assert not warnings
    assert items[0].reviewStatus == "reviewed"
    assert items[0].participants is None
    assert items[0].activity == ()
    assert "Synthetic market" in items[0].market
    with pytest.raises(ValueError, match="different run"):
        first.accept(
            registry.modules["scout"].spec, outputs[0].model_copy(update={"run_id": "wrong"})
        )


@pytest.mark.asyncio
async def test_uncited_and_cross_candidate_claims_excluded():
    registry, outputs = await fixture_outputs()
    aggregate = ResultAggregator("run")
    aggregate.accept(registry.modules["scout"].spec, outputs[0])
    aggregate.accept(
        ModuleSpec(name="extra", label="Extra", role="market"),
        ModuleOutput(
            run_id="run",
            module_id="extra",
            findings=(
                Finding(
                    id="bad", candidate_id="fixture:replay", field="market", text="Uncited claim"
                ),
                Finding(
                    id="cross",
                    candidate_id="another",
                    field="demand",
                    text="Cross entity",
                    evidence_ids=("fixture:identity",),
                ),
            ),
        ),
    )
    items, warnings = aggregate.build()
    assert len(warnings) == 2
    assert items[0].reviewStatus == "pending"
    assert items[0].recommendation == "Needs validation"
    assert "Uncited claim" not in items[0].market


@pytest.mark.asyncio
async def test_verifier_cannot_promote_without_reviewed_demand():
    registry, outputs = await fixture_outputs()
    aggregate = ResultAggregator("run")
    aggregate.accept(registry.modules["scout"].spec, outputs[0])
    aggregate.accept(
        registry.modules["verifier"].spec,
        ModuleOutput(
            run_id="run",
            module_id="verifier",
            reviews=(
                Review(
                    candidate_id="fixture:replay",
                    recommendation="Worth a conversation",
                    accepted_finding_ids=("fixture:description",),
                ),
            ),
        ),
    )
    items, _ = aggregate.build()
    assert items[0].recommendation == "Needs validation"
    assert "requires a reviewed demand" in items[0].uncertainty


class Stub:
    def __init__(self, name, dependencies=(), action=None):
        self.spec = ModuleSpec(name=name, label=name, role="scout", depends_on=dependencies)
        self.action = action

    async def run(self, context):
        if self.action:
            await self.action(context)
        return ModuleOutput(run_id=context.run_id, module_id=self.spec.name)


@pytest.mark.asyncio
async def test_independent_modules_concurrent_and_dependencies_wait():
    arrived = set()
    both_started = asyncio.Event()

    def action(name):
        async def independent(context):
            arrived.add(name)
            if len(arrived) == 2:
                both_started.set()
            await asyncio.wait_for(both_started.wait(), 1)

        return independent

    async def dependent(context):
        assert context.module_states["a"] == context.module_states["b"] == "complete"
        assert {output.module_id for output in context.outputs} == {"a", "b"}

    service = RunManager(
        ModuleRegistry(
            Stub("a", action=action("a")),
            Stub("b", action=action("b")),
            Stub("c", ("a", "b"), dependent),
        )
    )
    run = service.start("test")
    await run.task
    assert run.status == "complete"


@pytest.mark.asyncio
async def test_failure_timeout_partial_and_cancellation():
    async def fail(context):
        raise ValueError("secret-token")

    async def slow(context):
        await asyncio.sleep(10)

    async def receives_failure(context):
        assert context.module_states["bad"] == "failed"

    service = RunManager(
        ModuleRegistry(
            Stub("bad", action=fail),
            Stub("slow", action=slow),
            Stub("dependent", ("bad",), receives_failure),
        ),
        module_timeout=0.02,
    )
    run = service.start("test")
    with pytest.raises(RuntimeError):
        service.start("concurrent")
    await run.task
    assert run.status == "partial"
    assert run.progress["slow"].status == "timed_out"
    assert "secret-token" not in service.snapshot(run).model_dump_json()
    next_run = service.start("cancel")
    await asyncio.sleep(0)
    await service.cancel(next_run)
    assert next_run.status == "cancelled"
    assert all(p.status not in ("queued", "running") for p in next_run.progress.values())
    service.ttl = -1
    with pytest.raises(KeyError):
        service.get(run.id)


@pytest.mark.asyncio
async def test_global_deadline_retains_completed_outputs():
    async def slow(context):
        await asyncio.sleep(10)

    service = RunManager(ModuleRegistry(Stub("fast"), Stub("slow", action=slow)), timeout=0.02)
    run = service.start("test")
    await run.task
    assert run.status == "timed_out"
    assert "fast" in run.aggregate.outputs


def test_registry_rejects_missing_dependencies_and_cycles():
    with pytest.raises(ValueError, match="Missing"):
        ModuleRegistry(Stub("a", ("missing",)))
    with pytest.raises(ValueError, match="cycle"):
        ModuleRegistry(Stub("a", ("b",)), Stub("b", ("a",)))


def test_api_handoff_and_default_unavailable(monkeypatch):
    monkeypatch.delenv("GRADIENT_MODULE_FACTORY", raising=False)
    with TestClient(create_app(modules=load_modules())) as client:
        assert not any(item["available"] for item in client.get("/api/modules").json()["modules"])
        response = client.post("/api/runs", json={"thesis": "test"})
        assert response.status_code == 202
        key = response.json()["run_id"]
        assert client.get(f"/api/runs/{key}/opportunities").json() == []
        assert client.get("/api/runs/not-found").status_code == 404
        assert client.post("/api/runs", json={"thesis": " "}).status_code == 422
    with TestClient(create_app(modules=build_modules())) as client:
        key = client.post("/api/runs", json={"thesis": "test"}).json()["run_id"]
        client.portal.call(lambda: client.app.state.modules.runs[key].task)
        status = client.get(f"/api/runs/{key}").json()
        assert status["status"] == "complete"
        assert status["mode"] == "demo"
        items = client.get(f"/api/runs/{key}/opportunities").json()
        assert items[0]["isDemo"] is True
        assert client.get(f"/api/opportunities/{items[0]['id']}").json() == items[0]
        assert client.post(f"/api/runs/{key}/cancel").json()["status"] == "complete"


@pytest.mark.asyncio
async def test_identity_conflicts_withhold_but_additional_citations_do_not():
    registry, outputs = await fixture_outputs()
    aggregate = ResultAggregator("run")
    aggregate.accept(registry.modules["scout"].spec, outputs[0])
    other = ModuleSpec(name="other", label="Other Scout", role="scout")
    citation = outputs[0].evidence[0].model_copy(update={"id": "second-identity"})
    same = outputs[0].candidates[0].model_copy(update={"evidence_ids": (citation.id,)})
    aggregate.accept(
        other,
        ModuleOutput(run_id="run", module_id="other", candidates=(same,), evidence=(citation,)),
    )
    assert len(aggregate.build()[0]) == 1
    conflict = ModuleSpec(name="conflict", label="Conflicting Scout", role="scout")
    aggregate.accept(
        conflict,
        ModuleOutput(
            run_id="run",
            module_id="conflict",
            candidates=(same.model_copy(update={"name": "Different Builder"}),),
        ),
    )
    items, warnings = aggregate.build()
    assert items == ()
    assert any("Conflicting candidate identity" in warning for warning in warnings)

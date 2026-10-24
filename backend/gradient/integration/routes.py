from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from gradient.integration.contracts import OpportunityView, RunSnapshot
from gradient.integration.service import Run, RunManager
from gradient.models import Record

router = APIRouter()


class StartRun(Record):
    thesis: str = Field(min_length=1, max_length=2000)


def manager(request: Request) -> RunManager:
    return request.app.state.modules


def lookup(request: Request, run_id: str) -> Run:
    try:
        return manager(request).get(run_id)
    except KeyError:
        raise HTTPException(404, "Run expired or was not found. Start a new search.") from None


@router.get("/api/modules")
async def modules(request: Request):
    registry = manager(request).registry
    return {
        "mode": "demo" if registry.demo else "live",
        "modules": [module.spec for module in registry.modules.values()],
    }


@router.post("/api/runs", response_model=RunSnapshot, status_code=202)
async def start(body: StartRun, request: Request):
    service = manager(request)
    try:
        run = service.start(body.thesis)
    except RuntimeError as error:
        raise HTTPException(429, str(error)) from None
    return service.snapshot(run)


@router.get("/api/runs/{run_id}", response_model=RunSnapshot)
async def status(run_id: str, request: Request):
    return manager(request).snapshot(lookup(request, run_id))


@router.post("/api/runs/{run_id}/cancel", response_model=RunSnapshot)
async def cancel(run_id: str, request: Request):
    run = lookup(request, run_id)
    await manager(request).cancel(run)
    return manager(request).snapshot(run)


@router.get("/api/runs/{run_id}/opportunities", response_model=list[OpportunityView])
async def opportunities(run_id: str, request: Request):
    return lookup(request, run_id).aggregate.build()[0]


@router.get("/api/opportunities/{opportunity_id}", response_model=OpportunityView)
async def opportunity(opportunity_id: str, request: Request):
    run = lookup(request, opportunity_id.split(":", 1)[0])
    for item in run.aggregate.build()[0]:
        if item.id == opportunity_id:
            return item
    raise HTTPException(
        404, "Opportunity is unavailable or has been withheld after evidence review."
    )

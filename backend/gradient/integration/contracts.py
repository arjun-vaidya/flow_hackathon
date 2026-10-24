from typing import Literal, Protocol

from pydantic import Field, HttpUrl

from gradient.models import Record

ModuleState = Literal[
    "queued", "running", "complete", "partial", "failed", "timed_out", "unavailable", "cancelled"
]
RunState = Literal["queued", "running", "complete", "partial", "failed", "timed_out", "cancelled"]
Recommendation = Literal["Worth a conversation", "Needs validation", "Watch"]
FieldName = Literal["description", "demand", "trigger", "thesis", "uncertainty", "market"]


class ModuleSpec(Record):
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,49}$")
    label: str = Field(min_length=1, max_length=100)
    role: Literal["scout", "market", "verifier"]
    depends_on: tuple[str, ...] = ()
    available: bool = True


class Citation(Record):
    id: str = Field(min_length=1, max_length=200)
    candidate_id: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    title: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(min_length=1, max_length=6000)
    source: str = Field(min_length=1, max_length=100)
    kind: Literal["Observed", "Self-reported", "Provider summary"]
    author: str | None = Field(default=None, max_length=200)
    date: str | None = Field(default=None, max_length=100)
    limitation: str = Field(min_length=1, max_length=2000)


class Candidate(Record):
    # Stable provider/entity identifier supplied by Scout and passed downstream.
    # A human display name is never an entity-matching key.
    candidate_id: str = Field(min_length=1, max_length=200)
    project: str = Field(min_length=1, max_length=200)
    name: str | None = Field(default=None, max_length=200)
    handle: str | None = Field(default=None, max_length=200)
    category: str = Field(default="Unclassified", max_length=200)
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=20)


class Finding(Record):
    id: str = Field(min_length=1, max_length=200)
    candidate_id: str = Field(min_length=1, max_length=200)
    field: FieldName
    text: str = Field(min_length=1, max_length=4000)
    evidence_ids: tuple[str, ...] = Field(default=(), max_length=20)


class Review(Record):
    candidate_id: str = Field(min_length=1, max_length=200)
    recommendation: Recommendation
    accepted_finding_ids: tuple[str, ...] = Field(max_length=50)
    rejected_finding_ids: tuple[str, ...] = Field(default=(), max_length=50)
    unknowns: tuple[str, ...] = Field(default=(), max_length=20)
    questions: tuple[str, ...] = Field(default=(), max_length=10)


class ModuleOutput(Record):
    schema_version: Literal[1] = 1
    run_id: str
    module_id: str
    status: Literal["complete", "partial"] = "complete"
    candidates: tuple[Candidate, ...] = Field(default=(), max_length=20)
    evidence: tuple[Citation, ...] = Field(default=(), max_length=100)
    findings: tuple[Finding, ...] = Field(default=(), max_length=100)
    reviews: tuple[Review, ...] = Field(default=(), max_length=20)
    warnings: tuple[str, ...] = Field(default=(), max_length=20)
    integration_refs: dict[str, str] = Field(default_factory=dict, max_length=20)


class ModuleContext(Record):
    run_id: str
    thesis: str
    # Immutable predecessor outputs, including independent completed branches.
    # Missing dependencies are represented in module_states rather than fabricated data.
    outputs: tuple[ModuleOutput, ...]
    module_states: dict[str, ModuleState]


class ResearchModule(Protocol):
    @property
    def spec(self) -> ModuleSpec: ...

    async def run(self, context: ModuleContext) -> ModuleOutput: ...


class ModuleProgress(Record):
    name: str
    label: str
    role: str
    status: ModuleState = "queued"
    message: str | None = None


class RunSnapshot(Record):
    run_id: str
    thesis: str
    mode: Literal["live", "demo"]
    status: RunState
    modules: tuple[ModuleProgress, ...]
    opportunity_count: int
    warnings: tuple[str, ...]


class OpportunityEvidence(Record):
    id: str
    title: str
    quote: str
    kind: str
    author: str
    source: str
    date: str
    interpretation: str
    limitation: str
    sourceUrl: HttpUrl
    isDemo: bool


class OpportunityView(Record):
    id: str
    runId: str
    candidateId: str
    name: str
    initials: str
    project: str
    handle: str
    recommendation: Recommendation
    category: str
    description: str
    demand: str
    trigger: str
    uncertainty: str
    thesis: str
    market: str
    participants: int | None = None
    hosting: int | None = None
    payment: int | None = None
    evidence: tuple[OpportunityEvidence, ...]
    questions: tuple[str, ...]
    activity: tuple[dict[str, object], ...] = ()
    isDemo: bool
    reviewStatus: Literal["pending", "reviewed", "conflicted"]
    modules: tuple[str, ...]

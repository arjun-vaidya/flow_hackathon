from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field

SourceStatus = Literal["complete", "partial", "failed", "timed_out", "unavailable"]
EventState = Literal[
    "queued", "running", "complete", "partial", "failed", "timed_out", "unavailable"
]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Evidence(Record):
    source: str = Field(min_length=1, max_length=64)
    source_item_id: str = Field(min_length=1, max_length=256)
    subject_id: str = Field(min_length=1, max_length=256)
    url: HttpUrl
    title: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(min_length=1, max_length=6000)
    kind: Literal["repository", "issue", "comment", "company", "news"]
    attribution: Literal["observed", "self_reported", "provider_summary"]
    author_id: str | None = Field(default=None, max_length=256)
    published_at: datetime | None = None
    collected_at: datetime = Field(default_factory=utcnow)
    limitations: tuple[str, ...] = ()

    @computed_field
    @property
    def evidence_id(self) -> str:
        return sha256(f"{self.source}:{self.source_item_id}".encode()).hexdigest()[:24]


class SourceRequest(Record):
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=64)
    operation: str = Field(default="search", min_length=1, max_length=64)
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=6)
    items_per_repo: int = Field(default=10, ge=1, le=10)


class SourceBatch(Record):
    status: SourceStatus = "complete"
    evidence: tuple[Evidence, ...] = ()
    warnings: tuple[str, ...] = ()


class SourceResult(SourceBatch):
    run_id: str
    request_id: str
    source: str
    operation: str
    started_at: datetime
    finished_at: datetime = Field(default_factory=utcnow)


class SourceInfo(Record):
    name: str
    operations: tuple[str, ...]
    available: bool
    reason: str | None = None


class RunEvent(Record):
    run_id: str
    request_id: str
    source: str
    state: EventState
    at: datetime = Field(default_factory=utcnow)


class EvidenceGroup(Record):
    subject_id: str
    evidence_ids: tuple[str, ...]
    participant_ids: tuple[str, ...]


class ResearchResult(Record):
    run_id: str
    thesis: str
    status: Literal["complete", "partial", "failed", "timed_out"]
    phase: Literal["collection"] = "collection"
    evidence: tuple[Evidence, ...]
    groups: tuple[EvidenceGroup, ...]
    source_results: tuple[SourceResult, ...]
    events: tuple[RunEvent, ...]
    warnings: tuple[str, ...]
    # Collection intentionally does not manufacture investor recommendations.
    briefs: tuple[dict[str, object], ...] = ()
    integration_refs: dict[str, str] = Field(default_factory=dict)


class RunLimits(Record):
    deadline_seconds: float = Field(default=120, gt=0, le=120)
    source_timeout_seconds: float = Field(default=20, gt=0, le=20)
    max_concurrency: int = Field(default=3, ge=1, le=6)
    max_requests: int = Field(default=8, ge=1, le=20)
    max_repositories: int = Field(default=6, ge=1, le=6)
    max_evidence: int = Field(default=100, ge=1, le=500)

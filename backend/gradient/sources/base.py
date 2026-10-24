from typing import Protocol

from gradient.models import SourceBatch, SourceInfo, SourceRequest


class DataSource(Protocol):
    """Adapters share a client, return attributable evidence, and honor cancellation."""

    @property
    def info(self) -> SourceInfo: ...

    async def collect(self, request: SourceRequest) -> SourceBatch: ...

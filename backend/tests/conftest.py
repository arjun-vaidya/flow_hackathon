from collections.abc import Awaitable, Callable

from gradient.models import Evidence, SourceBatch, SourceInfo, SourceRequest


def make_evidence(source: str = "fast", item: str = "1", author: str = "person-1") -> Evidence:
    return Evidence(
        source=source,
        source_item_id=item,
        subject_id=f"{source}:project:1",
        url=f"https://example.test/{source}/issues/1#comment-{item}",
        title="Hosting request",
        excerpt="Could this be hosted for our team?",
        kind="comment",
        attribution="self_reported",
        author_id=author,
    )


class FakeSource:
    def __init__(
        self,
        name: str,
        handler: Callable[[SourceRequest], Awaitable[SourceBatch]],
        available: bool = True,
    ):
        self.name = name
        self.handler = handler
        self.available = available
        self.calls: list[SourceRequest] = []

    @property
    def info(self) -> SourceInfo:
        return SourceInfo(name=self.name, available=self.available, operations=("search",))

    async def collect(self, request: SourceRequest) -> SourceBatch:
        self.calls.append(request)
        return await self.handler(request)


async def empty_result(request: SourceRequest) -> SourceBatch:
    return SourceBatch()

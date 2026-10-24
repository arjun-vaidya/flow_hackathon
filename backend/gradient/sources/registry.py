from gradient.models import SourceInfo
from gradient.sources.base import DataSource


class SourceRegistry:
    def __init__(self, *sources: DataSource):
        self._sources: dict[str, DataSource] = {}
        for source in sources:
            self.register(source)

    def register(self, source: DataSource) -> None:
        if source.info.name in self._sources:
            raise ValueError(f"Duplicate source: {source.info.name}")
        self._sources[source.info.name] = source

    def get(self, name: str) -> DataSource:
        return self._sources[name]

    def describe(self) -> tuple[SourceInfo, ...]:
        return tuple(source.info for source in self._sources.values())

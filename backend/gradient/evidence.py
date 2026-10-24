from collections import defaultdict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from gradient.models import Evidence, EvidenceGroup


def evidence_id(item: Evidence) -> str:
    return item.evidence_id


def canonical_url(item: Evidence) -> str:
    parts = urlsplit(str(item.url))
    # Preserve fragments: distinct GitHub comments share a path but not a fragment.
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")))
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, query, parts.fragment)
    )


class EvidenceStore:
    """Run-local storage. Single coordinator writer; adapters never mutate shared state."""

    def __init__(self, limit: int = 100):
        self.limit = limit
        self._items: dict[str, Evidence] = {}
        self._urls: dict[str, str] = {}
        self.warnings: list[str] = []

    def add(self, items: tuple[Evidence, ...]) -> None:
        for item in items:
            key = evidence_id(item)
            url = canonical_url(item)
            existing = self._items.get(key) or self._items.get(self._urls.get(url, ""))
            if existing:
                if existing.excerpt != item.excerpt:
                    self.warnings.append(
                        f"Conflicting excerpt for {key}; first observation retained."
                    )
                continue
            if len(self._items) >= self.limit:
                self.warnings.append("Evidence limit reached; remaining records omitted.")
                break
            self._items[key] = item
            self._urls[url] = key

    def snapshot(self) -> tuple[Evidence, ...]:
        return tuple(self._items.values())

    def groups(self) -> tuple[EvidenceGroup, ...]:
        subjects: dict[str, list[Evidence]] = defaultdict(list)
        for item in self._items.values():
            subjects[item.subject_id].append(item)
        return tuple(
            EvidenceGroup(
                subject_id=subject,
                evidence_ids=tuple(evidence_id(item) for item in items),
                # Repeated posts from one account remain one participant. This is
                # not a count of independent customers, companies, or demand.
                participant_ids=tuple(
                    sorted({f"{item.source}:{item.author_id}" for item in items if item.author_id})
                ),
            )
            for subject, items in sorted(subjects.items())
        )

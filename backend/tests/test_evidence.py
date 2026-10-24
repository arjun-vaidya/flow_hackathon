import pytest
from conftest import make_evidence
from pydantic import ValidationError

from gradient.evidence import EvidenceStore
from gradient.models import Evidence


def test_deduplicates_reposts_but_keeps_distinct_comments_and_counts_account_once():
    first = make_evidence(item="1")
    second = make_evidence(item="2")
    alias = first.model_copy(update={"source_item_id": "alias"})
    store = EvidenceStore()
    store.add((first, first, alias, second))
    assert len(store.snapshot()) == 2
    assert store.groups()[0].participant_ids == ("fast:person-1",)
    assert set(store.groups()[0].evidence_ids) == {first.evidence_id, second.evidence_id}


def test_conflicting_excerpt_is_retained_as_warning_and_evidence_limit_applies():
    first = make_evidence()
    store = EvidenceStore(limit=1)
    store.add(
        (first, first.model_copy(update={"excerpt": "Different text"}), make_evidence(item="2"))
    )
    assert store.snapshot() == (first,)
    assert len(store.warnings) == 2


def test_missing_url_and_javascript_urls_are_rejected():
    raw = make_evidence().model_dump(exclude={"evidence_id"})
    for value in (None, "", "javascript:alert(1)"):
        with pytest.raises(ValidationError):
            Evidence.model_validate({**raw, "url": value})

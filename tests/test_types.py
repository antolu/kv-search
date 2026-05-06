from __future__ import annotations

import dataclasses
import json

import pytest

from kv_search import KeywordQuery, SearchHit, SemanticResult


def test_search_hit_serializable_no_score() -> None:
    hit = SearchHit(path="notes/foo.md")
    d = dataclasses.asdict(hit)
    assert json.dumps(d) == '{"path": "notes/foo.md", "score": null, "metadata": {}}'


def test_search_hit_serializable_with_score() -> None:
    hit = SearchHit(path="notes/bar.md", score=0.85)
    d = dataclasses.asdict(hit)
    parsed = json.loads(json.dumps(d))
    assert parsed["path"] == "notes/bar.md"
    assert parsed["score"] == pytest.approx(0.85)


def test_semantic_result_serializable() -> None:
    result = SemanticResult(path="notes/baz.md", score=0.9, reasoning="matches topic")
    d = dataclasses.asdict(result)
    parsed = json.loads(json.dumps(d))
    assert parsed["path"] == "notes/baz.md"
    assert parsed["score"] == pytest.approx(0.9)
    assert parsed["reasoning"] == "matches topic"


def test_semantic_result_default_reasoning() -> None:
    result = SemanticResult(path="notes/x.md", score=0.5)
    assert not result.reasoning


def test_keyword_query_wraps_list() -> None:
    q = KeywordQuery(queries=["foo", "bar"])
    assert q.queries == ["foo", "bar"]


def test_keyword_query_frozen() -> None:
    q = KeywordQuery(queries=["foo"])
    with pytest.raises(dataclasses.FrozenInstanceError):
        q.queries = ["bar"]  # type: ignore[misc]


def test_keyword_query_subclassable() -> None:
    @dataclasses.dataclass(frozen=True)
    class LangQuery(KeywordQuery):
        language: str | None = None

    q = LangQuery(queries=["hello"], language="en")
    assert q.queries == ["hello"]
    assert q.language == "en"


def test_search_hit_metadata_default_empty() -> None:
    hit = SearchHit(path="a.md")
    assert hit.metadata == {}


def test_search_hit_metadata_populated() -> None:
    hit = SearchHit(path="a.md", metadata={"title": "Hello"})
    assert hit.metadata["title"] == "Hello"


def test_search_hit_serializable_with_metadata() -> None:
    hit = SearchHit(path="a.md", score=0.9, metadata={"title": "Hello"})
    d = dataclasses.asdict(hit)
    parsed = json.loads(json.dumps(d))
    assert parsed["metadata"] == {"title": "Hello"}


def test_types_frozen() -> None:
    hit = SearchHit(path="notes/foo.md")
    with pytest.raises(dataclasses.FrozenInstanceError):
        hit.path = "other.md"  # type: ignore[misc]

    hit_scored = SearchHit(path="notes/foo.md", score=0.5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        hit_scored.score = 0.9  # type: ignore[misc]

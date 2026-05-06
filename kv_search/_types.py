from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class KeywordQueries:
    queries: list[str]


@dataclasses.dataclass(frozen=True)
class SearchHit:
    path: str
    score: float | None = None
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True, slots=True)
class SemanticResult:
    path: str
    score: float
    reasoning: str = ""

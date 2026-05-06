from __future__ import annotations

from kv_search.__about__ import __version__
from kv_search._elasticsearch_backend import ElasticsearchKeywordBackend
from kv_search._engine import SearchEngine
from kv_search._interfaces import (
    KeywordSearchBackend,
    LLMCompletionFn,
    SemanticSearchBackend,
    VectorSearchBackend,
)
from kv_search._session import SearchSession
from kv_search._types import KeywordQueries, SearchHit, SemanticResult

__all__ = [
    "ElasticsearchKeywordBackend",
    "KeywordQueries",
    "KeywordSearchBackend",
    "LLMCompletionFn",
    "SearchEngine",
    "SearchHit",
    "SearchSession",
    "SemanticResult",
    "SemanticSearchBackend",
    "VectorSearchBackend",
    "__version__",
]

from kv_search._backends import ObsidianHttpBackend
from kv_search._engine import SearchEngine
from kv_search._interfaces import (
    KeywordSearchBackend,
    LLMCompletionFn,
    SemanticSearchBackend,
    VectorSearchBackend,
)
from kv_search._session import SearchSession
from kv_search._types import SearchHit, SemanticResult
from kv_search._version import version as __version__

__all__ = [
    "KeywordSearchBackend",
    "LLMCompletionFn",
    "ObsidianHttpBackend",
    "SearchEngine",
    "SearchHit",
    "SearchSession",
    "SemanticResult",
    "SemanticSearchBackend",
    "VectorSearchBackend",
    "__version__",
]

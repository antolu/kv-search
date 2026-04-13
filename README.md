# kv-search

Keyword, vector, and semantic hybrid search library with a pluggable backend model.

## What it does

`kv-search` provides a `SearchEngine` that combines three complementary search strategies over a corpus of documents (identified by path strings):

- **Keyword search** — exact/BM25-style matching via a `KeywordSearchBackend`
- **Vector search** — embedding similarity via a `VectorSearchBackend`, optionally constrained to an allowlist of paths from prior keyword results
- **Semantic search** — LLM-assisted reranking/reasoning via a `SemanticSearchBackend`, which receives all configured backends and an LLM callable to do whatever hybrid logic it needs

Backends are optional and pluggable — pass only what you have. The engine raises `RuntimeError` if you call a search method without a configured backend.

Each search operation runs against a `SearchSession`, which accumulates and deduplicates hits across calls. When keyword results exist in a session, vector search automatically narrows its scope to those paths (and tightens the minimum score threshold).

## Installation

```bash
pip install kv-search                        # core only
pip install "kv-search[elasticsearch]"       # with Elasticsearch keyword backend
```

## Usage

```python
import asyncio
from kv_search import SearchEngine, ElasticsearchKeywordBackend

keyword_backend = ElasticsearchKeywordBackend(
    hosts="http://localhost:9200",
    index="my-docs",
)

engine = SearchEngine(keyword_backend=keyword_backend)
session = engine.new_session()

hits = asyncio.run(engine.keyword_search(session, ["transformer attention"]))
# hits: list[SearchHit] with .path and .score
```

### Hybrid keyword + vector

```python
from kv_search import SearchEngine

engine = SearchEngine(
    keyword_backend=my_keyword_backend,
    vector_backend=my_vector_backend,
)
session = engine.new_session()

# keyword results populate the session allowlist
await engine.keyword_search(session, ["attention mechanism"])
# vector search is automatically scoped to those paths
hits = await engine.vector_search(session, "how does self-attention work?")
```

### Semantic search with an LLM

```python
engine = SearchEngine(
    keyword_backend=my_keyword_backend,
    vector_backend=my_vector_backend,
    semantic_backend=my_semantic_backend,
    llm=my_llm_fn,  # async (messages, *, system) -> str
)
session = engine.new_session()
results = await engine.semantic_search(session, "explain positional encoding")
# results: list[SemanticResult] with .path, .score, .reasoning
```

## Implementing custom backends

Subclass the relevant ABC from `kv_search`:

```python
from kv_search import KeywordSearchBackend, SearchHit

class MyKeywordBackend(KeywordSearchBackend):
    async def keyword_search(self, queries: list[str]) -> list[SearchHit]:
        ...
```

Same pattern for `VectorSearchBackend` and `SemanticSearchBackend`. The `LLMCompletionFn` is a Protocol — any async callable with the right signature works.

## Requirements

Python 3.11–3.14. The `elasticsearch` extra requires `pydantic >= 2.12.5`.

# kv-search integration design

## Context

`kv-search` is a generic hybrid search abstraction (keyword + vector + semantic) extracted from
`dragonglass`. It is released as v0.1. Two consumers are planned:

- **dragonglass** — Obsidian vault assistant; already has a local copy of the library in
  `hybrid_search/`; uses Elasticsearch-free keyword search via `ObsidianHttpBackend`
- **harmony** — on-premise LLM search engine; uses Elasticsearch with per-language indices;
  vector search not yet implemented

The goal is to make kv-search generic enough for both, migrate dragonglass off the local copy,
and scaffold harmony's future integration.

---

## Approach

Approach A: kv-search v0.2 changes first, then dragonglass migration, harmony deferred.

1. Land focused API changes in kv-search, cut v0.2
2. Migrate dragonglass against v0.2
3. Harmony scaffolding documented here but not implemented

---

## Part 1: kv-search v0.2 changes

### KeywordQuery

New frozen dataclass in `_types.py`:

```python
@dataclass(frozen=True)
class KeywordQuery:
    queries: list[str]
```

Subclassable — consumers add typed fields for backend-specific parameters (e.g.
`LanguageKeywordQuery(KeywordQuery)` adds `language: str | None`). Backends that don't need
extra fields just use `query.queries`.

`KeywordSearchBackend.keyword_search` signature changes from `list[str]` to `KeywordQuery`:

```python
async def keyword_search(self, query: KeywordQuery) -> list[SearchHit]: ...
```

The engine coerces `list[str] → KeywordQuery` before passing to the backend, so existing call
sites (`engine.keyword_search(session, ["foo", "bar"])`) continue to work unchanged.

`KeywordQuery` is added to the public exports in `__init__.py`.

### SearchHit.metadata

```python
@dataclass(frozen=True)
class SearchHit:
    path: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

Backends with richer results (title, url, snippet, domain, language) populate `metadata`.
Backends that don't leave it as an empty dict. `SemanticResult` does not get `metadata`.

### VectorQuery — not added

Vector search has no extensibility need: vector search is inherently semantic and language
detection does not apply. The existing `vector_search(query, *, top_n, min_score, allowlist)`
signature is unchanged.

---

## Part 2: dragonglass migration

### What changes

- Delete `dragonglass/hybrid_search/` entirely
- Add `kv-search >= 0.2` to `dragonglass/pyproject.toml`
- `ObsidianHttpBackend` stays in `dragonglass/search/backends.py`; its base class imports
  change from `dragonglass.hybrid_search.*` to `kv_search.*`
- All other import sites (MCP tools, agent runtime, CLI, server) updated from
  `dragonglass.hybrid_search` to `kv_search`
- `ObsidianHttpBackend.keyword_search` signature updated to accept `KeywordQuery`

### Test impact

- `tests/test_hybrid_search/` tests that duplicate kv-search's own test suite are deleted
- `ObsidianHttpBackend` tests and MCP tool tests remain

### Constraints

- No behavior changes — this is a mechanical import path migration
- kv-search must not absorb any dragonglass-specific logic

---

## Part 3: harmony scaffolding (deferred, not implemented now)

Documented here to inform kv-search design decisions.

### HarmonyKeywordBackend

Wraps harmony's existing `ElasticsearchService`. Accepts a
`LanguageKeywordQuery(KeywordQuery)` subclass:

```python
@dataclass(frozen=True)
class LanguageKeywordQuery(KeywordQuery):
    language: str | None = None
```

Language detection and multi-index fallback stay internal to the backend. Results populate
`SearchHit.metadata` with `title`, `url`, `snippet`, `domain`, `language`.

### NoOpVectorBackend

Placeholder `VectorSearchBackend` that returns `[]` for any query. Allows `SearchEngine` to
be fully instantiated while vector DB selection is deferred.

### Integration point

`SearchEngine` gets instantiated with both backends. Harmony's agentic orchestrator calls
through it instead of directly calling `ElasticsearchService`.

---

## What kv-search does NOT absorb

- Language detection logic
- Per-language index management
- Obsidian HTTP protocol details
- Any consumer-specific configuration

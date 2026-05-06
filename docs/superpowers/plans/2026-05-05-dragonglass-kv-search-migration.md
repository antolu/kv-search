# dragonglass kv-search migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dragonglass's local `hybrid_search/` copy with the `kv-search` package, updating all import sites and removing duplicated tests.

**Architecture:** Delete `dragonglass/hybrid_search/` entirely. Add `kv-search >= 0.2` as a dependency. Update `ObsidianHttpBackend`, `mcp/search/tools.py`, `agent/runtime.py`, and `cli.py` to import from `kv_search` instead of `dragonglass.hybrid_search`. Remove tests that duplicate kv-search's own suite; keep `ObsidianHttpBackend` tests and MCP tool tests.

**Tech Stack:** Python 3.11+, kv-search >= 0.2, httpx, pytest, pre-commit

**Prerequisite:** kv-search v0.2 must be installed (or installed as an editable local dep).

---

## File map

- Delete: `dragonglass/hybrid_search/__init__.py`
- Delete: `dragonglass/hybrid_search/_engine.py`
- Delete: `dragonglass/hybrid_search/_interfaces.py`
- Delete: `dragonglass/hybrid_search/_session.py`
- Delete: `dragonglass/hybrid_search/_types.py`
- Delete: `tests/test_hybrid_search/test_engine.py`
- Delete: `tests/test_hybrid_search/test_session.py`
- Delete: `tests/test_hybrid_search/test_types.py`
- Modify: `dragonglass/search/backends.py` — import from `kv_search`
- Modify: `dragonglass/mcp/search/tools.py` — import from `kv_search`
- Modify: `dragonglass/agent/runtime.py` — import from `kv_search`
- Modify: `dragonglass/cli.py` — import from `kv_search` if applicable
- Modify: `pyproject.toml` — add `kv-search >= 0.2` dependency
- Keep: `tests/test_hybrid_search/test_obsidian_backend.py`

---

### Task 1: Install kv-search and add to pyproject.toml

**Files:**
- Modify: `dragonglass/pyproject.toml`

- [ ] **Step 1: Install kv-search as editable local dep (development)**

From the dragonglass repo root:

```bash
pip install -e /Users/antonlu/code/kv-search
```

- [ ] **Step 2: Add `kv-search` to `pyproject.toml` dependencies**

Open `dragonglass/pyproject.toml` and add `"kv-search >= 0.2"` to the `dependencies` list. Do not add the `elasticsearch` extra — dragonglass does not use `ElasticsearchKeywordBackend`.

- [ ] **Step 3: Verify import works**

```bash
python -c "from kv_search import SearchEngine, SearchSession, KeywordQuery, SearchHit"
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add kv-search >= 0.2 dependency"
```

---

### Task 2: Update `ObsidianHttpBackend` imports and signature

**Files:**
- Modify: `dragonglass/search/backends.py`

`ObsidianHttpBackend.keyword_search` currently takes `queries: list[str]`. It must be updated to accept `query: KeywordQuery` and use `query.queries` internally.

- [ ] **Step 1: Update imports and signature in `backends.py`**

Replace the import block at the top:

```python
from kv_search import KeywordSearchBackend, SearchHit, VectorSearchBackend
from kv_search import KeywordQuery
```

Update `keyword_search`:

```python
async def keyword_search(self, query: KeywordQuery) -> list[SearchHit]:
    hits: list[SearchHit] = []
    seen: set[str] = set()
    async with httpx.AsyncClient(
        timeout=self._keyword_timeout, verify=False
    ) as client:
        for q in query.queries:
            for hit in await self._keyword_search_one(client, q, seen):
                seen.add(hit.path)
                hits.append(hit)
    return hits
```

Keep `_keyword_search_one` and `vector_search` unchanged except for adjusting any internal `SearchHit` references if needed (they should already work since `SearchHit` is still a frozen dataclass with `path` and `score`).

- [ ] **Step 2: Run pre-commit**

```bash
pre-commit run --all-files
```

Fix any issues.

- [ ] **Step 3: Commit**

```bash
git add dragonglass/search/backends.py
git commit -m "feat: migrate ObsidianHttpBackend to kv_search imports"
```

---

### Task 3: Update MCP tools and agent runtime imports

**Files:**
- Modify: `dragonglass/mcp/search/tools.py`
- Modify: `dragonglass/agent/runtime.py`
- Modify: `dragonglass/cli.py` (if it imports from `hybrid_search`)

- [ ] **Step 1: Update `mcp/search/tools.py`**

Change line 15:

```python
# before
from dragonglass.hybrid_search import SearchEngine, SearchSession

# after
from kv_search import SearchEngine, SearchSession
```

No other changes needed — call sites (`engine.keyword_search(session, queries)`, `engine.vector_search(...)`, `session.keyword_hits`, `session.allowlist`) are all engine-level and unchanged.

- [ ] **Step 2: Update `agent/runtime.py`**

Find all `from dragonglass.hybrid_search import` lines. Replace with `from kv_search import`.

The instantiation at line 363:

```python
backend = ObsidianHttpBackend(base_url=settings.vector_search_url)
self._engine = SearchEngine(keyword_backend=backend, vector_backend=backend)
```

`ObsidianHttpBackend` is imported from `dragonglass.search.backends` — that import stays. Only the `SearchEngine` import source changes.

- [ ] **Step 3: Check `cli.py` for any `hybrid_search` imports**

```bash
grep -n "hybrid_search" /Users/antonlu/code/dragonglass/dragonglass/cli.py
```

If any found, update them to `kv_search`.

- [ ] **Step 4: Verify no remaining hybrid_search imports**

```bash
grep -rn "dragonglass.hybrid_search\|from dragonglass.hybrid_search" /Users/antonlu/code/dragonglass/dragonglass/
```

Expected: no output.

- [ ] **Step 5: Run pre-commit**

```bash
pre-commit run --all-files
```

Fix any issues.

- [ ] **Step 6: Commit**

```bash
git add dragonglass/mcp/search/tools.py dragonglass/agent/runtime.py dragonglass/cli.py
git commit -m "feat: migrate mcp tools and agent runtime to kv_search imports"
```

---

### Task 4: Delete `hybrid_search/` module and duplicate tests

**Files:**
- Delete: `dragonglass/hybrid_search/` (entire directory)
- Delete: `tests/test_hybrid_search/test_engine.py`
- Delete: `tests/test_hybrid_search/test_session.py`
- Delete: `tests/test_hybrid_search/test_types.py`
- Keep: `tests/test_hybrid_search/test_obsidian_backend.py`

- [ ] **Step 1: Delete the `hybrid_search` module**

```bash
rm -rf /Users/antonlu/code/dragonglass/dragonglass/hybrid_search
```

- [ ] **Step 2: Delete duplicate test files**

```bash
rm -f /Users/antonlu/code/dragonglass/tests/test_hybrid_search/test_engine.py
rm -f /Users/antonlu/code/dragonglass/tests/test_hybrid_search/test_session.py
rm -f /Users/antonlu/code/dragonglass/tests/test_hybrid_search/test_types.py
```

- [ ] **Step 3: Update `test_obsidian_backend.py` imports**

```bash
grep -n "hybrid_search" /Users/antonlu/code/dragonglass/tests/test_hybrid_search/test_obsidian_backend.py
```

If it imports from `dragonglass.hybrid_search`, update to `kv_search`.

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest -vv
```

Expected: all PASS. If any test fails with `ModuleNotFoundError: dragonglass.hybrid_search`, there's a remaining import site — find it with `grep -rn "hybrid_search" /Users/antonlu/code/dragonglass/` and fix it.

- [ ] **Step 5: Commit**

```bash
git add -u
git commit -m "chore: remove hybrid_search module and duplicate tests"
```

---

### Task 5: Final verification

- [ ] **Step 1: Confirm no references to `hybrid_search` remain**

```bash
grep -rn "hybrid_search" /Users/antonlu/code/dragonglass/dragonglass/ /Users/antonlu/code/dragonglass/tests/
```

Expected: no output.

- [ ] **Step 2: Run full test suite one more time**

```bash
python -m pytest -vv
```

Expected: all PASS.

- [ ] **Step 3: Run pre-commit**

```bash
pre-commit run --all-files
```

Expected: all checks pass.

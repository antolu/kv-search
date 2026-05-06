from __future__ import annotations

import logging
import types
import typing
from collections.abc import Mapping

if typing.TYPE_CHECKING:
    from pydantic import JsonValue

from kv_search._interfaces import KeywordSearchBackend
from kv_search._types import KeywordQueries, SearchHit

logger = logging.getLogger(__name__)


def _import_elasticsearch() -> types.ModuleType:
    try:
        import elasticsearch  # noqa: PLC0415
    except ImportError:
        logger.exception(
            "Missing optional dependency for ElasticsearchKeywordBackend: elasticsearch. "
            'Install with `pip install "kv-search[elasticsearch]"`.'
        )
        raise
    return elasticsearch


class ElasticsearchKeywordBackend(KeywordSearchBackend):
    def __init__(  # noqa: PLR0913
        self,
        *,
        hosts: str | list[str],
        index: str,
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
        request_timeout: float = 10.0,
        verify_certs: bool = True,
        path_field: str = "path",
        size: int = 50,
        **extra_client_kwargs: object,
    ) -> None:
        elasticsearch = _import_elasticsearch()
        client_kwargs: dict[str, object] = {
            "hosts": hosts,
            "request_timeout": request_timeout,
            "verify_certs": verify_certs,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        elif username and password:
            client_kwargs["basic_auth"] = (username, password)
        client_kwargs.update(extra_client_kwargs)

        self._client = elasticsearch.AsyncElasticsearch(**client_kwargs)
        self._index = index
        self._path_field = path_field
        self._size = size

    async def keyword_search(self, queries: KeywordQueries) -> list[SearchHit]:
        hits: list[SearchHit] = []
        seen: set[str] = set()
        for q in queries.queries:
            try:
                query_body: dict[str, JsonValue] = {
                    "multi_match": {
                        "query": q,
                        "fields": [self._path_field, "title^2", "content"],
                    }
                }
                response = await self._client.search(
                    index=self._index,
                    query=query_body,
                    size=self._size,
                )
            except Exception:
                logger.exception("elasticsearch keyword search failed for term %r", q)
                continue

            body = typing.cast(Mapping[str, object], response)
            hits_container = body.get("hits", {})
            if not isinstance(hits_container, Mapping):
                continue
            body_hits = hits_container.get("hits", [])
            if not isinstance(body_hits, list):
                continue
            for item in body_hits:
                if not isinstance(item, Mapping):
                    continue
                source = item.get("_source", {})
                if not isinstance(source, Mapping):
                    continue
                path = source.get(self._path_field)
                if isinstance(path, str) and path not in seen:
                    seen.add(path)
                    score_raw = item.get("_score")
                    score = (
                        float(score_raw) if isinstance(score_raw, int | float) else None
                    )
                    metadata: dict[str, object] = {
                        k: v
                        for k, v in source.items()
                        if k != self._path_field
                        and isinstance(v, str | int | float | bool)
                    }
                    hits.append(SearchHit(path=path, score=score, metadata=metadata))
        return hits

    async def close(self) -> None:
        await self._client.close()

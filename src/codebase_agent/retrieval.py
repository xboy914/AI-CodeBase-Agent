import re
from collections.abc import Iterable
from typing import Any

TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+")


def tokenize(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(value) if len(token) > 1}


def chunk_key(payload: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(payload.get("path", "")),
        int(payload.get("start_line", 0)),
        int(payload.get("end_line", 0)),
    )


def lexical_score(query: str, payload: dict[str, Any]) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    score = 0.0
    for field, weight in (("symbol", 6.0), ("path", 3.0), ("kind", 2.0), ("content", 1.0)):
        value = str(payload.get(field) or "")
        field_tokens = tokenize(value)
        score += weight * len(query_tokens & field_tokens)

    normalized_query = re.sub(r"\s+", "", query).lower()
    symbol = re.sub(r"\s+", "", str(payload.get("symbol") or "")).lower()
    path = str(payload.get("path") or "").lower()
    if normalized_query and normalized_query == symbol:
        score += 12.0
    elif normalized_query and normalized_query in path:
        score += 5.0
    return score


def rank_lexical(
    query: str,
    payloads: Iterable[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    scored = [(lexical_score(query, payload), payload) for payload in payloads]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (-item[0], chunk_key(item[1])))
    return [payload for _, payload in scored[:limit]]


def reciprocal_rank_fusion(
    vector_ranking: list[dict[str, Any]],
    lexical_ranking: list[dict[str, Any]],
    limit: int,
    rank_constant: int = 60,
) -> list[dict[str, Any]]:
    scores: dict[tuple[str, int, int], float] = {}
    payload_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}

    for ranking in (vector_ranking, lexical_ranking):
        for rank, payload in enumerate(ranking, start=1):
            key = chunk_key(payload)
            payload_by_key[key] = payload
            scores[key] = scores.get(key, 0.0) + 1.0 / (rank_constant + rank)

    ordered = sorted(scores, key=lambda key: (-scores[key], key))
    return [
        {**payload_by_key[key], "retrieval_score": round(scores[key], 6)}
        for key in ordered[:limit]
    ]

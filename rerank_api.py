"""
Remote rerank helpers for Fortress Gatekeeper.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Sequence
from urllib import error, request

from fortress_models import (
    GATEKEEPER_API_BASE,
    GATEKEEPER_API_KEY,
    GATEKEEPER_INSTRUCTION,
    GATEKEEPER_MODEL_NAME,
)


def rerank_documents(
    query: str,
    documents: Sequence[str],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    instruction: Optional[str] = None,
    top_n: Optional[int] = None,
    return_documents: bool = False,
) -> list[dict[str, Any]]:
    """
    Call an OpenAI-compatible rerank endpoint and return normalized results.
    """
    normalized_documents = [document or "" for document in documents]
    if not normalized_documents:
        return []

    payload = {
        "model": model_name or GATEKEEPER_MODEL_NAME,
        "query": query or "",
        "documents": normalized_documents,
        "instruction": instruction or GATEKEEPER_INSTRUCTION,
        "return_documents": return_documents,
    }
    if top_n is not None:
        payload["top_n"] = int(top_n)

    request_url = f"{(base_url or GATEKEEPER_API_BASE).rstrip('/')}/rerank"
    http_request = request.Request(
        request_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key or GATEKEEPER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Rerank API error {exc.code}: {error_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Rerank API connection error: {exc.reason}") from exc

    parsed = json.loads(response_body)
    results = parsed.get("results")
    if not isinstance(results, list):
        raise ValueError("Rerank API response missing results list")

    normalized_results = []
    for result in results:
        normalized_results.append(
            {
                "index": int(result.get("index", 0)),
                "relevance_score": float(result.get("relevance_score", 0.0)),
                "document": result.get("document"),
            }
        )

    return normalized_results

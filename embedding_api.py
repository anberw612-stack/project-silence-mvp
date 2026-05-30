"""
Embedding API helpers for Fortress.

This module replaces all local embedding-model loading with OpenAI-compatible
API calls so Streamlit Cloud never has to download heavy model weights.
"""

import math
from typing import Optional, Sequence

from fortress_models import (
    EMBEDDING_API_BASE,
    EMBEDDING_API_KEY,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL_NAME,
    build_embedding_client,
)


def get_embedding_vectors(
    texts: Sequence[str],
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> list:
    """
    Fetch embeddings from an OpenAI-compatible API and return plain vectors.
    """
    normalized_texts = [text or "" for text in texts]
    if not normalized_texts:
        return []

    client = build_embedding_client(
        api_key=api_key or EMBEDDING_API_KEY,
        base_url=base_url or EMBEDDING_API_BASE,
    )

    vectors = []
    batch_size = max(1, EMBEDDING_BATCH_SIZE)

    for start in range(0, len(normalized_texts), batch_size):
        batch = normalized_texts[start:start + batch_size]
        response = client.embeddings.create(
            model=model or EMBEDDING_MODEL_NAME,
            input=batch,
        )
        ordered_items = sorted(response.data, key=lambda item: item.index)
        vectors.extend(item.embedding for item in ordered_items)

    return [_normalize_vector(vector) for vector in vectors]


def _clean_float(value) -> float:
    """
    Convert provider values into finite floats so malformed API numbers cannot
    poison cosine similarity calculations.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _normalize_vector(vector) -> list:
    return [_clean_float(value) for value in (vector or [])]


def cosine_similarity_score(left_vector, right_vector) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    left = _normalize_vector(left_vector)
    right = _normalize_vector(right_vector)

    if not left or len(left) != len(right):
        return 0.0

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return float(dot_product / (left_norm * right_norm))


def cosine_similarity_scores(query_vector, candidate_vectors) -> list:
    """
    Compute cosine similarities between one query vector and many candidates.
    """
    if not candidate_vectors:
        return []

    first_candidate = candidate_vectors[0]
    if isinstance(first_candidate, (int, float)):
        candidate_vectors = [candidate_vectors]

    return [
        cosine_similarity_score(query_vector, candidate_vector)
        for candidate_vector in candidate_vectors
    ]

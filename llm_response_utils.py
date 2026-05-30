"""
Helpers for cleaning and parsing MiniMax responses.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any


THINK_BLOCK_RE = re.compile(
    r"<(?:think|thought|thinking)>.*?</(?:think|thought|thinking)>",
    re.IGNORECASE | re.DOTALL,
)
CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def sanitize_llm_text(content: str | None) -> str:
    """
    Remove reasoning wrappers and markdown fences from model output.
    """
    if not content:
        return ""

    cleaned = THINK_BLOCK_RE.sub("", content).strip()
    fenced = CODE_FENCE_RE.fullmatch(cleaned)
    if fenced:
        cleaned = fenced.group(1).strip()
    return cleaned.strip()


def _extract_balanced_json_segment(text: str) -> str:
    """
    Find the first balanced JSON object or array in a string.
    """
    start = None
    opening = None
    closing = None

    for idx, char in enumerate(text):
        if char in "{[":
            start = idx
            opening = char
            closing = "}" if char == "{" else "]"
            break

    if start is None or opening is None or closing is None:
        raise ValueError("No JSON object found in model output")

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(text)):
        char = text[idx]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    raise ValueError("Incomplete JSON object in model output")


def extract_json_payload(content: str | None) -> Any:
    """
    Parse JSON from model output, tolerating <think> wrappers and prefixes.
    """
    cleaned = sanitize_llm_text(content)
    if not cleaned:
        raise ValueError("Empty model output")

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        segment = _extract_balanced_json_segment(cleaned)
        try:
            return json.loads(segment)
        except json.JSONDecodeError:
            normalized = re.sub(r",(\s*[}\]])", r"\1", segment)
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                return ast.literal_eval(normalized)

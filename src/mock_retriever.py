"""Deterministic synthetic retrieval fixture for answer-service integration.

Results follow the order in data/sample_chunks.json, regardless of the query.
They are fictional examples and must never be treated as handbook evidence.
"""

import json
from pathlib import Path
from typing import TypedDict


class RetrievedChunk(TypedDict):
    chunk_id: str
    section: str
    printed_page: int
    pdf_page: int
    text: str


_SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_chunks.json"


def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Return up to top_k fictional chunks in fixture order, without ranking."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if not query.strip():
        return []
    with _SAMPLE_PATH.open(encoding="utf-8") as fixture:
        return json.load(fixture)[:top_k]

"""Lightweight types shared by retrieval providers and their callers."""

from typing import TypedDict


class RetrievedChunk(TypedDict):
    chunk_id: str
    section: str
    printed_page: int
    pdf_page: int
    text: str


class RetrievalError(RuntimeError):
    """A retrieval index or model is unavailable or incompatible."""

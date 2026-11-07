"""Section-aware, page-bounded chunking for the PolyU handbook.

Member 1 — Handbook Processing & Data (COMP4431 group project).

The chunker takes the :class:`~pdf_processor.DocumentModel` and produces the
canonical chunks described in ``docs/member1_protocol.md``.

Invariants (enforced here, verified in tests):

* a chunk never crosses a page boundary;
* a chunk never mixes two sections;
* ``text`` is never truncated — oversized paragraphs are split on sentence
  boundaries, never mid-sentence;
* IDs are ``{section_key}_{sequence:03d}`` and unique.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

try:  # support both ``src.chunker`` and flat ``chunker`` imports
    from .pdf_processor import DocumentModel, Paragraph
except ImportError:  # pragma: no cover - flat import path
    from pdf_processor import DocumentModel, Paragraph


DEFAULT_MAX_WORDS = 450
DEFAULT_MIN_WORDS = 100

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    """One canonical handbook chunk."""

    chunk_id: str
    section: str
    printed_page: int
    pdf_page: int
    text: str

    def as_dict(self) -> dict:
        # Field order is deliberately the contract order.
        return {
            "chunk_id": self.chunk_id,
            "section": self.section,
            "printed_page": self.printed_page,
            "pdf_page": self.pdf_page,
            "text": self.text,
        }


def _word_count(text: str) -> int:
    return len(text.split())


def _split_oversized(text: str, max_words: int) -> list[str]:
    """Split one over-long paragraph on sentence boundaries.

    A single sentence longer than ``max_words`` is hard-split as a last resort so
    that no chunk can exceed the limit; this is recorded as a known limitation in
    the protocol because it can cut at a clause boundary.
    """

    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    pieces: list[str] = []
    buffer: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal buffer, count
        if buffer:
            pieces.append(" ".join(buffer).strip())
            buffer = []
            count = 0

    for sentence in sentences:
        words = _word_count(sentence)
        if words > max_words:
            flush()
            words_list = sentence.split()
            for start in range(0, len(words_list), max_words):
                pieces.append(" ".join(words_list[start : start + max_words]))
            continue
        if buffer and count + words > max_words:
            flush()
        buffer.append(sentence)
        count += words
    flush()
    return pieces or [text]


def _pack_paragraphs(
    paragraphs: list[Paragraph], max_words: int, min_words: int
) -> list[str]:
    """Pack the paragraphs of one (page, section) run into chunk texts."""

    units: list[str] = []
    for paragraph in paragraphs:
        if _word_count(paragraph.text) <= max_words:
            units.append(paragraph.text)
        else:
            units.extend(_split_oversized(paragraph.text, max_words))

    chunks: list[str] = []
    buffer: list[str] = []
    count = 0

    for unit in units:
        words = _word_count(unit)
        if buffer and count + words > max_words:
            chunks.append("\n\n".join(buffer))
            buffer = [unit]
            count = words
        else:
            buffer.append(unit)
            count += words
    if buffer:
        chunks.append("\n\n".join(buffer))

    # Merge a very short trailing chunk into its predecessor when it still fits.
    if len(chunks) > 1 and _word_count(chunks[-1]) < min_words:
        merged = chunks[-2] + "\n\n" + chunks[-1]
        if _word_count(merged) <= max_words:
            chunks[-2:] = [merged]

    return chunks


def _section_runs(paragraphs: tuple[Paragraph, ...]) -> list[tuple[str, str, list[Paragraph]]]:
    """Group a page's paragraphs into consecutive (section_key, label, paragraphs) runs."""

    runs: list[tuple[str, str, list[Paragraph]]] = []
    for paragraph in paragraphs:
        if runs and runs[-1][0] == paragraph.section_key:
            runs[-1][2].append(paragraph)
        else:
            runs.append((paragraph.section_key, paragraph.section_label, [paragraph]))
    return runs


def chunk_document(
    document: DocumentModel,
    max_words: int = DEFAULT_MAX_WORDS,
    min_words: int = DEFAULT_MIN_WORDS,
) -> list[Chunk]:
    """Turn an extracted :class:`DocumentModel` into chunks."""

    if max_words <= 0 or min_words <= 0:
        raise ValueError("max_words and min_words must be positive")
    if min_words > max_words:
        raise ValueError("min_words must not exceed max_words")

    counters: dict[str, int] = defaultdict(int)
    chunks: list[Chunk] = []

    for page in document.pages:
        for section_key, section_label, paragraphs in _section_runs(page.paragraphs):
            # A heading with no body text after it on this page (because the body
            # starts on the next page) would become a 2-3 word chunk of no use to
            # retrieval.  The heading is already carried by ``section``.
            if all(paragraph.is_heading for paragraph in paragraphs):
                continue
            for text in _pack_paragraphs(paragraphs, max_words, min_words):
                if not text.strip():
                    continue
                counters[section_key] += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"{section_key}_{counters[section_key]:03d}",
                        section=section_label,
                        printed_page=page.printed_page,
                        pdf_page=page.pdf_page,
                        text=text,
                    )
                )

    return chunks


def chunk_stats(
    document: DocumentModel, chunks: list[Chunk], max_words: int, min_words: int
) -> dict:
    """Summary statistics written next to the chunk file."""

    word_counts = [_word_count(chunk.text) for chunk in chunks]
    sections = sorted({chunk.section for chunk in chunks})
    return {
        "source_title": document.title,
        "pdf_pages_total": document.pdf_page_count,
        "body_pages": len(document.pages),
        "printed_page_min": min(page.printed_page for page in document.pages),
        "printed_page_max": max(page.printed_page for page in document.pages),
        "front_matter_pages": list(document.front_matter_pages),
        "divider_pages": list(document.divider_pages),
        "max_words": max_words,
        "min_words": min_words,
        "chunks": len(chunks),
        "sections": len(sections),
        "words_total": sum(word_counts),
        "words_min": min(word_counts) if word_counts else 0,
        "words_max": max(word_counts) if word_counts else 0,
        "words_mean": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
    }

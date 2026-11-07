"""Tests for the Member 1 handbook pipeline.

Run either way:

    pytest tests/test_member1_pipeline.py
    python tests/test_member1_pipeline.py

The tests need the handbook PDF.  Resolution order:

1. ``$HANDBOOK_PDF``
2. ``<repo>/data/handbook.pdf``

If neither exists the tests print a skip message and exit 0 (the checked-in
``data/chunks.jsonl`` can still be validated with ``scripts/validate_chunks.py``).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chunker import chunk_document  # noqa: E402
from pdf_processor import extract_handbook  # noqa: E402

PDF_PATH = Path(os.environ.get("HANDBOOK_PDF", REPO_ROOT / "data" / "handbook.pdf"))
ID_RE = re.compile(r"^(sec\d+(_[A-Z])?|app\d+(_[A-Z])?)_\d{3}$")

_RUNNING_UNDER_PYTEST = "pytest" in sys.modules

try:  # make pytest skip cleanly when the PDF is not present
    import pytest
except ImportError:  # pragma: no cover - pytest is optional
    pytest = None

if not PDF_PATH.exists() and _RUNNING_UNDER_PYTEST and pytest is not None:
    pytest.skip(f"handbook PDF not found at {PDF_PATH}", allow_module_level=True)

_document = None
_chunks = None


def _load():
    global _document, _chunks
    if _document is None:
        _document = extract_handbook(PDF_PATH)
        _chunks = chunk_document(_document)
    return _document, _chunks


# --------------------------------------------------------------------------- #
# Page map
# --------------------------------------------------------------------------- #


def test_page_map_dimensions():
    document, _ = _load()
    assert document.pdf_page_count == 137
    assert len(document.pages) == 117
    assert document.max_printed_page == 117
    assert [page.printed_page for page in document.pages] == list(range(1, 118))


def test_page_map_spot_checks():
    document, _ = _load()
    mapping = {page.pdf_page: page.printed_page for page in document.pages}
    # The plan's worked example: 5.C is printed page 33 = PDF page 45.
    assert mapping[45] == 33
    assert mapping[9] == 1
    assert mapping[137] == 117
    # The offset grows across the document, so it must not be treated as constant.
    assert 9 - mapping[9] == 8
    assert 137 - mapping[137] == 20
    assert 45 - mapping[45] == 12


def test_dividers_are_excluded():
    document, _ = _load()
    body = {page.pdf_page for page in document.pages}
    for divider in (8, 10, 14, 18, 39, 49, 62, 67, 78, 82, 84, 97, 127):
        assert divider not in body
    assert document.front_matter_pages == tuple(range(1, 8))
    assert sorted(document.divider_pages) == [8, 10, 14, 18, 39, 49, 62, 67, 78, 82, 84, 97, 127]


# --------------------------------------------------------------------------- #
# Chunk contract
# --------------------------------------------------------------------------- #


def test_chunk_schema():
    _, chunks = _load()
    for chunk in chunks:
        assert list(chunk.as_dict()) == [
            "chunk_id",
            "section",
            "printed_page",
            "pdf_page",
            "text",
        ]
        assert isinstance(chunk.chunk_id, str) and ID_RE.match(chunk.chunk_id)
        assert isinstance(chunk.section, str) and chunk.section.strip()
        assert isinstance(chunk.printed_page, int) and 1 <= chunk.printed_page <= 117
        assert isinstance(chunk.pdf_page, int) and 1 <= chunk.pdf_page <= 137
        assert chunk.text.strip()


def test_chunk_ids_are_unique():
    _, chunks = _load()
    ids = [chunk.chunk_id for chunk in chunks]
    assert len(ids) == len(set(ids))


def test_plan_example_chunk():
    _, chunks = _load()
    chunk = next(c for c in chunks if c.chunk_id == "sec5_C_001")
    assert chunk.section == "5.C Retaking of Failed Subjects"
    assert chunk.printed_page == 33
    assert chunk.pdf_page == 45
    assert "retake a subject" in chunk.text


def test_every_body_page_has_a_chunk():
    document, chunks = _load()
    covered = {chunk.printed_page for chunk in chunks}
    assert covered == {page.printed_page for page in document.pages}


def test_chunk_size_bounds():
    _, chunks = _load()
    for chunk in chunks:
        words = len(chunk.text.split())
        assert words <= 450 * 1.2, chunk.chunk_id
        assert words >= 10
    sizes = [len(chunk.text.split()) for chunk in chunks]
    assert sum(sizes) / len(sizes) > 150


def test_determinism():
    document, chunks = _load()
    again = chunk_document(document)
    assert [(c.chunk_id, c.text) for c in again] == [(c.chunk_id, c.text) for c in chunks]


def test_text_is_verbatim_from_its_page():
    import pymupdf

    document, chunks = _load()

    def squash(text: str) -> str:
        return re.sub(r"[\s\-]+", "", text)

    doc = pymupdf.open(PDF_PATH)
    try:
        raw = {
            index + 1: squash(doc[index].get_text())
            for index in range(doc.page_count)
        }
    finally:
        doc.close()

    for chunk in chunks:
        assert squash(chunk.text) in raw[chunk.pdf_page], chunk.chunk_id


# --------------------------------------------------------------------------- #
# Runner (works without pytest)
# --------------------------------------------------------------------------- #


def main() -> int:
    if not PDF_PATH.exists():
        print(f"SKIP: handbook PDF not found at {PDF_PATH}")
        print("      set HANDBOOK_PDF=/path/to/Student_Handbook_2026-27_English.pdf")
        return 0

    failures = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_")]
    for name, fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"PASS {name}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Regression checks for the appeal table correction."""
import re
import sys

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from appeal_table import candidate
from chunker import chunk_document
from pdf_processor import extract_handbook


@pytest.mark.skipif(not (ROOT / "data/handbook.pdf").is_file(), reason="handbook PDF required")
def test_candidate_preserves_text_and_identifies_table_columns():
    original = [chunk.as_dict() for chunk in chunk_document(extract_handbook(ROOT / "data/handbook.pdf"))]
    fixed = candidate(original)
    before = [c for c in original if c["chunk_id"].startswith("sec6_I_")]
    after = [c for c in fixed if c["chunk_id"].startswith("sec6_I_")]
    squash = lambda s: re.sub(r"\s+", "", s)
    for page in (56, 57, 58, 59, 60):
        assert squash("".join(c["text"] for c in before if c["pdf_page"] == page)) == squash("".join(c["text"] for c in after if c["pdf_page"] == page))
    assert len({c["chunk_id"] for c in fixed}) == len(fixed)
    by_id = {c["chunk_id"]: c for c in after}
    assert "common to subject result, de-registration and award classification" in by_id["sec6_I_002"]["section"]
    assert "subject results" in by_id["sec6_I_003"]["section"]
    assert by_id["sec6_I_003"]["text"].startswith("if there is evidence")
    assert "de-registration" in by_id["sec6_I_004"]["section"]
    assert by_id["sec6_I_004"]["text"].startswith("if a candidate has evidence")
    assert [c for c in fixed if not c["chunk_id"].startswith("sec6_I_")] == [c for c in original if not c["chunk_id"].startswith("sec6_I_")]

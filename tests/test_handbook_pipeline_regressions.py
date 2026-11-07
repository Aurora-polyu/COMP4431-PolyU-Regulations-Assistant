"""Regression checks for page mapping, validation, and safe build outputs."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import pdf_processor as processor
from validate_chunks import validate

PDF = Path(os.environ.get("HANDBOOK_PDF", ROOT / "data" / "handbook.pdf"))
needs_pdf = pytest.mark.skipif(not PDF.is_file(), reason="reference handbook unavailable")


class FakeDocument:
    page_count = 137

    def __init__(self):
        self.footers = {}
        printed = 0
        for page in range(8, 138):
            if page in processor.DIVIDER_PAGES:
                self.footers[page] = processor.DIVIDER_FOOTERS.get(page)
            else:
                printed += 1
                self.footers[page] = printed

    def __getitem__(self, index):
        return self.footers[index + 1]


def test_known_page_map_and_decorative_dividers(monkeypatch):
    monkeypatch.setattr(processor, "_footer_number", lambda page: page)
    body, front, dividers = processor._detect_page_map(FakeDocument())
    assert len(body) == 117 and body[128] == 108 and body[137] == 117
    assert front == list(range(1, 8))
    assert dividers == list(processor.DIVIDER_PAGES)
    assert 39 not in body and 127 not in body


@pytest.mark.parametrize("page,footer", [(11, None), (11, 1), (11, 3), (137, None), (127, 107)])
def test_invalid_footer_fails(monkeypatch, page, footer):
    monkeypatch.setattr(processor, "_footer_number", lambda value: value)
    document = FakeDocument()
    document.footers[page] = footer
    with pytest.raises(processor.HandbookFormatError, match=f"PDF page {page}"):
        processor._detect_page_map(document)


def test_incorrect_document_length_fails():
    document = FakeDocument()
    document.page_count = 136
    with pytest.raises(processor.HandbookFormatError, match="137 PDF pages"):
        processor._detect_page_map(document)


@needs_pdf
def test_validator_rejects_mismatched_printed_page(tmp_path):
    chunks = [json.loads(line) for line in (ROOT / "data/chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert chunks[1]["printed_page"] == chunks[2]["printed_page"] == 2
    chunks[1]["printed_page"] = 3
    path = tmp_path / "bad.jsonl"
    path.write_text("".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks), encoding="utf-8")
    errors, _ = validate(path, PDF, 450, 100)
    assert any("sec2_A_001" in error and "printed page 2, not 3" in error for error in errors)
    assert not any("printed pages without any chunk" in error for error in errors)


@needs_pdf
def test_validator_rejects_divider_page(tmp_path):
    chunks = [json.loads(line) for line in (ROOT / "data/chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    chunks[1]["pdf_page"] = 10
    path = tmp_path / "bad.jsonl"
    path.write_text("".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks), encoding="utf-8")
    errors, _ = validate(path, PDF, 450, 100)
    assert any("sec2_A_001" in error and "not a numbered body page" in error for error in errors)


@needs_pdf
def test_build_output_paths_and_reproducibility(tmp_path):
    artifacts = [ROOT / "data" / name for name in
                 ("chunks.jsonl", "chunks_stats.json", "page_map.csv", "table_pages.csv")]
    before = [hashlib.sha256(path.read_bytes()).digest() for path in artifacts]
    output = tmp_path / "check.jsonl"
    cmd = [sys.executable, str(ROOT / "scripts/build_chunks.py"), "--pdf", str(PDF), "--out", str(output)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert output.read_bytes() == artifacts[0].read_bytes()
    assert all((tmp_path / name).is_file() for name in
               ("check_stats.json", "check_page_map.csv", "check_table_pages.csv"))
    custom = [tmp_path / "custom" / name for name in ("stats.json", "map.csv", "tables.csv")]
    subprocess.run(cmd + ["--stats", str(custom[0]), "--page-map", str(custom[1]),
                          "--table-report", str(custom[2])], check=True, capture_output=True, text=True)
    assert all(path.is_file() for path in custom)
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in artifacts]

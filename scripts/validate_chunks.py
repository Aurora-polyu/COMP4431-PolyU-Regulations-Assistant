#!/usr/bin/env python3
"""Validate ``data/chunks.jsonl`` against the Member 1 contract.

Checks performed (see ``docs/member1_protocol.md`` §10):

* exactly the five contract fields, with the right types;
* unique ``chunk_id`` matching the documented pattern;
* page numbers inside the ranges of the supplied PDF;
* non-empty ``text``;
* every body page represented by at least one chunk;
* each chunk's text is a verbatim (whitespace/hyphen-insensitive) substring of its
  own PDF page, which catches cross-page leakage;
* chunk sizes within the configured bounds.

Exit code 0 when everything passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_processor import extract_handbook  # noqa: E402

REQUIRED_FIELDS = ["chunk_id", "section", "printed_page", "pdf_page", "text"]
ID_RE = re.compile(r"^(sec\d+(_[A-Z])?|app\d+(_[A-Z])?)_\d{3}$")


def _squash(text: str) -> str:
    return re.sub(r"[\s\-]+", "", text)


def validate(
    chunks_path: Path,
    pdf_path: Path | None,
    max_words: int,
    min_words: int,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not chunks_path.exists():
        return [f"Chunk file not found: {chunks_path}"], warnings

    chunks: list[dict] = []
    with chunks_path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"line {number}: invalid JSON ({exc})")

    if not chunks:
        return errors + ["chunk file is empty"], warnings

    seen_ids: set[str] = set()
    for index, chunk in enumerate(chunks, start=1):
        keys = list(chunk.keys())
        if len(keys) != len(REQUIRED_FIELDS) or set(keys) != set(REQUIRED_FIELDS):
            errors.append(f"chunk {index}: fields {keys} != {REQUIRED_FIELDS}")
            continue

        chunk_id = chunk["chunk_id"]
        if not isinstance(chunk_id, str) or not ID_RE.match(chunk_id):
            errors.append(f"chunk {index}: bad chunk_id {chunk_id!r}")
        elif chunk_id in seen_ids:
            errors.append(f"chunk {index}: duplicate chunk_id {chunk_id!r}")
        seen_ids.add(chunk_id)

        if not isinstance(chunk["section"], str) or not chunk["section"].strip():
            errors.append(f"chunk {index}: empty section")
        for field in ("printed_page", "pdf_page"):
            if not isinstance(chunk[field], int) or isinstance(chunk[field], bool):
                errors.append(f"chunk {index}: {field} is not an integer")
        if not isinstance(chunk["text"], str) or not chunk["text"].strip():
            errors.append(f"chunk {index}: empty text")

        words = len(chunk["text"].split())
        if words > max_words * 1.2:
            errors.append(
                f"chunk {index} ({chunk_id}): {words} words exceeds {max_words} * 1.2"
            )
        if words < min_words:
            warnings.append(
                f"chunk {index} ({chunk_id}): {words} words below target {min_words} "
                "(allowed at a page or section boundary)"
            )

    if pdf_path is not None and pdf_path.exists():
        document = extract_handbook(pdf_path)
        max_pdf = document.pdf_page_count
        max_printed = document.max_printed_page
        body_pages = {page.printed_page for page in document.pages}

        for index, chunk in enumerate(chunks, start=1):
            if not (1 <= chunk["printed_page"] <= max_printed):
                errors.append(
                    f"chunk {index} ({chunk['chunk_id']}): printed_page "
                    f"{chunk['printed_page']} outside 1..{max_printed}"
                )
            if not (1 <= chunk["pdf_page"] <= max_pdf):
                errors.append(
                    f"chunk {index} ({chunk['chunk_id']}): pdf_page "
                    f"{chunk['pdf_page']} outside 1..{max_pdf}"
                )

        covered = {chunk["printed_page"] for chunk in chunks}
        missing = sorted(body_pages - covered)
        if missing:
            errors.append(f"printed pages without any chunk: {missing}")

        # Text integrity against the raw PDF page.
        import pymupdf

        doc = pymupdf.open(pdf_path)
        try:
            raw = {
                page_index + 1: _squash(doc[page_index].get_text())
                for page_index in range(doc.page_count)
            }
        finally:
            doc.close()

        mismatched: dict[int, int] = {}
        for chunk in chunks:
            pdf_page = chunk["pdf_page"]
            if pdf_page not in raw:
                errors.append(f"{chunk['chunk_id']}: pdf_page {pdf_page} not in PDF")
                continue
            if _squash(chunk["text"]) not in raw[pdf_page]:
                mismatched[pdf_page] = mismatched.get(pdf_page, 0) + 1
                errors.append(
                    f"{chunk['chunk_id']}: text is not a substring of PDF page {pdf_page}"
                )
        if mismatched:
            errors.append(f"pages with integrity failures: {sorted(mismatched)}")
    else:
        print("note: no PDF supplied, skipping page-range and integrity checks")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=REPO_ROOT / "data" / "chunks.jsonl")
    parser.add_argument("--pdf", type=Path, default=REPO_ROOT / "data" / "handbook.pdf")
    parser.add_argument("--max-words", type=int, default=450)
    parser.add_argument("--min-words", type=int, default=100)
    args = parser.parse_args(argv)

    pdf = args.pdf if args.pdf.exists() else None
    errors, warnings = validate(args.chunks, pdf, args.max_words, args.min_words)

    if warnings:
        print(f"Warnings: {len(warnings)} short chunk(s)")
        for warning in warnings[:10]:
            print("  -", warning)
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")

    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for error in errors[:40]:
            print("  -", error)
        if len(errors) > 40:
            print(f"  ... and {len(errors) - 40} more")
        return 1

    print(f"OK: {args.chunks} satisfies the Member 1 contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

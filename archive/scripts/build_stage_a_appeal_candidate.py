#!/usr/bin/env python3
"""Build a review-only candidate with source-verified appeal table column labels.

This edition-specific transformation leaves the original files untouched. The
three labels are derived from the printed table layout across PDF pages 56–57;
the passage text itself remains a substring of its own source page.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_HASH = "2729978a200ca6738a4a50e44d0f5778069400a339a4f6dcc8dd50644c73665c"
PDF_HASH = "4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464"
PREFIX = "sec6_I_"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate(chunks: list[dict]) -> list[dict]:
    first = next(c for c in chunks if c["chunk_id"] == "sec6_I_001")
    second = next(c for c in chunks if c["chunk_id"] == "sec6_I_002")
    if (first["pdf_page"], second["pdf_page"]) != (56, 57):
        raise ValueError("Unexpected appeal table page mapping")
    heading = "Grounds for Appeal Appeal against Subject Result(s)"
    subject = "if there is evidence provided by a candidate or any other person that the assessments"
    dereg = "if a candidate has evidence to support that his/her assessment performance"
    after = "A student’s disagreement with the marking"
    prefix, common = first["text"].split(heading, 1)
    common = heading + common
    before, rest = second["text"].split(subject, 1)
    if before.strip():
        raise ValueError("Unexpected text before first continuation cell")
    subject_text, rest = (subject + rest).split(dereg, 1)
    dereg_text, remainder = (dereg + rest).split(after, 1)
    remainder = after + remainder
    def piece(template: dict, text: str, section: str) -> dict:
        return {**template, "section": section, "text": text.strip()}
    section = "6.I Academic Appeals"
    replacements = {
        "sec6_I_001": [piece(first, prefix, section), piece(first, common, section + " — grounds common to subject result, de-registration and award classification appeals")],
        "sec6_I_002": [piece(second, subject_text, section + " — grounds for appeal against subject results"), piece(second, dereg_text, section + " — grounds for appeal against de-registration"), piece(second, remainder, section)],
    }
    result = []
    number = 0
    for c in chunks:
        for item in replacements.get(c["chunk_id"], [c]):
            item = dict(item)
            if item["chunk_id"].startswith(PREFIX):
                number += 1
                item["chunk_id"] = f"{PREFIX}{number:03d}"
            result.append(item)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.chunks) != SOURCE_HASH or digest(args.pdf) != PDF_HASH:
        parser.error("source chunks or PDF do not match the reviewed edition")
    if args.out.resolve() in {args.chunks.resolve(), args.pdf.resolve()}:
        parser.error("output must be separate from inputs")
    if args.out.exists():
        parser.error("output already exists; choose a new path")
    chunks = [json.loads(line) for line in args.chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = candidate(chunks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        for row in result:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(result)} chunks to {args.out} (SHA-256 {digest(args.out)})")
    print("Review-only candidate: appeal section labels are derived from the PDF table layout; IDs in section 6.I change.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build ``data/chunks.jsonl`` from the handbook PDF.

Usage (from the repository root)::

    python scripts/build_chunks.py --pdf data/handbook.pdf

Optional::

    python scripts/build_chunks.py --pdf data/handbook.pdf \
        --max-words 450 --min-words 100 \
        --out data/chunks.jsonl

The script is deterministic: same PDF + same flags => same output.
See ``docs/data-and-indexing.md`` for the output contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chunker import Chunk, DEFAULT_MAX_WORDS, DEFAULT_MIN_WORDS, chunk_document, chunk_stats  # noqa: E402
from appeal_table import PDF_HASH, SOURCE_HASH, candidate  # noqa: E402
from table_annotations import annotate  # noqa: E402
from pdf_processor import extract_handbook, find_tables_report  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_page_map(path: Path, document) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pdf_page", "printed_page", "paragraphs", "words"])
        for page in document.pages:
            words = sum(len(p.text.split()) for p in page.paragraphs)
            writer.writerow([page.pdf_page, page.printed_page, len(page.paragraphs), words])


def _write_table_report(path: Path, pdf_path: Path, skip_pages: set[int]) -> int:
    rows = find_tables_report(pdf_path, skip_pages=skip_pages)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pdf_page", "table_index", "rows", "cols", "x0", "y0", "x1", "y1"])
        for row in rows:
            writer.writerow(
                [
                    row["pdf_page"],
                    row["table_index"],
                    row["rows"],
                    row["cols"],
                    row["x0"],
                    row["y0"],
                    row["x1"],
                    row["y1"],
                ]
            )
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=REPO_ROOT / "data" / "handbook.pdf")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "chunks.jsonl")
    parser.add_argument("--stats", type=Path)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--table-report", type=Path)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument(
        "--no-table-report",
        action="store_true",
        help="Skip the (slow) table scan used for the manual verification checklist.",
    )
    args = parser.parse_args(argv)

    default_out = REPO_ROOT / "data" / "chunks.jsonl"
    if args.out.resolve() == default_out.resolve():
        companion_defaults = (REPO_ROOT / "data" / "chunks_stats.json",
                              REPO_ROOT / "data" / "page_map.csv",
                              REPO_ROOT / "data" / "table_pages.csv")
    else:
        companion_defaults = (args.out.with_name(args.out.stem + "_stats.json"),
                              args.out.with_name(args.out.stem + "_page_map.csv"),
                              args.out.with_name(args.out.stem + "_table_pages.csv"))
    args.stats = args.stats or companion_defaults[0]
    args.page_map = args.page_map or companion_defaults[1]
    args.table_report = args.table_report or companion_defaults[2]

    if not args.pdf.exists():
        parser.error(
            f"PDF not found: {args.pdf}\n"
            "Place the authorised handbook at data/handbook.pdf or pass --pdf PATH."
        )

    document = extract_handbook(args.pdf)
    chunks = chunk_document(document, max_words=args.max_words, min_words=args.min_words)
    pdf_hash = _sha256(args.pdf)
    if pdf_hash == PDF_HASH:
        # Apply the reviewed layout annotations only to the exact raw extraction.
        # Fail rather than silently dropping the fix when chunking flags change.
        raw = "".join(json.dumps(c.as_dict(), ensure_ascii=False) + "\n" for c in chunks)
        if hashlib.sha256(raw.encode("utf-8")).hexdigest() != SOURCE_HASH:
            parser.error("reviewed handbook extraction differs from the baseline; review the appeal table before rebuilding")
        chunks = [Chunk(**c) for c in annotate(candidate([c.as_dict() for c in chunks]))]
    stats = chunk_stats(document, chunks, args.max_words, args.min_words)
    stats["source_sha256"] = pdf_hash
    stats["source_file"] = args.pdf.name

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.as_dict(), ensure_ascii=False) + "\n")

    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.page_map.parent.mkdir(parents=True, exist_ok=True)
    if not args.no_table_report:
        args.table_report.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_page_map(args.page_map, document)

    table_count = 0
    if not args.no_table_report:
        non_body = set(document.front_matter_pages) | set(document.divider_pages)
        table_count = _write_table_report(args.table_report, args.pdf, non_body)

    print(f"PDF pages        : {stats['pdf_pages_total']}")
    print(f"Body pages       : {stats['body_pages']} (printed {stats['printed_page_min']}-{stats['printed_page_max']})")
    print(f"Divider pages    : {len(stats['divider_pages'])}")
    print(f"Chunks           : {stats['chunks']} across {stats['sections']} sections")
    print(f"Words per chunk  : min {stats['words_min']} / mean {stats['words_mean']} / max {stats['words_max']}")
    if not args.no_table_report:
        print(f"Tables detected  : {table_count} (see {args.table_report.name})")
    print(f"Written          : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

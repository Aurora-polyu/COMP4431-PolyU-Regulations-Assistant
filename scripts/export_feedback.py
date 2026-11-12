#!/usr/bin/env python3
"""Export local feedback (ratings and reports) to CSV or JSON Lines.

Usage (from the repository root)::

    python scripts/export_feedback.py --out feedback.csv
    python scripts/export_feedback.py --out feedback.jsonl

The output is derived from ``data/user_data.sqlite`` via ``list_feedback``.
Prints the counts of likes, dislikes and reports when done.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.user_data import list_feedback

FIELDS = ["time", "message id", "rating", "reason", "comment", "question", "answer", "chunk ids"]


def _chunk_ids(feedback_row):
    return ", ".join(feedback_row.get("chunk_ids") or [])


def _rows(feedback):
    for item in feedback:
        yield [
            item.get("created_at"),
            item.get("message_id"),
            item.get("rating"),
            item.get("reason"),
            item.get("comment"),
            item.get("question"),
            item.get("answer"),
            _chunk_ids(item),
        ]


def write_csv(out: Path, feedback) -> None:
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(_rows(feedback))


def write_jsonl(out: Path, feedback) -> None:
    with out.open("w", encoding="utf-8") as handle:
        for item in feedback:
            row = {field: value for field, value in zip(FIELDS, next(_rows([item])))}
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_counts(feedback) -> None:
    likes = sum(1 for item in feedback if item.get("kind") == "rating" and item.get("rating") == 1)
    dislikes = sum(1 for item in feedback if item.get("kind") == "rating" and item.get("rating") == -1)
    reports = sum(1 for item in feedback if item.get("kind") == "report")
    print(f"Likes: {likes}  Dislikes: {dislikes}  Reports: {reports}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="output path ending in .csv or .jsonl")
    args = parser.parse_args(argv)

    if args.out.suffix.lower() not in (".csv", ".jsonl"):
        parser.error("--out must end in .csv or .jsonl")

    feedback = list_feedback()
    if args.out.suffix.lower() == ".csv":
        write_csv(args.out, feedback)
    else:
        write_jsonl(args.out, feedback)
    print(f"Wrote {len(feedback)} feedback record(s) to {args.out}")
    print_counts(feedback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

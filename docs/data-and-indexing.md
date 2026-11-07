# Data and indexing

Use an authorized 2026/27 Student Handbook for Taught Programmes PDF at `data/handbook.pdf`. Confirm permission before distributing it or derived data. The extractor is tailored to this edition and checks its expected structure; a different edition needs separate review.

The active `data/chunks.jsonl` contains one JSON object per passage, with `chunk_id`, `section`, `printed_page`, `pdf_page`, and `text`. Companion files contain chunk statistics, the PDF-to-printed-page map, and detected table locations. Table extraction can lose relationships, so inspect relevant pages and annotations against the PDF. A matching hash alone does not prove correctness.

To validate existing chunks:

```sh
python scripts/validate_chunks.py --chunks data/chunks.jsonl --pdf data/handbook.pdf
```

To prepare a candidate without overwriting the active data, use a new directory:

```sh
mkdir -p /tmp/handbook-candidate
python scripts/build_chunks.py --pdf data/handbook.pdf --out /tmp/handbook-candidate/chunks.jsonl
python scripts/validate_chunks.py --chunks /tmp/handbook-candidate/chunks.jsonl --pdf data/handbook.pdf
```

The builder writes candidate statistics, page mapping, and table report beside the specified output. For the reviewed PDF, it checks the raw extraction hash and applies the reviewed table corrections; it fails if the baseline differs. Review the candidate and tables before promoting it. Do not overwrite the current data or index merely to test the pipeline.

Build a new index after approval:

```sh
python scripts/build_index.py --chunks data/chunks.jsonl --index-dir /absolute/path/to/handbook-index
export RETRIEVAL_INDEX_DIR=/absolute/path/to/handbook-index
```

The index records the source file's absolute path and hash, the embedding model and its immutable revision. Keep that file in place and rebuild after moving or changing it. The first build may download the default embedding model; retrieval requires the recorded revision to be available locally. Set `RETRIEVAL_MODEL` before running the app when using a nondefault model.

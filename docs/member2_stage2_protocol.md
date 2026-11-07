# Member 2 Stage 2: Hybrid Retrieval Protocol

## Goal and prerequisites

Build and test a lightweight local hybrid retriever using the Stage 1 synthetic chunks. Preserve the Stage 1 contract so the answer service can replace its mock import without changing its call or handling of returned chunks. The synthetic examples are fictional: they are not evidence for real academic-regulation answers.

The source is a nonempty JSON array of chunks. Each chunk has exactly these fields:

| Field | Requirement |
|---|---|
| `chunk_id` | Unique, stable, nonblank string |
| `section` | Nonblank section identifier and title |
| `printed_page` | Positive integer printed page number |
| `pdf_page` | Positive, 1-based integer PDF page number |
| `text` | Nonblank complete passage |

Member 1 must confirm the contract and eventually provide validated handbook chunks with stable IDs and correct page mapping. Coordinate any contract change with Member 3. The existing `src.mock_retriever` and its fixture-order behavior remain available for independent answer-service development.

## Indexing workflow

1. Install the project's pinned retrieval dependencies in a Python 3.12 virtual environment. Start with `BAAI/bge-small-en-v1.5` as the candidate local embedding model; its final selection depends on a later handbook retrieval benchmark.
2. Run `python scripts/build_index.py` from the project root to build from `data/sample_chunks.json` into the local `chroma_db/` directory. Use `--chunks` and `--index-dir` to select another source and destination. An initial model download may be necessary.
3. Validate the complete input before indexing: reject missing or additional fields, blank strings, non-positive or non-integer page numbers, duplicate IDs, and an empty corpus. Index the passage as the Chroma document and store section and page fields as metadata; use the chunk ID as the document ID.
4. Build a fresh index generation from the full input and publish it only after the build succeeds. Record the source path and hash, embedding model and immutable Hub revision, query encoding configuration, and index format. Search must load that exact model revision. Rebuild when the source or embedding configuration changes; never silently use a stale index.
5. Keep local indexes, model caches, and generated handbook data out of Git. Do not add the handbook to the repository without confirming permission to share it.

## Search workflow and interface

Member 3 imports `retrieve` from `src.retriever`:

```python
retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]
```

For a nonblank query, load the selected index and construct the in-memory BM25 index from the same stored documents. Search with the local embedding model and BM25+ (which avoids negative IDF for common terms), preserving alphanumeric form identifiers such as `ZX101` during case-insensitive tokenization. Fuse up to `max(20, top_k)` candidates from each branch using reciprocal rank fusion with constant 60; deduplicate by `chunk_id` and break score ties by ID. Return at most `top_k` ranked chunks with the five original fields and complete passage text. Retrieval scores indicate rank, not correctness or evidential support.

A blank query returns `[]`, a non-positive `top_k` raises `ValueError`, and results are capped at the corpus size. An empty result for a nonblank query means no passage was retrieved, not an error. Missing, stale, unreadable, or incompatible indexes, unavailable local models, and search failures raise `RetrievalError` from `src.contracts`; they must not trigger a fallback to fictional evidence. Multiple queries may be issued in succession; callers combining results can deduplicate by `chunk_id`. Set `RETRIEVAL_INDEX_DIR` for a nondefault index and `RETRIEVAL_MODEL` when a nondefault embedding model was used. Consult the README for setup and rebuild commands.

## Verification and handoff

1. Run `python -m unittest discover -s tests` in the configured environment. Check input validation, tokenization, fusion and deduplication, return limits, blank queries, invalid limits, and failure handling.
2. Use temporary indexes and controlled embeddings to verify build, reload, full-field retrieval, source-change detection, and replacement of stale chunks on rebuild.
3. Run a separate real-model smoke test against the fictional fixture using a paraphrase and the exact `ZX101` identifier. Record the results and any limitations; these examples are not a meaningful handbook benchmark.
4. Give Members 1 and 3 the setup and rebuild instructions, index configuration and error behavior, and the import change from `src.mock_retriever` to `src.retriever`. Ask both to confirm the unchanged chunk contract and handoff.
5. Before real-answer integration, build a separate index from Member 1's validated handbook chunks. Evaluate retrieval against manually checked handbook questions, including exact identifiers and paraphrases, before choosing the final embedding model or claiming retrieval quality.

Stage 2 is complete when the build and search workflows are reproducible, the checks and smoke test are reported, documentation is available, and the teammate handoff is confirmed. Teammate confirmation remains a separate coordination step and must not be assumed.

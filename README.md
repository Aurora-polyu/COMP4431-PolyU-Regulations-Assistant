# PolyU Academic Regulations Assistant

A COMP4431 group project to build a local chatbot that helps students understand academic regulations using the 2026/27 Student Handbook for Taught Programmes.

## Project structure

- `data/` — handbook and processed data
- `scripts/` — preprocessing and setup scripts
- `src/` — application, retrieval, and conversation code
- `tests/` — tests and evaluation materials
- `presentation/` — presentation and demo materials
- `PROJECT_IMPLEMENTATION_PLAN.md` — project scope, architecture, and team responsibilities

The project is at the initial structure stage; implementation and setup instructions will be added as the team develops it. Confirm permission to share the handbook before adding it to the repository.

## Stage 1 retrieval mock

`data/sample_chunks.json` contains **fictional examples**, not handbook content or academic regulations. The mock returns these chunks in their fixture order for any nonblank query; it does not perform search or rank relevance. Use it to develop the answer service until the real retriever replaces it:

```python
from src.mock_retriever import retrieve

chunks = retrieve("example question", top_k=2)
for chunk in chunks:
    print(chunk["section"], chunk["printed_page"], chunk["pdf_page"], chunk["text"])
```

A blank query returns an empty list, and a non-positive `top_k` raises `ValueError`. Run `python -m unittest discover -s tests` to check the fixture and interface. See [the Stage 1 protocol](docs/member2_stage1_protocol.md) for the contract and handoff steps.

## Stage 2 hybrid retrieval

See the [Stage 2 protocol](docs/member2_stage2_protocol.md) for the contract, workflow, verification, and handoff.

The real retriever combines local sentence embeddings in ChromaDB with BM25 and reciprocal rank fusion. The default input is Member 1’s `data/chunks.jsonl`; the fictional fixture must use a separate index and must never be used as handbook evidence. The candidate embedding model is `BAAI/bge-small-en-v1.5`; it is not yet validated on the handbook.

Use Python 3.12 and install the pinned dependencies:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_index.py
python -m unittest discover -s tests
```

Place Member 1’s validated `data/chunks.jsonl` in the repository first; if it is absent, use `--chunks` with the handoff path. The first build downloads the model; search loads the exact Hugging Face model revision recorded by the index from the local model cache. Supported embedding models must expose their immutable Hub commit. If that revision is missing locally, restore it or rebuild the index. The default index is `chroma_db/` (ignored by Git). To use a different JSON chunk file or index, run:

```sh
python scripts/build_index.py --chunks /path/to/chunks.jsonl --index-dir /path/to/index
export RETRIEVAL_INDEX_DIR=/path/to/index
```

For a synthetic smoke test, use a separate ignored directory and select it explicitly for retrieval:

```sh
python scripts/build_index.py --chunks data/sample_chunks.json --index-dir chroma_db_sample
export RETRIEVAL_INDEX_DIR=chroma_db_sample
# Unset this variable before querying the handbook index.
unset RETRIEVAL_INDEX_DIR
```

Paths to local indexes should be ignored by Git; `chroma_db_sample/` is ignored by this repository. The supplied fictional fixture is identified by its content, even when copied from another checkout. A sample build cannot replace an existing non-sample index; choose a separate directory. The index records the absolute source path and its SHA-256 hash, plus the model, immutable model revision, and query configuration. Indexes created before revision tracking must be rebuilt. Keep the source file available, and rebuild after moving or changing it, changing models, or updating chunks. Set `RETRIEVAL_MODEL` to the same model used by `--model` if overriding the default. Rebuilding publishes a fresh index; old generations remain on disk so active readers are not disrupted. Remove the entire index directory when it is no longer in use to reclaim space, then rebuild.

Member 3 can replace the mock import while retaining the same call and result fields:

```python
from src.retriever import retrieve

for chunk in retrieve("How do I request temporary leave?", top_k=5):
    print(chunk["chunk_id"], chunk["section"], chunk["printed_page"], chunk["pdf_page"], chunk["text"])
```

Blank queries return `[]`; non-positive limits raise `ValueError`. Missing, stale, incompatible, or unreadable indexes and unavailable local models raise `RetrievalError` with troubleshooting context. If the source, model, or index is unavailable, restore it and rebuild; do not silently fall back to synthetic data. Search scores are ranking signals, not probabilities or proof of evidence relevance.

Import the shared `RetrievedChunk` and `RetrievalError` types from `src.contracts` without installing the retrieval dependencies. An empty result for a nonblank query means no passage was retrieved, not an infrastructure error; returned passages still need to be checked for relevance and support. Callers may issue multiple queries and deduplicate combined results by `chunk_id`. An older default index built from the provided fictional fixture is rejected and must be replaced with a handbook index.

Member 1 has supplied validated handbook chunks on `feature/data`; until integration, pass the handoff path with `--chunks`. Build the handbook index from those chunks. Members 1 and 3 should confirm the contract and handoff; the existing mock remains available for independent development. The synthetic smoke checks are not a handbook benchmark.

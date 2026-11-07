# PolyU Academic Regulations Assistant

An English-language COMP4431 project that answers questions using the 2026/27 Student Handbook for Taught Programmes. Answers and citations must still be checked against the handbook. Multilingual retrieval and answers are outside the current scope.

## Local setup

Use Python 3.12, an authorized copy of the handbook, and an authorized DeepSeek API key. Confirm redistribution permission before sharing the PDF or handbook-derived files; the repository already tracks extracted chunks and companion files. The supplied `data/sample_chunks.json`, `src/mock_retriever.py`, and `src/mock_backend.py` contain fictional development examples, not regulations.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add `DEEPSEEK_API_KEY` to the ignored `.env` file without committing it. Optionally set `DEEPSEEK_MODEL` and `DEEPSEEK_BASE_URL` there. Live requests may incur charges. The default model is `deepseek-flash`.

Place an authorized PDF at `data/handbook.pdf`, and validate it and the approved `data/chunks.jsonl` as described in the [integration protocol](docs/integration_protocol.md) and [Stage A review](docs/stage_a_review.md). PDF identity and table mappings require review; a matching hash alone does not establish extraction correctness.

Build a new handbook index in a dedicated location, then set retrieval variables **in the shell before starting Streamlit**:

```sh
python scripts/build_index.py --chunks data/chunks.jsonl --index-dir /absolute/path/to/handbook-index
export RETRIEVAL_INDEX_DIR=/absolute/path/to/handbook-index
export RETRIEVAL_BACKEND=real
unset RETRIEVAL_MODEL
streamlit run app.py
```

The initial build downloads the default embedding model, `BAAI/bge-small-en-v1.5`. The index records the absolute chunk-file path and hash, model revision, and settings. Keep the source file unchanged and available; rebuild after moving or changing it. If using a nondefault model, set `RETRIEVAL_MODEL` to the same model before startup. Retrieval settings in `.env` are not reliable on first use because the retriever is selected before the DeepSeek client loads that file.

Ask a question, expand its sources to read the full passages and both page numbers, and use **New Conversation** to clear session history. The UI calls the real answer service; it does not automatically substitute fictional evidence when retrieval fails.

## Checks and troubleshooting

```sh
python -m pip check
HANDBOOK_PDF="$PWD/data/handbook.pdf" python -m pytest -q -rs
```

Without the PDF, handbook-dependent tests may be skipped; record the skips. For a missing or stale index, confirm `RETRIEVAL_INDEX_DIR`, the source path and hash, then build a fresh index using the command above. Restore the recorded local embedding model revision if unavailable. For answer-service failures, check the API key, model, network connection and service configuration. The UI deliberately avoids displaying raw error details that may contain sensitive information.

`RETRIEVAL_BACKEND=mock` explicitly enables fictional development retrieval; clear it for handbook use. Any index built from sample chunks must be separate from the handbook index. Development fixture warnings must remain visible and fixture results must never be treated as handbook rules. See the [Stage B review](docs/stage_b_review.md) and [Stage C review](docs/stage_c_review.md) for existing retrieval misses, table-coverage limitations and verification results. The agreed retrieval benchmark and integrated evaluation are still pending.

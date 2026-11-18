# Testing

From the project root, activate the environment and run:

```sh
python -m pip check
HANDBOOK_PDF="$PWD/data/handbook.pdf" python -m pytest -q -rs
```

Tests requiring the handbook may be skipped when it is unavailable; check the reported skips. The suite covers extraction and reviewed table transformations, retrieval and index consistency, conversation responses, citations, the Streamlit interface, chat history and transactional storage, Collection, feedback, suggested questions, and MCP. Tests use test doubles and temporary files, so they do not require live model provider requests.

For manual review, run the app with the real handbook index and ask representative questions, including follow-ups and questions with insufficient evidence. Compare every claim and cited passage with the relevant PDF page, including table layout, conditions, and printed/PDF page numbers. A valid citation ID alone does not establish that the answer is correct or complete. Live model calls may incur charges.

For an integrated manual pass, reopen and search a saved chat, save and export an answer, and rate and report an answer. Check the sidebar's **Delete all my data** and **Confirm delete** controls against a disposable database. See [MCP setup](mcp.md) for client checks.

Feedback is reviewed from the local database:

```sh
python scripts/export_feedback.py --out feedback.csv
```

The export lists each rating and report with its timestamp, message id, rating, reason, comment, question, answer and supporting chunk ids, and prints the counts of likes, dislikes and reports. `--out feedback.jsonl` writes JSON Lines instead of CSV.

See [Data and indexing](data-and-indexing.md) for candidate extraction and validation without replacing active artifacts.

On Windows, the same test command works in PowerShell (`python -m pytest -q -rs`); `PYTHONUTF8` is not required. ChromaDB may keep temporary index files open until Python exits. If Windows prevents their removal, the affected tests still run their assertions and report a cleanup warning with the directory path; delete that directory after the process exits. Other cleanup errors still fail the test.

Git is configured to check out `data/chunks.jsonl` with LF line endings so its byte-level SHA-256 matches the recorded Stage E hash. An existing checkout that already has CRLF may need the file refreshed after pulling: first check `git diff -- data/chunks.jsonl` and preserve any local changes, then run `git restore --worktree -- data/chunks.jsonl`. Rebuild the retrieval index afterward, because its manifest records the exact source-file bytes.

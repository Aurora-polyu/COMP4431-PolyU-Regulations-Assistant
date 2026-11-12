# Member D: Suggested Questions and MCP Server

**Features:** A3 Suggested questions, A5 MCP server · **Deadline:** 16 Nov 2026, 23:59 · **Background:** [NEW_FEATURES_PLAN.md](../../archive/plans/2026-11-new-features-proposal.md)

> **Team rules.** A's branch 1 merges to `main` first; B, C and D branch from it. Edit only your own files; only A edits `app.py`. Rebase on `main` before a pull request; each needs one review and a passing `python -m pytest -q -rs`. Storage functions take `db_path=None`, otherwise use `USER_DATA_DB` (default `data/user_data.sqlite`). Optional work starts only after your core pull request is merged.

**Status (12 Nov):** Implementation is integrated on this branch. The checkboxes below record the original acceptance criteria; final manual verification is outstanding.

## 1. Goal

New users don't know what to ask, and students would rather use the handbook inside the AI agents they already use. Show starter questions by domain on the empty chat, and expose handbook search as a local MCP server for Claude Desktop, Claude Code and Codex.

## 2. Branches and files

| Branch | Files |
|---|---|
| `feat/suggested-questions` | `src/suggested_questions.py`, `src/ui/suggestions.py`, `tests/test_suggested_questions.py` |
| `feat/mcp-server` | `mcp_server.py`, `docs/mcp.md`, `tests/test_mcp_server.py`, the `mcp` line in `requirements.txt` |

## 3. Tasks

**Branch 1: suggested questions**
1. `SUGGESTED_QUESTIONS: dict[str, list[str]]` with 6 domains × 3 questions, taken from the table in A3 of the plan (Pause or leave study · Exams and results · Subjects and retakes · Transcripts and certificates · Study load and registration · Campus services).
2. Run all 18 on the real system (index and API key). Keep only those that return `answered` from the right section; replace the rest (check the two "not in the tested set" first). Paste the results in the pull request.
3. `render_suggestions()`: a three-line "How to use" text (ask a question; open the sources; rate, save or report an answer), domain chips (`st.pills`), then the three questions as buttons. Return the clicked question or `None`; show only while the chat is empty.
4. Write `tests/test_suggested_questions.py`: each domain has 3+ non-empty unique questions; no duplicates across domains; renders and returns the clicked text (`AppTest`).

**Branch 2: MCP server**
1. Pin the MCP Python SDK version in `requirements.txt` and check its `FastMCP` import path.
2. `search_handbook(query)`: reject empty input; call `retrieve(query, top_k=5)`; return `chunk_id`, `section`, `printed_page`, `pdf_page`, `text`.
3. `get_section(section)`: read `data/chunks.jsonl`; return chunks whose `section` starts with the id, in order; if none, a clear error listing nearby valid ids.
4. Load the embedding model at startup (first search takes about 9 s otherwise). Logs go to standard error; no `print`, since stdout carries the protocol.
5. `docs/mcp.md`: one copy-paste setup each for Claude Desktop (`claude_desktop_config.json`), Claude Code (`claude mcp add ...`) and Codex (`~/.codex/config.toml`), checked against each tool's current docs; absolute paths, venv Python, `RETRIEVAL_INDEX_DIR`; how to test with MCP Inspector (`mcp dev mcp_server.py`).
6. Write `tests/test_mcp_server.py`: call the tool functions directly with an injected retriever and a temporary chunks file.

## 4. Interfaces you use

- **Hook:** you replace the stub `render_suggestions() -> str | None`; A passes the returned question to `render_turn`.
- **Retriever:** `retrieve(query, top_k)` from `src/retriever.py`; chunks from `data/chunks.jsonl`.
- **MCP rules:** both tools are read-only, store no student data and need no model API key. Their descriptions tell the caller to check the official handbook and the responsible office. Run locally over stdio (team decision: nothing hosted).

## 5. Done when

- [ ] A new user picks a domain, clicks a question and gets a cited answer; all 18 questions are verified.
- [ ] MCP Inspector lists both tools and returns correct output.
- [ ] Claude Desktop and Claude Code answer "How do I defer my study?" using `search_handbook`.
- [ ] `docs/mcp.md` lets a teammate set up any of the three clients in a few minutes.

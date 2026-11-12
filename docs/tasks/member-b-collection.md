# Member B: My Collection

**Features:** A2 My collection · **Deadline:** 16 Nov 2026, 23:59 · **Background:** [NEW_FEATURES_PLAN.md](../NEW_FEATURES_PLAN.md)

> **Team rules.** A's branch 1 merges to `main` first; B, C and D branch from it. Edit only your own files; only A edits `app.py`. Rebase on `main` before a pull request; each needs one review and a passing `python -m pytest -q -rs`. Storage functions take `db_path=None`, otherwise use `USER_DATA_DB` (default `data/user_data.sqlite`). Optional work starts only after your core pull request is merged.

## 1. Goal

Important answers can't be kept and found again. Let students save an answer as a snapshot and find it later in a searchable Collection view.

## 2. Branches and files

| Branch | Files |
|---|---|
| `feat/collection` | `src/ui/collection.py`, `tests/test_collection.py` |

## 3. Tasks

1. **`render_save_button(message)`:** only on answered messages. Shows "Save" or "Saved" via `is_saved(message["id"])`. Saving stores the question, the answer without citation markers (`strip_citation_markers`), the cited passages, status, `evidence_source`, edition "2026/27" and the date. Widget key `save_<id>`; `st.toast` on save.
2. **`render_collection_view()`:** heading; banner "Saved answers are copies. Check the official handbook before acting."; search box; items newest first, each with question, answer, source popovers (`render_source_popovers`), saved date, a note field (`update_note` on change) and **Remove**. Empty state: "Nothing saved yet. Use Save under an answer."
3. **Download all as Markdown:** a pure function `collection_to_markdown(items)` feeds `st.download_button`.
4. Write `tests/test_collection.py`: `collection_to_markdown`; Save toggling and persistence through `AppTest` with an injected answer service and a temporary database.

## 4. Interfaces you use

- **From `src/user_data.py`:** `save_answer`, `is_saved`, `list_saved(search="")`, `update_note`, `remove_saved`.
- **From `src/ui/sources.py`:** `render_source_popovers(chunks)`, `strip_citation_markers(content, chunks)`.
- **Message dict:** `{"role", "content", "chunks", "id", "question", "status", "evidence_source"}`.
- **You replace the stubs** `render_save_button(message)` and `render_collection_view()`; A already calls them.

## 5. Done when

- [ ] Save an answer, restart the app, and find it in Collection with its sources.
- [ ] Search finds it; a note can be added; Remove deletes it.
- [ ] Download all as Markdown produces a readable `.md` file.
- [ ] Tests pass with a temporary database.

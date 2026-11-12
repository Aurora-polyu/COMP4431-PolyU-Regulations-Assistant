# Member A: App Skeleton, Storage and Chat History

**Features:** A1 Saved chat history, A6 UI layout · **Deadline:** 16 Nov 2026, 23:59 · **Background:** [NEW_FEATURES_PLAN.md](../NEW_FEATURES_PLAN.md)

> **Team rules.** A's branch 1 merges to `main` first; B, C and D branch from it. Edit only your own files; only A edits `app.py`. Rebase on `main` before a pull request; each needs one review and a passing `python -m pytest -q -rs`. Storage functions take `db_path=None`, otherwise use `USER_DATA_DB` (default `data/user_data.sqlite`). Optional work starts only after your core pull request is merged.

## 1. Goal

Conversations are lost on refresh. Save chats automatically (with a Temporary chat option, as in ChatGPT), and build the skeleton and storage that B, C and D plug into.

## 2. Branches and files

| Branch | Files |
|---|---|
| `feat/app-skeleton-storage` (merges first) | `app.py`, `src/user_data.py`, `src/ui/__init__.py`, `src/ui/sources.py`, `src/ui/actions.py`, stubs `src/ui/collection.py`, `src/ui/feedback.py`, `src/ui/suggestions.py`, `src/ui/chat_list.py`, `tests/test_user_data.py`, `tests/test_app.py` |
| `feat/chat-history` (after branch 1) | `src/ui/chat_list.py`, `tests/test_chat_history.py`, small hook calls in `app.py` |

## 3. Tasks

**Branch 1: skeleton and storage**
1. In `render_turn`, add `id` (uuid4 hex), `question`, `status` and `evidence_source` to assistant messages. Move the source popovers and `_remove_citation_markers` into `src/ui/sources.py`.
2. Build the sidebar (top to bottom): logo · **New chat** + **Temporary chat** · **Search chats** · **Collection** · **Chats** list · **Settings** popover, footer. Add `st.session_state.view` ("Chat" / "Collection"). Keep `app.py` a single script (no `st.navigation`).
3. Wire the hooks: `render_action_bar(message)` after each answer; `render_suggestions()` on the empty chat (pass a returned question to `render_turn`); `persist_turn(...)` after each turn. Stubs do nothing, so the app looks unchanged.
4. Implement all of `src/user_data.py` with `sqlite3` (tables `conversations`, `chat_messages`, `saved_answers`, `feedback`, created lazily).
5. Change `tests/test_app.py` to label-based selectors; all 9 existing tests stay green.
6. Write `tests/test_user_data.py`: round trip, duplicate save, rating upsert, report, search, remove, delete all, temporary database.

**Branch 2: chat history**
1. `persist_turn`: unless temporary, create the chat on the first turn (title = first question, about 60 characters), then append both messages.
2. `render_chat_list()`: newest first (about 15), filtered by Search chats, current chat highlighted. Clicking a row reopens it; a "…" popover offers **Rename** and **Delete**.
3. **Temporary chat:** sets `st.session_state.temporary = True`, shows "Temporary chat: not saved", writes nothing. **New chat** clears the chat id and the flag.
4. **Settings:** **Delete all my data** with a confirmation checkbox, then `delete_all()` and a session reset.
5. When reopening a chat, preset `st.session_state["rate_<id>"]` from `get_rating`.
6. Write `tests/test_chat_history.py`: create, append, reopen (identical messages with chunks), rename, delete, search, temporary writes nothing, delete all.

## 4. Interfaces you provide

**Assistant message:** `{"role", "content", "chunks", "id", "question", "status", "evidence_source"}`. Each chunk has `chunk_id`, `section`, `printed_page`, `pdf_page`, `text`.

**`src/user_data.py`** (all take `db_path=None`):

| Function | Purpose |
|---|---|
| `init_db()` | Create tables if missing |
| `create_conversation(title) -> int` | New chat |
| `append_message(conversation_id, message)` | Store one message with its chunks |
| `list_conversations(limit=15, search="")` | Newest first; search title and text |
| `load_conversation(conversation_id)` | Messages in order |
| `rename_conversation(id, title)` / `delete_conversation(id)` | Rename / delete one chat |
| `delete_all()` | Delete chats, saved answers and feedback |
| `save_answer(message_id, question, answer, status, evidence_source, sources, note="") -> int` | Idempotent per `message_id` |
| `is_saved(message_id) -> int \| None` | Saved id or `None` |
| `list_saved(search="")` / `update_note(saved_id, note)` / `remove_saved(saved_id)` | Collection |
| `set_rating(message_id, rating, question, answer, chunk_ids)` / `get_rating(message_id)` | +1 / −1, one row per message |
| `add_report(message_id, reason, comment, question, answer, chunk_ids)` / `list_feedback()` | Reports and export |

**UI hooks (stubs):** `render_action_bar(message)` in `actions.py` (calls the next two) · `render_save_button(message)`, `render_collection_view()` in `collection.py` (B) · `render_rating_and_report(message)` in `feedback.py` (C) · `render_suggestions() -> str | None` in `suggestions.py` (D) · `render_chat_list()`, `persist_turn(user_message, assistant_message)` in `chat_list.py` (A) · `render_source_popovers(chunks)`, `strip_citation_markers(content, chunks)` in `sources.py` (A).

## 5. Done when

- [ ] Branch 1: the app behaves exactly as before, storage tests pass, and B, C and D can plug in without touching `app.py`.
- [ ] Branch 2: ask two questions, restart, reopen the chat, ask a follow-up that still resolves, rename and delete it.
- [ ] A Temporary chat leaves nothing in the list; Delete all my data empties everything.
- [ ] `git status` does not show `data/user_data.sqlite`.

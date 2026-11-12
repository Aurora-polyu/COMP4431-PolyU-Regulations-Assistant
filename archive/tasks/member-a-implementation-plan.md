# Member A: Implementation Plan for Branch 1

**Scope:** `feat/app-skeleton-storage` only. Chat history (branch 2) is listed at the end and is not detailed here.
**Contract:** [member-a-skeleton-and-history.md](member-a-skeleton-and-history.md). This file adds order, checkpoints and known traps; it does not change the interfaces.

Branch 1 ships in three stages. Each stage ends with a runnable app and a green test suite, so a failure is always local to the stage that just ran.

---

## Stage 1: Shell and extraction

**Goal:** move rendering helpers out of `app.py`, add the shared hook calls, and leave the visible interface exactly as it is.

**Files**

| File | Change |
|---|---|
| `src/ui/__init__.py` | New. Package marker, no imports. |
| `src/ui/sources.py` | New. Receives `strip_citation_markers` and `render_source_popovers`. |
| `src/ui/actions.py` | New. `render_action_bar(message)` calls the save and feedback stubs. |
| `src/ui/collection.py` | New stub: `render_save_button`, `render_collection_view`. |
| `src/ui/feedback.py` | New stub: `render_rating_and_report`. |
| `src/ui/suggestions.py` | New stub: `render_suggestions() -> None`. |
| `src/ui/chat_list.py` | New stub: `render_chat_list`, `persist_turn`. |
| `app.py` | Use the new modules and add the assistant message fields. |

**Steps**

1. Copy `_remove_citation_markers` from `app.py` into `src/ui/sources.py` as `strip_citation_markers(content, chunks)`. Keep the regular expression, the chunk id set and the "unknown brackets stay" rule unchanged.
2. Move the source loop from `_render_message` into `render_source_popovers(chunks)`. Keep the label format `f"{section} · printed p. {printed_page} / PDF p. {pdf_page}"` and the nesting `st.popover(title, width="stretch")` → `st.container(height=300, border=False)` → `st.text(...)`.
3. Add `render_action_bar(message)` in `actions.py`. It returns early unless the message is an assistant message with an `id`, then calls `render_save_button(message)` and `render_rating_and_report(message)` inside one empty keyed container.
4. Add the four stubs. Every stub returns `None` and draws nothing.
5. In `render_turn`, change the assistant record to `{"role", "content", "chunks", "id", "question", "status", "evidence_source"}`. Take `status` and `evidence_source` from the service response. Use `"error"` and `None` in the exception branch. Generate `id` with `uuid.uuid4().hex`.
6. Call `render_action_bar(message)` after `_render_message(message)`, then `persist_turn(user, message)`.
7. Remove `import re` from `app.py`.

**Checkpoint:** `tests/test_app.py` passes with no edits. The rendered text, the popover labels and the history dicts are byte-identical to before.

---

## Stage 2: Sidebar and view switch

**Goal:** build the ChatGPT-style sidebar and the Collection view switch.

**Files:** `app.py`, `assets/style.css`, `tests/test_app.py`.

**Sidebar order, top to bottom**

1. Logo and title (unchanged columns).
2. **New chat** button, key `new_chat`, callback clears `messages`.
3. **Temporary chat** button, key `temporary_chat`.
4. **Search chats** input, key `search`.
5. **Collection** button, key `show_collection`, sets `view` to `"Collection"`.
6. **Chats** heading and `render_chat_list()`. The stub draws nothing in this branch.
7. **Settings** popover.
8. Existing About text, picture container and handbook footer.

**Main area**

- `st.session_state.view == "Collection"` renders `render_collection_view()`.
- Otherwise run the current chat flow. Render `render_suggestions()` only while the chat is empty and pass a returned question to `render_turn`.
- Add `view = "Chat"` to the session defaults.

**Style**

The current rule `[data-testid="stSidebar"] [data-testid="stButton"] button` turns every sidebar button red and full width. Wrap New chat in a keyed container and scope the red rule to that container. New buttons keep the default outlined style.

**Tests**

Add two helpers to `tests/test_app.py`:

```python
def button(app, label):
    found = [b for b in app.button if b.label == label]
    assert len(found) == 1, [b.label for b in app.button]
    return found[0]

def source_popovers(app):
    return [p for p in app.get("popover")
            if " · printed p. " in p.proto.popover.label]
```

Replace every positional selector. `app.button[0]` becomes `button(app, "New chat")`. Every `app.get("popover")` count and index becomes `source_popovers(app)`. The single-button assertion becomes a check that New chat exists and no answer action buttons exist yet.

**Checkpoint:** `python -m pytest -q` passes. A screenshot of the sidebar is posted for review. No `st.text` call is added anywhere in the sidebar, so `app.text[0]` still points at the first source passage.

---

## Stage 3: Storage

**Goal:** implement `src/user_data.py` and its tests. The app does not call it in this branch.

**Files:** `src/user_data.py`, `tests/test_user_data.py`.

**Rules**

- Resolve the path on every call: `db_path or os.environ.get("USER_DATA_DB") or "data/user_data.sqlite"`. A relative default resolves from the repository root.
- Open one connection per call, set `PRAGMA foreign_keys=ON` and `row_factory = sqlite3.Row`, close it in `finally`. Never cache a connection.
- Create tables with `CREATE TABLE IF NOT EXISTS` inside the connection helper. Nothing is created at import time.
- Store chunk lists as JSON text.

**Tables:** `conversations`, `chat_messages`, `saved_answers`, `feedback`. The `feedback` table holds both ratings and reports, with a `kind` column. A partial unique index on `(kind, message_id)` keeps one rating row per message.

**Functions:** all rows of the interface table in the contract. Key behaviours:

- `save_answer` is idempotent per `message_id` and returns the existing row id.
- `set_rating` upserts on `message_id` and keeps any report fields.
- `add_report` upserts on `message_id` and keeps any rating.
- `list_conversations` searches titles and message text, newest first.
- `list_saved` searches question, answer and note.
- `delete_all` empties all four tables.

**Tests, eight cases:** conversation round trip with identical chunks, duplicate save, rating upsert, report, search, remove, delete all, two isolated database paths. Each test passes an explicit `db_path` under `tmp_path` and also covers the `USER_DATA_DB` fallback once.

**Checkpoint:** `python -m pytest -q -rs` passes. `git status --short` shows no `data/user_data.sqlite`. Local commit on `feat/app-skeleton-storage`. No push and no pull request.

---

## Verification for the branch

```sh
python -m pytest -q -rs
```

```sh
streamlit run app.py
```

Manual pass: ask a question, ask a follow-up, open a source passage, confirm the sidebar buttons do nothing visible yet, confirm Collection opens an empty page, confirm the app behaves as before. Check that `git status --short` lists only the intended files.

## Known traps

- `answer_question` must stay imported at module level in `app.py`. `tests/test_app.py` patches `src.conversation.answer_question` and relies on the fresh script run picking it up. Never import it inside `src/ui`.
- Every extra sidebar button breaks `app.button[0]` and `len(app.button) == 1`. Key and label every widget.
- A `st.popover("Settings")` is added to `app.get("popover")`. Source popovers must be selected by the `" · printed p. "` label fragment.
- Do not call `st.text` in the sidebar, or `app.text[0]` will no longer be the first source passage.
- No persistence happens in branch 1. `persist_turn` is an empty function, so a rerun cannot write a turn twice.
- Preset any `rate_<id>` session key before the main chat loop in branch 2. Mutating a widget key after the widget is created raises a Streamlit error.

## Branch 2 (later)

`feat/chat-history` replaces the `chat_list` stubs: `persist_turn`, `render_chat_list`, Temporary chat, Settings delete-all and restored ratings. The assistant `id` and the partial unique index on `chat_messages.message_id` exist from branch 1 so the second branch can use them as the duplicate-write guard.

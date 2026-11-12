# Member B — Collection design note

**Branch:** `feat/collection` · **Files:** `src/ui/collection.py`, `tests/test_collection.py`
**Task:** [member-b-collection.md](member-b-collection.md) · **Plan:** [NEW_FEATURES_PLAN.md](../NEW_FEATURES_PLAN.md)

This note fixes the behaviour before the code is written. It only covers parts the
task file leaves open; everything else follows the task file literally.

## 1. Scope

Replace the two stubs `render_save_button(message)` and `render_collection_view()`
that `app.py` already calls. Add the pure helper `collection_to_markdown(items)`.

No changes to `app.py`, `src/user_data.py`, `src/ui/sources.py` or any other
member's files: the storage layer (Member A) and the citation helpers already expose
everything this module needs.

## 2. Save button

- Rendered only for `role == "assistant"`, `status == "answered"` and a non-empty
  `id`. Other statuses (`needs_clarification`, `insufficient_evidence`, `error`)
  show no button, because their text is not a grounded answer.
- Label comes from `is_saved(message["id"])`: `Save` when unsaved, `Saved` when the
  row exists. `Saved` is disabled — un-saving happens in Collection, where the
  saved item and its sources are visible together.
- Clicking `Save` writes exactly one row through
  `save_answer(message_id, question, answer, status, evidence_source, sources)`:
  - `question` = `message["question"]`
  - `answer` = `strip_citation_markers(message["content"], chunks)` — the stored
    copy keeps no bracket markers, so it stays readable outside the chat
  - `sources` = `message["chunks"]` (the cited passages shown in the UI)
  - `status`, `evidence_source` copied from the message
- After writing, `st.toast("Saved to Collection")` and `st.rerun()` so the button
  becomes `Saved` in the same interaction.
- Widget key: `save_<message id>`, as required by the task file.

## 3. Collection view

Order: heading, banner, search, download, items newest first.

- Heading: `My Collection`.
- Banner (always visible): *"Saved answers are copies. Check the official handbook before acting."*
- Search: `st.text_input` with key `collection_search`, passed straight to
  `list_saved(search=...)`. Empty search lists everything.
- Download: `st.download_button("Download all as Markdown", ...)` with
  `collection_to_markdown(items)`, file name `collection.md`, MIME `text/markdown`.
  Rendered only when at least one item exists.
- Empty state: `st.info("Nothing saved yet. Use Save under an answer.")` and no
  download button.

Each item is a bordered container containing, in order:

1. the saved question (bold),
2. a caption with the saved date and the handbook edition,
3. the stored answer (no citation markers),
4. `render_source_popovers(item["sources"])` when sources exist,
5. a `st.text_area` note with key `note_<saved id>`; when the value differs from the
   stored note, `update_note(saved id, value)` and a toast,
6. a `Remove` button with key `remove_<saved id>`; it calls `remove_saved` and
   reruns, so the item disappears immediately.

## 4. Edition and date

`save_answer` has no edition column and Member B must not change the schema. The
handbook edition is a constant for this application, so:

- the view shows `Handbook 2026/27` as a fixed label;
- the Markdown export writes `Handbook edition: 2026/27` once in the header;
- the saved date is `created_at`, written by SQLite.

If Member A later adds an edition column, only the label source changes.

## 5. `collection_to_markdown(items)`

Pure and deterministic: it uses only the item fields, never the current time, so it
can be asserted exactly in tests.

Format:

```markdown
# My Collection — PolyU Academic Regulations Assistant

Handbook edition: 2026/27
Saved answers: 2

> Saved answers are copies. Check the official handbook before acting.

---

## 1. <question>

- Saved: <created_at>
- Status: answered
- Sources: 2

**Answer**

<answer>

**Note**

<note, or "(none)">

**Sources**

### 5.C Retaking of Failed Subjects · printed p. 33 / PDF p. 45

> <passage text, line by line as a block quote>

---

## 2. ...
```

- Item order is the order `list_saved` returns (newest first); the function does not
  re-sort.
- A missing note becomes `(none)`.
- A missing source section is omitted.
- An empty list returns a short file that says nothing is saved.

## 6. Tests (`tests/test_collection.py`)

1. `collection_to_markdown` with two items: heading, count, both questions, answer,
   note, source label and passage, numbering order, and the banner line.
2. Empty list: deterministic output, contains "No saved answers".
3. `AppTest` with `USER_DATA_DB` pointed at a temporary SQLite file and
   `src.conversation.answer_question` patched:
   - ask a question, click `Save`;
   - assert the database row: question, answer without `[chunk_id]` markers,
     sources, status, evidence source;
   - rerun and assert the button now reads `Saved`;
   - open Collection and assert the question, answer and source popover are shown;
   - type a note and assert `list_saved` returns it;
   - search for a term and assert the item filters;
   - click `Remove` and assert the row is gone and the empty state appears.
4. Persistence across an app restart: a second `AppTest` instance on the same
   temporary database still shows the saved item.

## 7. Done when

The task file's four checkboxes hold, `python -m pytest -q -rs` passes, and no file
outside the two owned files has changed.

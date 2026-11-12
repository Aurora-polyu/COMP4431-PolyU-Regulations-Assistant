# Member C: Feedback, Report and Docs

**Features:** A4 Feedback and report, final docs · **Deadline:** 16 Nov 2026, 23:59 · **Background:** [NEW_FEATURES_PLAN.md](../../archive/plans/2026-11-new-features-proposal.md)

> **Team rules.** A's branch 1 merges to `main` first; B, C and D branch from it. Edit only your own files; only A edits `app.py`. Rebase on `main` before a pull request; each needs one review and a passing `python -m pytest -q -rs`. Storage functions take `db_path=None`, otherwise use `USER_DATA_DB` (default `data/user_data.sqlite`). Optional work starts only after your core pull request is merged.

**Status (12 Nov):** Implementation is integrated on this branch. The checkboxes below record the original acceptance criteria; final manual verification is outstanding.

## 1. Goal

Wrong answers go unnoticed. Let students rate and report answers, and give the team a way to export and review that feedback. Feedback stays on each machine; nothing is uploaded.

## 2. Branches and files

| Branch | Files |
|---|---|
| `feat/feedback-report` | `src/ui/feedback.py`, `scripts/export_feedback.py`, `tests/test_feedback.py`; at the end `README.md`, `docs/architecture.md`, `docs/testing.md` |

## 3. Tasks

1. **`render_rating_and_report(message)`:** nothing on error replies. `st.feedback("thumbs", key=f"rate_{id}")` with an `on_change` handler that calls `set_rating` (1 → +1, 0 → −1). Changing the rating updates the same row.
2. **Report:** `st.popover("Report")` with a reason (wrong fact / missing condition or exception / wrong or irrelevant source / out of date / other), a comment of up to 500 characters and **Submit**, which calls `add_report` and shows `st.toast("Thanks, report saved")`. Shown on answered and insufficient-evidence replies.
3. **`scripts/export_feedback.py --out feedback.csv`** (or `.jsonl`) using `list_feedback`: time, message id, rating, reason, comment, question, answer, chunk ids. Print the counts of likes, dislikes and reports.
4. Write `tests/test_feedback.py`: rating mapping and change, report saved, export file content, no widgets on error replies.
5. **Last, after the other branches merge:** update `README.md` (the five features and how to use them), `docs/architecture.md` (storage and UI hooks) and `docs/testing.md` (new tests, how to review feedback).

## 4. Interfaces you use

- **From `src/user_data.py`:** `set_rating`, `get_rating`, `add_report`, `list_feedback`.
- **Rating key:** the widget key is `rate_<message id>`. A presets `st.session_state["rate_<id>"]` when a chat is reopened; your widget must not override a preset value.
- **Message dict:** `{"role", "content", "chunks", "id", "question", "status", "evidence_source"}`.
- **You replace the stub** `render_rating_and_report(message)`; A already calls it.

## 5. Done when

- [ ] 👍, 👎 and Report work under every eligible answer, and rows appear in the database.
- [ ] A reopened chat shows its stored ratings.
- [ ] The export script writes the file and prints the counts.
- [ ] The docs describe all five core features.

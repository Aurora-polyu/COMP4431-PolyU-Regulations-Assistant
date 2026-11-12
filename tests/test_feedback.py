"""Feedback hooks and export checks for the rating/report feature."""

import json
import os
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src import user_data
from src.ui.feedback import REPORT_REASONS

CHUNK = {"chunk_id": "test_1", "section": "5.C Retaking", "printed_page": 33,
         "pdf_page": 45, "text": "Complete passage."}
ANSWER = "A grounded answer."
REPLY = {"status": "answered", "answer": ANSWER, "evidence_source": "handbook",
         "clarification_question": None, "cited_chunks": [CHUNK]}
HOOK_SCRIPT = Path(__file__).resolve().parent / "_feedback_hook_app.py"


def rating_rows(db):
    return [f for f in user_data.list_feedback(db_path=db) if f["kind"] == "rating"]


def report_rows(db):
    return [f for f in user_data.list_feedback(db_path=db) if f["kind"] == "report"]


def app_with_reply(tmp_path, monkeypatch, reply=REPLY):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    with patch("src.conversation.answer_question", return_value=reply):
        app = AppTest.from_file(Path(__file__).resolve().parent.parent / "app.py",
                                default_timeout=10).run()
        app.chat_input[0].set_value("Q?").run()
    return app


def message_id(app):
    return app.session_state["messages"][1]["id"]


def hook_app(msg_dict):
    """Render just the feedback hook for a fixed message dict in AppTest."""
    import json

    os.environ["HOOK_MSG"] = json.dumps(msg_dict)
    return AppTest.from_file(HOOK_SCRIPT, default_timeout=10).run()


def test_rating_flow_updates_stored_rating(tmp_path, monkeypatch):
    app = app_with_reply(tmp_path, monkeypatch)
    mid = message_id(app)
    assert len(app.feedback) == 1
    assert app.feedback[0].key == f"rate_{mid}"

    app.feedback[0].set_value(1).run()
    rows = rating_rows(tmp_path / "user_data.sqlite")
    assert len(rows) == 1
    assert rows[0]["message_id"] == mid
    assert rows[0]["rating"] == 1
    assert rows[0]["question"] == "Q?"
    assert rows[0]["answer"] == ANSWER
    assert rows[0]["chunk_ids"] == ["test_1"]

    app.feedback[0].set_value(0).run()
    rows = rating_rows(tmp_path / "user_data.sqlite")
    assert len(rows) == 1
    assert rows[0]["rating"] == -1
    assert user_data.get_rating(mid, db_path=tmp_path / "user_data.sqlite") == -1
    assert app.feedback[0].value == 0


def _action_bar_button(app, label):
    """Return the single widget with the given label in the per-answer bar."""
    return [b for b in app.button if b.label == label][0]


def test_report_flow_saves_reason_and_comment(tmp_path, monkeypatch):
    app = app_with_reply(tmp_path, monkeypatch)
    mid = message_id(app)
    assert any(p.proto.popover.label == "Report" for p in app.get("popover"))

    app.selectbox[0].set_value("wrong fact").run()
    app.text_area[0].set_value("Page 33 states the exception.").run()
    _action_bar_button(app, "Submit").click().run()
    rows = report_rows(tmp_path / "user_data.sqlite")
    assert len(rows) == 1
    assert rows[0]["message_id"] == mid
    assert rows[0]["reason"] == "wrong fact"
    assert rows[0]["comment"] == "Page 33 states the exception."
    assert rows[0]["question"] == "Q?"
    assert rows[0]["chunk_ids"] == ["test_1"]
    assert any("Thanks, report saved" in t.value for t in app.toast)
    assert user_data.get_rating(mid, db_path=tmp_path / "user_data.sqlite") is None


def test_rating_change_keeps_report_row(tmp_path, monkeypatch):
    db = tmp_path / "user_data.sqlite"
    monkeypatch.setenv("USER_DATA_DB", str(db))
    user_data.set_rating("m1", 1, "Q?", ANSWER, ["test_1"], db_path=db)
    user_data.add_report("m1", "out of date", "obsolete page", "Q?", ANSWER, ["test_1"], db_path=db)
    message = {"role": "assistant", "content": ANSWER, "chunks": [CHUNK], "id": "m1",
               "question": "Q?", "status": "answered", "evidence_source": "handbook"}

    app = hook_app(message)
    assert app.feedback[0].value == 1
    app.feedback[0].set_value(0).run()
    assert user_data.get_rating("m1", db_path=db) == -1
    app.selectbox[0].set_value("missing condition or exception").run()
    app.text_area[0].set_value("The deadline is also stated.").run()
    _action_bar_button(app, "Submit").click().run()

    assert user_data.get_rating("m1", db_path=db) == -1
    rows = report_rows(db)
    assert len(rows) == 1
    assert rows[0]["reason"] == "missing condition or exception"


def test_widgets_on_statuses(tmp_path, monkeypatch):
    db = tmp_path / "user_data.sqlite"
    for status, expect_rate, expect_report in (
        ("answered", True, True),
        ("needs_clarification", True, True),
        ("insufficient_evidence", False, True),
        ("error", False, False),
    ):
        reply = {"status": status, "answer": "No supporting passage.",
                 "evidence_source": "handbook", "clarification_question": None,
                 "cited_chunks": []}
        app = app_with_reply(tmp_path, monkeypatch, reply=reply)
        assert len(app.feedback) == (1 if expect_rate else 0)
        report_popovers = [p for p in app.get("popover")
                           if p.proto.popover.label == "Report"]
        assert bool(report_popovers) is expect_report
        assert user_data.list_feedback(db_path=db) == []


def test_export_csv_and_jsonl(tmp_path, monkeypatch):
    db = tmp_path / "user_data.sqlite"
    user_data.set_rating("m1", 1, "Q1", "A1", ["test_1"], db_path=db)
    user_data.set_rating("m2", -1, "Q2", "A2", [], db_path=db)
    user_data.add_report("m3", "other", "see details", "Q3", "A3", ["test_1", "test_2"], db_path=db)
    monkeypatch.setenv("USER_DATA_DB", str(db))

    csv_out = tmp_path / "feedback.csv"
    code = __import__("scripts.export_feedback", fromlist=["main"]).main(["--out", str(csv_out)])
    assert code == 0
    lines = csv_out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4
    assert lines[0].split(",") == ["time", "message id", "rating", "reason", "comment",
                                   "question", "answer", "chunk ids"]
    assert any("m1" in line and ",1," in line for line in lines)

    jsonl_out = tmp_path / "feedback.jsonl"
    code = __import__("scripts.export_feedback", fromlist=["main"]).main(["--out", str(jsonl_out)])
    assert code == 0
    records = [__import__("json").loads(line)
               for line in jsonl_out.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 3
    report = [r for r in records if r["reason"] == "other"][0]
    assert report["chunk ids"] == "test_1, test_2"
    assert report["answer"] == "A3"


def test_submit_without_reason_shows_toast_but_no_row(tmp_path, monkeypatch):
    app = app_with_reply(tmp_path, monkeypatch)
    _action_bar_button(app, "Submit").click().run()
    assert report_rows(tmp_path / "user_data.sqlite") == []
    assert any("Please select a reason" in t.value for t in app.toast)


def test_reopen_chat_shows_preset_rating(tmp_path, monkeypatch):
    db = tmp_path / "user_data.sqlite"
    monkeypatch.setenv("USER_DATA_DB", str(db))
    user_data.set_rating("m1", -1, "Q?", ANSWER, ["test_1"], db_path=db)
    message = {"role": "assistant", "content": ANSWER, "chunks": [CHUNK], "id": "m1",
               "question": "Q?", "status": "answered", "evidence_source": "handbook"}
    app = hook_app(message)
    assert app.feedback[0].value == 0


def test_render_rating_and_report_skip_conditions(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    from src.ui import feedback as feedback_ui
    for message in (
        {"role": "assistant", "content": "x", "id": "a1", "status": "error"},
        {"role": "user", "content": "x", "id": "u1", "status": "answered"},
        {"role": "assistant", "content": "x", "id": None, "status": "answered"},
    ):
        with patch("streamlit.container"), patch("streamlit.columns"):
            feedback_ui.render_rating_and_report(message)
    assert len(REPORT_REASONS) >= 5

"""Checks for My Collection: Markdown export, saving, notes, search and removal."""

from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

import src.user_data as user_data
from src.ui.collection import collection_to_markdown

ROOT = Path(__file__).resolve().parent.parent
CHUNK = {"chunk_id": "test_1", "section": "5.C Retaking", "printed_page": 33,
         "pdf_page": 45, "text": "Complete passage.\nSecond line."}

ITEM_ONE = {
    "id": 2,
    "message_id": "m2",
    "question": "Can I retake a failed subject?",
    "answer": "Retaking is allowed within the study load limit.",
    "status": "answered",
    "evidence_source": "handbook",
    "sources": [CHUNK],
    "note": "Check the 21-credit rule.",
    "created_at": "2026-11-12 10:30:00",
}
ITEM_TWO = {
    "id": 1,
    "message_id": "m1",
    "question": "When is the add/drop period?",
    "answer": "The add/drop period is the first two weeks.",
    "status": "answered",
    "evidence_source": "handbook",
    "sources": [],
    "note": "",
    "created_at": "2026-11-11 09:00:00",
}


def response(answer="Retake is allowed. [test_1]"):
    return {"status": "answered", "answer": answer,
            "evidence_source": "handbook",
            "clarification_question": None, "cited_chunks": [CHUNK]}


def start():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()


def ask(app, question):
    return app.chat_input[0].set_value(question).run()


def buttons(app, label):
    return [b for b in app.button if b.label == label]


def markdown_contains(app, text):
    return any(text in item.value for item in app.markdown)


# --------------------------------------------------------------------------- #
# Markdown export
# --------------------------------------------------------------------------- #


def test_collection_to_markdown_contains_questions_answers_notes_and_sources():
    result = collection_to_markdown([ITEM_ONE, ITEM_TWO])

    assert result.startswith("# My Collection")
    assert "Handbook edition: 2026/27" in result
    assert "Saved answers: 2" in result
    assert "> Saved answers are copies." in result

    assert "## 1. Can I retake a failed subject?" in result
    assert "## 2. When is the add/drop period?" in result
    assert result.index("Can I retake") < result.index("add/drop period")

    assert "Retaking is allowed within the study load limit." in result
    assert "Check the 21-credit rule." in result
    assert "5.C Retaking · printed p. 33 / PDF p. 45" in result
    assert "> Complete passage." in result
    assert "> Second line." in result


def test_collection_to_markdown_uses_placeholder_for_missing_note_and_sources():
    result = collection_to_markdown([ITEM_TWO])

    assert "(none)" in result
    assert "**Sources**" not in result
    assert "Saved answers: 1" in result


def test_collection_to_markdown_empty_is_deterministic():
    first = collection_to_markdown([])
    second = collection_to_markdown([])

    assert first == second
    assert "No saved answers yet." in first
    assert "Saved answers: 0" in first


# --------------------------------------------------------------------------- #
# Save button and collection view
# --------------------------------------------------------------------------- #


def test_save_persists_stripped_answer_and_source(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Can I retake?")

        assert len(buttons(app, "Save")) == 1
        buttons(app, "Save")[0].click().run()

    saved = user_data.list_saved()
    assert len(saved) == 1
    assert saved[0]["question"] == "Can I retake?"
    assert saved[0]["answer"] == "Retake is allowed."
    assert saved[0]["sources"] == [CHUNK]
    assert saved[0]["status"] == "answered"
    assert saved[0]["evidence_source"] == "handbook"
    assert saved[0]["created_at"]


def test_saved_state_uses_is_saved(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    user_data.save_answer("m1", "Question", "Answer", "answered", "handbook", [CHUNK])

    script = (
        "import streamlit as st\n"
        "from src.ui.collection import render_save_button\n"
        "message = {'role': 'assistant', 'status': 'answered', 'id': 'm1',\n"
        "           'content': 'Answer', 'question': 'Question', 'chunks': [],\n"
        "           'evidence_source': 'handbook'}\n"
        "render_save_button(message)\n"
    )
    app = AppTest.from_string(script, default_timeout=10).run()

    assert [b.label for b in app.button] == ["Saved"]
    assert app.button[0].disabled is True


def test_save_button_is_hidden_for_non_answers(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    script = (
        "from src.ui.collection import render_save_button\n"
        "render_save_button({'role': 'assistant', 'status': 'insufficient_evidence',\n"
        "                    'id': 'm2', 'content': 'No evidence.',\n"
        "                    'question': 'Q', 'chunks': []})\n"
        "render_save_button({'role': 'user', 'status': 'answered', 'id': 'm3',\n"
        "                    'content': 'Question', 'chunks': []})\n"
    )
    app = AppTest.from_string(script, default_timeout=10).run()

    assert not app.button
    assert not app.exception


def test_collection_view_shows_item_note_and_search(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Can I retake?")
        buttons(app, "Save")[0].click().run()

    saved_id = user_data.list_saved()[0]["id"]

    buttons(app, "Collection")[0].click().run()
    assert app.title[0].value == "My Collection"
    assert markdown_contains(app, "Can I retake?")
    assert markdown_contains(app, "Retake is allowed.")
    assert any("printed p. 33" in p.proto.popover.label for p in app.get("popover"))

    note = [item for item in app.text_area if item.key == f"note_{saved_id}"][0]
    note.set_value("Important for my case.").run()
    assert user_data.list_saved()[0]["note"] == "Important for my case."

    search = [item for item in app.text_input if item.key == "collection_search"][0]
    search.set_value("retake").run()
    assert markdown_contains(app, "Can I retake?")

    search.set_value("nothing matches").run()
    assert any("No saved answers match" in item.value for item in app.info)
    assert not buttons(app, "Remove")


def test_collection_view_remove_deletes_the_row(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    user_data.save_answer("m1", "Can I retake?", "Retake is allowed.",
                          "answered", "handbook", [CHUNK])

    app = start()
    buttons(app, "Collection")[0].click().run()
    assert buttons(app, "Remove")

    buttons(app, "Remove")[0].click().run()
    assert user_data.list_saved() == []
    assert any("Nothing saved yet" in item.value for item in app.info)


def test_collection_survives_an_app_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    with patch("src.conversation.answer_question", return_value=response()):
        first = start()
        ask(first, "Can I retake?")
        buttons(first, "Save")[0].click().run()

    second = start()
    buttons(second, "Collection")[0].click().run()
    assert markdown_contains(second, "Can I retake?")
    assert markdown_contains(second, "Retake is allowed.")
    assert not second.exception


def test_download_button_appears_only_with_items(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DB", str(tmp_path / "user_data.sqlite"))
    app = start()
    buttons(app, "Collection")[0].click().run()
    assert not app.get("download_button")

    user_data.save_answer("m1", "Question", "Answer", "answered", "handbook", [CHUNK])
    app.run()
    assert app.get("download_button")

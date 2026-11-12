"""Chat history behaviour: persistence, reopen, rename, delete and search."""
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src import user_data

CHUNK = {"chunk_id": "test_1", "section": "5.C Retaking", "printed_page": 33,
         "pdf_page": 45, "text": "Complete passage.\nSecond line."}


def response(status="answered", answer="Grounded answer.", source="handbook", **extra):
    result = {"status": status, "answer": answer, "evidence_source": source,
              "clarification_question": None, "cited_chunks": [CHUNK]}
    result.update(extra)
    return result


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "user_data.sqlite"
    monkeypatch.setenv("USER_DATA_DB", str(path))
    return path


def start():
    return AppTest.from_file(Path(__file__).resolve().parent.parent / "app.py", default_timeout=10).run()


def ask(app, question):
    return app.chat_input[0].set_value(question).run()


def button(app, label):
    found = [b for b in app.button if b.label == label]
    assert len(found) == 1, [b.label for b in app.button]
    return found[0]


def by_key(app, kind, key):
    found = [w for w in app.get(kind) if getattr(w, "key", None) == key]
    assert len(found) == 1, (kind, key, [getattr(w, "key", None) for w in app.get(kind)])
    return found[0]


def test_first_turn_creates_conversation(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "What is the retake rule?")
        conversations = user_data.list_conversations(db_path=db_path)
        assert [c["title"] for c in conversations] == ["What is the retake rule?"]
        messages = user_data.load_conversation(conversations[0]["id"], db_path=db_path)
        assert [m["role"] for m in messages] == ["user", "assistant"]
        assert messages[0]["content"] == "What is the retake rule?"
        assert messages[1]["content"] == "Grounded answer."
        assert messages[1]["chunks"] == [CHUNK]
        assert messages[1]["question"] == "What is the retake rule?"
        assert messages[1]["status"] == "answered"
        assert messages[1]["id"] == app.session_state["messages"][1]["id"]


def test_followup_appends_to_same_conversation(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "First question")
        ask(app, "Second question")
        conversations = user_data.list_conversations(db_path=db_path)
        assert len(conversations) == 1
        messages = user_data.load_conversation(conversations[0]["id"], db_path=db_path)
        assert [m["content"] for m in messages] == [
            "First question", "Grounded answer.", "Second question", "Grounded answer."
        ]


def test_reopen_restores_identical_messages_and_chunks(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "First question")
        ask(app, "Follow-up")
        original = [dict(m) for m in app.session_state["messages"]]
        button(app, "New chat").click().run()
        assert app.session_state["messages"] == []
        button(app, "First question").click().run()
        restored = app.session_state["messages"]
        for key in ("role", "content", "chunks", "id", "question", "status", "evidence_source"):
            assert [m.get(key) for m in restored] == [m.get(key) for m in original]
        assert app.session_state["chat_id"] is not None
        assert not app.exception


def test_rename_conversation(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Original title")
        conversation_id = app.session_state["chat_id"]
        by_key(app, "text_input", f"rename_input_{conversation_id}").set_value("Renamed chat")
        by_key(app, "button", f"rename_chat_{conversation_id}").click().run()
        assert [c["title"] for c in user_data.list_conversations(db_path=db_path)] == ["Renamed chat"]
        assert [b.label for b in app.button
                if getattr(b, "key", None) == f"open_chat_{conversation_id}"] == ["Renamed chat"]


def test_delete_conversation_resets_current_chat(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Question to delete")
        conversation_id = app.session_state["chat_id"]
        by_key(app, "button", f"delete_chat_{conversation_id}").click().run()
        assert user_data.list_conversations(db_path=db_path) == []
        assert app.session_state["messages"] == []
        assert app.session_state["chat_id"] is None
        assert not [b for b in app.button if getattr(b, "key", None) == f"open_chat_{conversation_id}"]


def test_search_filters_chat_list(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Retake policy")
        button(app, "New chat").click().run()
        ask(app, "Appeal deadline")
        assert len(user_data.list_conversations(db_path=db_path)) == 2
        by_key(app, "text_input", "search").set_value("Retake").run()
        listed = [b.label for b in app.button if b.label in ("Retake policy", "Appeal deadline")]
        assert listed == ["Retake policy"]
        by_key(app, "text_input", "search").set_value("").run()
        listed = [b.label for b in app.button if b.label in ("Retake policy", "Appeal deadline")]
        assert sorted(listed) == ["Appeal deadline", "Retake policy"]


def test_temporary_chat_writes_nothing(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        button(app, "Temporary chat").click().run()
        assert app.session_state["temporary"] is True
        assert any("Temporary chat: not saved" in c.value for c in app.caption)
        ask(app, "Private question")
        assert user_data.list_conversations(db_path=db_path) == []
        assert user_data.list_saved(db_path=db_path) == []
        assert user_data.list_feedback(db_path=db_path) == []
        assert not any(b.label in ("Save", "Saved") for b in app.button)
        assert not any(p.proto.popover.label == "Report" for p in app.get("popover"))
        assert app.session_state["chat_id"] is None
        button(app, "New chat").click().run()
        assert app.session_state["temporary"] is False


def test_delete_all_clears_storage_and_session(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Question")
        assert user_data.list_conversations(db_path=db_path)
        by_key(app, "checkbox", "confirm_delete_all").check().run()
        by_key(app, "button", "delete_all").click().run()
        assert user_data.list_conversations(db_path=db_path) == []
        assert user_data.list_saved(db_path=db_path) == []
        assert user_data.list_feedback(db_path=db_path) == []
        assert app.session_state["messages"] == []
        assert app.session_state["chat_id"] is None
        assert by_key(app, "checkbox", "confirm_delete_all").value is False
        assert not app.exception


def _marker(message):
    import streamlit as st
    st.markdown(f"ACTIONBAR {message['id']}")


def _bars(app):
    return [m.value for m in app.markdown if m.value.startswith("ACTIONBAR")]


def test_action_bar_survives_save_and_reopen(db_path):
    with patch("src.conversation.answer_question", return_value=response()), \
            patch("src.ui.actions.render_save_button", _marker):
        app = start()
        ask(app, "First question")
        assert len(_bars(app)) == 1
        button(app, "New chat").click().run()
        assert _bars(app) == []
        button(app, "First question").click().run()
        assert len(_bars(app)) == 1


def test_action_bar_in_temporary_chat(db_path):
    with patch("src.conversation.answer_question", return_value=response()), \
            patch("src.ui.actions.render_save_button", _marker):
        app = start()
        button(app, "Temporary chat").click().run()
        ask(app, "Private question")
        assert _bars(app) == []


def test_search_treats_wildcards_literally(db_path):
    with patch("src.conversation.answer_question", return_value=response()):
        app = start()
        ask(app, "Retake policy")
        button(app, "New chat").click().run()
        ask(app, "100% attendance")
        assert [c["title"] for c in user_data.list_conversations(search="%", db_path=db_path)] == ["100% attendance"]
        assert user_data.list_conversations(search="_", db_path=db_path) == []


def test_save_failure_does_not_leave_partial_session_history(db_path):
    with patch("src.conversation.answer_question", return_value=response()), \
            patch("src.ui.chat_list.user_data.save_turn", side_effect=OSError("disk error")):
        app = start()
        ask(app, "Question")
        assert app.session_state["messages"] == []
        assert app.session_state["chat_id"] is None
        assert user_data.list_conversations(db_path=db_path) == []
        assert any("Could not save" in item.value for item in app.error)

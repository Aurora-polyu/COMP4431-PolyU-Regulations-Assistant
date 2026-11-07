"""Streamlit integration checks using injected answer-service responses."""
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.conversation import FIXTURE_WARNING

CHUNK = {"chunk_id": "test_1", "section": "5.C Retaking", "printed_page": 33,
         "pdf_page": 45, "text": "Complete passage.\nSecond line."}


def response(status="answered", answer="Grounded answer.", source="handbook", **extra):
    result = {"status": status, "answer": answer, "evidence_source": source,
              "clarification_question": None, "cited_chunks": [CHUNK]}
    result.update(extra)
    return result


def start():
    return AppTest.from_file(Path(__file__).resolve().parent.parent / "app.py", default_timeout=10).run()


def ask(app, question):
    return app.chat_input[0].set_value(question).run()


def contents(app):
    return [m["content"] for m in app.session_state["messages"]]


def test_answer_followup_history_citations_rerun_and_reset():
    seen = []
    def service(question, history):
        seen.append((question, history))
        if len(seen) == 1:
            return response(status="needs_clarification", answer="", clarification_question="Which programme?")
        return response()
    with patch("src.conversation.answer_question", side_effect=service):
        app = start()
        assert not app.selectbox
        ask(app, "First question")
        ask(app, "Undergraduate")
        assert seen[1][1] == [{"role": "user", "content": "First question"},
                               {"role": "assistant", "content": "Which programme?"}]
        assert len(app.expander) == 1
        assert "5.C Retaking" in app.expander[0].label
        assert "printed p. 33 / PDF p. 45" in app.expander[0].label
        assert app.text[0].value == CHUNK["text"]
        app.run()
        assert len(seen) == 2 and len(contents(app)) == 4
        app.button[0].click().run()
        assert contents(app) == []
        assert len(app.expander) == 0
        assert not app.exception


def test_welcome_disappears_on_submit_and_returns_on_reset():
    motto = "To learn and to apply, for the benefit of mankind."
    with patch("src.conversation.answer_question", return_value=response()) as service:
        app = start()
        assert any(motto in item.value for item in app.markdown)
        assert len(app.button) == 1
        ask(app, "A question")
        assert not any(motto in item.value for item in app.markdown)
        assert service.call_args.args == ("A question", [])
        assert app.expander[0].proto.expanded is False
        app.button[0].click().run()
        assert any(motto in item.value for item in app.markdown)
        assert not app.exception


@pytest.mark.parametrize("status", ["answered", "needs_clarification", "insufficient_evidence", "error"])
def test_fixture_warning_survives_all_statuses(status):
    kwargs = {"clarification_question": "Which programme?"} if status == "needs_clarification" else {}
    with patch("src.conversation.answer_question", return_value=response(status=status, answer=FIXTURE_WARNING + "\n\nTest content", source="fixture", **kwargs)):
        app = start()
        ask(app, "Question")
        assert contents(app)[1].count(FIXTURE_WARNING) == 1
        app.run()
        assert any(FIXTURE_WARNING in item.value for item in app.markdown)
        if status != "answered":
            assert not app.expander


def test_safe_error_guidance_and_exceptions_do_not_expose_secrets():
    with patch("src.conversation.answer_question", return_value=response(status="error", answer="Retrieval failed: secret-token")):
        app = start()
        ask(app, "Question")
        assert "handbook search is unavailable" in contents(app)[1]
        assert "secret-token" not in contents(app)[1]
    with patch("src.conversation.answer_question", side_effect=RuntimeError("secret-token")):
        app = start()
        ask(app, "Question")
        assert "secret-token" not in contents(app)[1]
        assert "could not complete" in contents(app)[1]


def test_insufficient_and_clarification_are_distinct_and_history_matches():
    with patch("src.conversation.answer_question", side_effect=[
        response(status="insufficient_evidence", answer="No supporting passage."),
        response(status="needs_clarification", answer="Which programme?", clarification_question="Which programme?"),
        response(),
    ]) as service:
        app = start()
        ask(app, "First")
        ask(app, "Second")
        assert contents(app)[1] == "No supporting passage."
        assert contents(app)[3] == "Which programme?"
        ask(app, "Third")
        assert service.call_args.args[1] == [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "No supporting passage."},
            {"role": "user", "content": "Second"},
            {"role": "assistant", "content": "Which programme?"},
        ]


def test_mixed_fixture_and_handbook_evidence_warning_reaches_ui():
    from src.conversation import answer_question as real_answer
    from src.llm_client import LlmError

    handbook = dict(CHUNK, chunk_id="sec5_C_001")
    fixture = dict(CHUNK, chunk_id="sample_001")

    class FailingModel:
        def complete(self, *args, **kwargs):
            raise LlmError("private detail")

    def mixed_service(question, history):
        return real_answer(question, history, retrieve=lambda *a, **k: [handbook, fixture], llm=FailingModel())

    with patch("src.conversation.answer_question", side_effect=mixed_service):
        app = start()
        ask(app, "Question")
        assert FIXTURE_WARNING in contents(app)[1]
        assert "private detail" not in contents(app)[1]

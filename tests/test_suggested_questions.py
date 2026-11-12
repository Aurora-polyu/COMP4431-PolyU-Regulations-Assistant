"""Suggested questions: data checks and the Streamlit hook."""
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.suggested_questions import POPULAR_QUESTIONS, SUGGESTED_QUESTIONS


def test_each_domain_has_enough_unique_questions():
    assert len(SUGGESTED_QUESTIONS) == 6
    for domain, questions in SUGGESTED_QUESTIONS.items():
        assert len(questions) >= 3, domain
        assert all(q.strip() for q in questions), domain
        assert len(set(questions)) == len(questions), domain


def test_no_duplicates_across_domains():
    every = [q for qs in SUGGESTED_QUESTIONS.values() for q in qs]
    assert len(set(every)) == len(every)


def _script():
    import streamlit as st
    from src.ui.suggestions import render_suggestions
    st.session_state.clicked = render_suggestions()


def test_renders_and_returns_clicked_question():
    app = AppTest.from_function(_script, default_timeout=10).run()
    assert app.session_state.clicked is None
    assert [b.label for b in app.button] == POPULAR_QUESTIONS
    app.button[1].click().run()
    assert app.session_state.clicked == POPULAR_QUESTIONS[1]
    assert not app.exception


def _app_response():
    chunk = {"chunk_id": "t1", "section": "4.H Deferment", "printed_page": 16, "pdf_page": 27, "text": "Text"}
    return {"status": "answered", "answer": "Answer.", "evidence_source": "handbook",
            "clarification_question": None, "cited_chunks": [chunk]}


def _start_app():
    path = Path(__file__).resolve().parent.parent / "app.py"
    return AppTest.from_file(path, default_timeout=10).run()


def test_domain_chip_switches_questions():
    domains = list(SUGGESTED_QUESTIONS)
    app = _start_app()
    app.get("button_group")[0].set_value(domains[2]).run()
    assert [b.label for b in app.button if b.key and b.key.startswith("suggestion_")] == SUGGESTED_QUESTIONS[domains[2]]


def test_new_chat_resets_topic_to_popular():
    app = _start_app()
    app.get("button_group")[0].set_value("Campus services").run()
    next(b for b in app.button if b.label == "New chat").click().run()
    assert app.get("button_group")[0].value == "Popular"
    assert [b.label for b in app.button if b.key and b.key.startswith("suggestion_")] == POPULAR_QUESTIONS


def test_clicking_suggestion_asks_it_and_hides_suggestions():
    question = SUGGESTED_QUESTIONS[list(SUGGESTED_QUESTIONS)[0]][0]
    with patch("src.conversation.answer_question", return_value=_app_response()) as service:
        app = _start_app()
        next(b for b in app.button if b.label == question).click().run()
        assert service.call_args.args[0] == question
        assert not [b for b in app.button if b.key and b.key.startswith("suggestion_")]
        assert not app.exception

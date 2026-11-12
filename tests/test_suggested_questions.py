"""Suggested questions: data checks and the Streamlit hook."""
from streamlit.testing.v1 import AppTest

from src.suggested_questions import SUGGESTED_QUESTIONS


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
    first = list(SUGGESTED_QUESTIONS)[0]
    assert app.session_state.clicked is None
    assert [b.label for b in app.button] == SUGGESTED_QUESTIONS[first]
    app.button[1].click().run()
    assert app.session_state.clicked == SUGGESTED_QUESTIONS[first][1]
    assert not app.exception

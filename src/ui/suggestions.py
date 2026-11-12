"""Starter questions on the empty chat. Returns the clicked question, or None."""
import streamlit as st

from src.suggested_questions import POPULAR_QUESTIONS, SUGGESTED_QUESTIONS


def _ensure_topic():
    if not st.session_state.get("suggestion_domain"):
        st.session_state.suggestion_domain = "Popular"


def render_suggestions() -> str | None:
    holder = st.empty()
    clicked = None
    with holder.container():
        with st.container(key="welcome_navigation"):
            st.markdown("<h1 class='welcome-heading'>What would you like to know?</h1>", unsafe_allow_html=True)
            st.markdown("<p class='welcome-intro'>Choose an example or type your own question below.</p>", unsafe_allow_html=True)
            domain = st.pills("Browse by topic", ["Popular", *SUGGESTED_QUESTIONS],
                              default="Popular", key="suggestion_domain", on_change=_ensure_topic) or "Popular"
            st.markdown("<div class='suggestions-label'>Suggested questions</div>", unsafe_allow_html=True)
            questions = POPULAR_QUESTIONS if domain == "Popular" else SUGGESTED_QUESTIONS[domain]
            for i, question in enumerate(questions):
                if st.button(question, key=f"suggestion_{i}", width="stretch"):
                    clicked = question
    if clicked:
        holder.empty()  # app.py answers in this same run, so clear the chips now
    return clicked

"""Starter questions on the empty chat. Returns the clicked question, or None."""
import streamlit as st

from src.suggested_questions import SUGGESTED_QUESTIONS

HOW_TO_USE = (
    "1. Ask a question about the handbook.  \n"
    "2. Open the sources under the answer to read the passages.  \n"
    "3. Rate, save or report an answer."
)


def render_suggestions() -> str | None:
    st.markdown(HOW_TO_USE)
    domains = list(SUGGESTED_QUESTIONS)
    domain = st.pills("Topic", domains, default=domains[0], key="suggestion_domain",
                      label_visibility="collapsed") or domains[0]
    clicked = None
    for i, question in enumerate(SUGGESTED_QUESTIONS[domain]):
        if st.button(question, key=f"suggestion_{i}", width="stretch"):
            clicked = question
    return clicked

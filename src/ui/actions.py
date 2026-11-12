"""Per-answer action bar shared by collection and feedback hooks."""

import streamlit as st

from src.ui.collection import render_save_button
from src.ui.feedback import render_rating, render_report


def render_action_bar(message):
    if st.session_state.get("temporary") or message.get("role") != "assistant" or not message.get("id"):
        return
    with st.container(key=f"answer_actions_{message['id']}"):
        save, rating, report = st.columns([1, 1.25, 1], vertical_alignment="center")
        with save:
            render_save_button(message)
        with rating:
            render_rating(message)
        with report:
            render_report(message)

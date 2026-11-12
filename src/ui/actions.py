"""Per-answer action bar shared by collection and feedback hooks."""

import streamlit as st

from src.ui.collection import render_save_button
from src.ui.feedback import render_rating_and_report


def render_action_bar(message):
    if message.get("role") != "assistant" or not message.get("id"):
        return
    with st.container(key=f"actions_{message['id']}"):
        render_save_button(message)
        render_rating_and_report(message)

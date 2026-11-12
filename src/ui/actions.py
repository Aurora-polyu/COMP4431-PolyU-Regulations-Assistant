"""Per-answer action bar shared by collection and feedback hooks."""

from src.ui.collection import render_save_button
from src.ui.feedback import render_rating_and_report


def render_action_bar(message):
    if message.get("role") != "assistant" or not message.get("id"):
        return
    render_save_button(message)
    render_rating_and_report(message)

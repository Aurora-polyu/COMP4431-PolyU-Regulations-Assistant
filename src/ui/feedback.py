"""Rating and report hooks under each assistant answer."""

import streamlit as st

from src import user_data

REPORT_REASONS = [
    "Select a reason…",
    "wrong fact",
    "missing condition or exception",
    "wrong or irrelevant source",
    "out of date",
    "other",
]

RATE_STATUSES = {"answered", "needs_clarification"}
REPORT_STATUSES = {"answered", "needs_clarification", "insufficient_evidence"}


def _eligible(message, statuses):
    return (message.get("role") == "assistant" and message.get("id")
            and message.get("status") in statuses)


def _chunk_ids(message):
    return [c.get("chunk_id") for c in message.get("chunks", [])
            if isinstance(c, dict) and isinstance(c.get("chunk_id"), str)]


def _on_rating_changed(message):
    thumbs = st.session_state.get(f"rate_{message['id']}")
    if thumbs is None:
        return
    user_data.set_rating(message["id"], 1 if thumbs == 1 else -1,
                         message.get("question"), message.get("content"), _chunk_ids(message))


def _submit_report(message):
    key = f"report_{message['id']}"
    reason = st.session_state.get(f"reason_{key}")
    if not reason or reason == "Select a reason…":
        st.toast("Please select a reason before submitting")
        return
    user_data.add_report(message["id"], reason,
                         st.session_state.get(f"comment_{key}", "") or None,
                         message.get("question"), message.get("content"), _chunk_ids(message))
    st.toast("Thanks, report saved")


def _widget_default(message):
    preset = st.session_state.get(f"rate_{message['id']}")
    if preset in (0, 1):
        return preset
    stored = user_data.get_rating(message["id"])
    return 1 if stored == 1 else (0 if stored == -1 else None)


def render_rating_and_report(message):
    if not _eligible(message, RATE_STATUSES) and not _eligible(message, REPORT_STATUSES):
        return
    with st.container(key=f"feedback_{message['id']}"):
        columns = st.columns([0.35, 0.65], vertical_alignment="bottom")
        with columns[0]:
            if _eligible(message, RATE_STATUSES):
                default = _widget_default(message)
                if default is None and message.get("status") == "answered":
                    default = 0  # hold the current selection on answered replies
                st.feedback("thumbs", key=f"rate_{message['id']}",
                            default=default,
                            on_change=_on_rating_changed, args=(message,))
        with columns[1]:
            if _eligible(message, REPORT_STATUSES):
                with st.popover("Report", key=f"report_{message['id']}"):
                    st.selectbox("Reason", REPORT_REASONS, key=f"reason_report_{message['id']}")
                    st.text_area("Comment", max_chars=500, key=f"comment_report_{message['id']}")
                    st.button("Submit", key=f"submit_report_{message['id']}",
                              on_click=_submit_report, args=(message,))

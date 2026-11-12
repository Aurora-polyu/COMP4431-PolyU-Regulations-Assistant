"""English-language Streamlit interface for the handbook answer service."""

import uuid
from pathlib import Path

import streamlit as st

from src import user_data
from src.conversation import FIXTURE_WARNING, NO_EVIDENCE_ANSWER, answer_question
from src.ui.actions import render_action_bar
from src.ui.chat_list import persist_turn, render_chat_list
from src.ui.collection import render_collection_view
from src.ui.sources import render_source_popovers, strip_citation_markers
from src.ui.suggestions import render_suggestions

st.set_page_config(
    page_title="PolyU Academic Regulations Assistant",
    page_icon="assets/polyu_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

TITLE = "PolyU Academic Regulations Assistant"
MOTTO = "To learn and to apply, for the benefit of mankind."

STYLESHEET = Path(__file__).resolve().parent / "assets" / "style.css"
st.markdown(f"<style>{STYLESHEET.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "view" not in st.session_state:
    st.session_state.view = "Chat"
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
if "temporary" not in st.session_state:
    st.session_state.temporary = False


def _new_chat():
    st.session_state.messages = []
    st.session_state.chat_id = None
    st.session_state.temporary = False
    st.session_state.view = "Chat"
    st.session_state.pop("suggestion_domain", None)


def _delete_all():
    try:
        user_data.delete_all()
    except Exception:
        st.session_state.delete_all_error = True
        return
    for message in st.session_state.messages:
        message_id = message.get("id")
        if message_id:
            st.session_state.pop(f"rate_{message_id}", None)
    st.session_state.messages = []
    st.session_state.chat_id = None
    st.session_state.temporary = False
    st.session_state.view = "Chat"
    st.session_state.search = ""
    st.session_state.delete_all_success = True


@st.dialog("Your data has been deleted", width="small")
def _show_delete_confirmation():
    with st.container(key="delete_success"):
        st.markdown("<div class='save-success-icon' aria-hidden='true'>✓</div>", unsafe_allow_html=True)
        st.markdown("### All clear")
        st.write("Your chats, saved answers and feedback have been deleted.")
        if st.button("Continue", key="continue_after_delete", type="primary", use_container_width=True):
            st.rerun()


def _show_collection():
    st.session_state.view = "Collection"


ERROR_MESSAGES = {
    "no_api_key": "The model provider API key is not configured. Add it to your local .env file and restart the app.",
    "retrieval": "The handbook search is unavailable. Check the selected index and rebuild it if needed; see the setup guide.",
    "provider": "The answer service is unavailable. Check your API configuration and connection, then try again.",
}
GENERIC_ERROR = "The answer service could not complete the request. Please try again and check the setup guide if the problem continues."


def _safe_error(error_code):
    """Map a service error code to fixed guidance without displaying raw details."""
    return ERROR_MESSAGES.get(error_code, GENERIC_ERROR)


def _display_response(resp):
    """Return the exact text to display and retain in conversation history."""
    status = resp.get("status")
    answer = resp.get("answer") if isinstance(resp.get("answer"), str) else ""
    # The service prefixes fixture answers with the warning; strip it so it is
    # added back exactly once, including on safe error messages.
    answer = answer.removeprefix(FIXTURE_WARNING).strip()
    if status == "answered":
        content = answer or "The answer service returned an empty answer. Please try again."
    elif status == "needs_clarification":
        question = resp.get("clarification_question")
        question = question.strip() if isinstance(question, str) else ""
        content = "\n\n".join(dict.fromkeys(part for part in (answer, question) if part))
        content = content or "Could you clarify your question?"
    elif status == "insufficient_evidence":
        content = answer or NO_EVIDENCE_ANSWER
    else:
        content = _safe_error(resp.get("error_code"))
    if resp.get("evidence_source") == "fixture":
        return f"{FIXTURE_WARNING}\n\n{content}"
    return content


def _render_message(message):
    with st.chat_message(message["role"], avatar=f"assets/{message['role']}_avatar.svg"):
        chunks = message.get("chunks", [])
        content = strip_citation_markers(message["content"], chunks) if message["role"] == "assistant" else message["content"]
        st.markdown(content)
        render_source_popovers(chunks)


def render_turn(question):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    user = {"role": "user", "content": question, "chunks": []}
    st.session_state.messages.append(user)
    _render_message(user)
    try:
        with st.spinner("Thinking..."):
            response = answer_question(question, history)
        content = _display_response(response)
        chunks = response.get("cited_chunks", []) if response.get("status") == "answered" else []
        if not isinstance(chunks, list):
            chunks = []
        status = response.get("status")
        evidence_source = response.get("evidence_source")
    except Exception:
        content = GENERIC_ERROR
        chunks = []
        status = "error"
        evidence_source = None
    message = {
        "role": "assistant",
        "content": content,
        "chunks": chunks,
        "id": uuid.uuid4().hex,
        "question": question,
        "status": status,
        "evidence_source": evidence_source,
    }
    st.session_state.messages.append(message)
    try:
        persist_turn(user, message)
    except Exception:
        # A failed transaction stored neither message; keep session history aligned.
        del st.session_state.messages[-2:]
        st.error("Could not save this conversation. Check local storage and try your question again.")
        return
    # Rerun so the sidebar list and the history loop (message + action bar) redraw.
    st.rerun()


with st.sidebar:
    with st.container(key="sidebar_brand"):
        logo, name = st.columns([1, 3], vertical_alignment="center")
        with logo:
            st.image("assets/polyu_logo.svg", width=55)
        with name:
            st.markdown(f"<div class='sidebar-title'>{TITLE}</div>", unsafe_allow_html=True)
    with st.container(key="new_chat_button"):
        st.button("New chat", key="new_chat", on_click=_new_chat, use_container_width=True)
    with st.expander("Search chats"):
        st.text_input("Search chat titles", key="search", label_visibility="collapsed", placeholder="Search chat titles")
    st.button("My collection", key="show_collection", on_click=_show_collection, use_container_width=True)
    st.markdown("**Recent chats**")
    with st.container(height=240, border=False, key="recent_chats"):
        render_chat_list()
    with st.container(key="sidebar_footer"):
        with st.expander("About & handbook"):
            st.markdown(
                "1. Ask a question about the handbook.\n"
                "2. Open the sources under the answer to read the passages.\n"
                "3. Rate, save or report an answer."
            )
            st.markdown("**Handbook**  \n2026/27 Student Handbook for Taught Programmes")
        with st.popover("Delete all my data", use_container_width=True):
            st.warning("This permanently deletes all chats, saved answers and feedback. Continue?")
            st.button(
                "Confirm delete",
                key="delete_all",
                on_click=_delete_all,
                use_container_width=True,
            )
        if st.session_state.pop("delete_all_error", False):
            st.error("Could not delete your data. Please try again.")

if st.session_state.pop("delete_all_success", False):
    _show_delete_confirmation()


if st.session_state.view == "Collection":
    render_collection_view()
else:
    if st.session_state.temporary:
        st.caption("Temporary chat: not saved locally. Save and feedback are unavailable; questions are sent to the model provider.")
    with st.bottom:
        question = st.chat_input("Ask about PolyU academic regulations...")
        with st.container(key="handbook_guidance"):
            st.caption("Check the official handbook or contact your department for decisions about your situation.")
    if not st.session_state.messages and not question:
        welcome = st.empty()
        welcome.markdown(f"<div class='welcome'>{MOTTO}</div>", unsafe_allow_html=True)
        suggestion = render_suggestions()
        if suggestion:
            welcome.empty()
            question = suggestion

    for message in st.session_state.messages:
        _render_message(message)
        render_action_bar(message)

    if question:
        render_turn(question)

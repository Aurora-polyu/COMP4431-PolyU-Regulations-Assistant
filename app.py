"""English-language Streamlit interface for the handbook answer service."""

import streamlit as st

from src.conversation import FIXTURE_WARNING, NO_EVIDENCE_ANSWER, answer_question

st.set_page_config(
    page_title="PolyU Academic Regulations Assistant",
    page_icon="assets/polyu_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

TITLE = "PolyU Academic Regulations Assistant"
MOTTO = "To learn and to apply, for the benefit of mankind."

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@600&display=swap');
    :root { --red: #9E2435; --red-deep: #7C1D2A; --ink: #2B2B2D; }
    html, body, [data-testid="stAppViewContainer"] { font-family: Geist, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #FFFFFF; }
    [data-testid="stMainBlockContainer"] { max-width: 880px; padding-top: 32px; padding-bottom: 32px; }
    [data-testid="stSidebar"] { background: #F7F5F4; min-width: 320px; max-width: 320px; transform: none !important; margin-left: 0 !important; visibility: visible !important; }
    [data-testid="stSidebarHeader"], [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarContent"] { padding: 24px; display: flex; flex-direction: column; }
    [data-testid="stSidebarUserContent"] { flex: 1; padding-bottom: 0; }
    [data-testid="stSidebarUserContent"] > div { height: 100%; }
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] { min-height: 100%; }
    [data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has(> .st-key-handbook_footer) { margin-top: auto; }
    .st-key-sidebar_picture [data-testid="stFullScreenFrame"] { display: flex; justify-content: center; }
    .st-key-sidebar_picture img { display: block; width: auto !important; max-width: 100%; max-height: 300px; height: auto; margin: 0 auto; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 16px; }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p { font-size: 14px; line-height: 1.55; }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] strong { font-size: 15px; }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        width: 100%; margin-top: 16px; color: white; background: var(--red); border: 0; border-radius: 8px;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover { background: var(--red-deep); color: white; }
    .sidebar-title { font-family: "Source Sans 3", sans-serif; font-size: 21px; font-weight: 600; line-height: 1.3; overflow-wrap: break-word; color: var(--ink); }
    .welcome { margin: 50vh auto 32px; max-width: 700px; text-align: center; font-size: 24px; font-weight: 600; line-height: 1.4; color: #77777A; }
    [data-testid="stChatMessage"] { background: transparent; padding: 0; margin: 16px 0; }
    [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) { flex-direction: row-reverse; }
    [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] {
        flex: 0 1 auto; width: fit-content; max-width: 80%; margin: 0; background: #F7F5F4; border-radius: 20px; padding: 8px 16px;
    }
    [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) [data-testid="stChatMessageContent"] { min-width: 0; }
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] pre, [data-testid="stChatInput"] textarea {
        font-size: 16px; line-height: 1.6; overflow-wrap: anywhere;
    }
    [data-testid="stBottomBlockContainer"] { max-width: 880px; margin-left: auto; margin-right: auto; }
    [data-testid="stChatInput"] { min-height: 56px; border: 1px solid #E7E0DD; border-radius: 16px; }
    [data-testid="stChatInput"]:focus-within { border-color: var(--red); }
    [data-testid="stExpander"] { border: 1px solid #E7E0DD; border-radius: 8px; }
    [data-testid="stExpander"] summary { color: var(--red-deep); }
    @media (max-width: 767px) {
        [data-testid="stAppScrollToBottomContainer"] { left: 320px !important; width: calc(100% - 320px) !important; }
    }
    @media (max-width: 640px) {
        [data-testid="stSidebar"] { position: relative !important; min-width: 155px; max-width: 155px; width: 155px !important; }
        [data-testid="stSidebarContent"] { padding: 8px; }
        [data-testid="stAppScrollToBottomContainer"] { left: 155px !important; width: calc(100% - 155px) !important; }
        [data-testid="stMainBlockContainer"] { padding-left: 16px; padding-right: 16px; }
        .sidebar-title { font-size: 20px; }
        .welcome { font-size: 22px; }
        [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] { max-width: 95%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def _new_chat():
    st.session_state.messages = []


def _safe_error(answer):
    """Map service failures to fixed guidance without displaying raw details."""
    text = answer.removeprefix(FIXTURE_WARNING).strip()
    if text.startswith("MODEL_API_KEY is not set."):
        return "The model provider API key is not configured. Add it to your local .env file and restart the app."
    if text.startswith(("Retrieval failed:", "Retrieval is not available:")):
        return "The handbook search is unavailable. Check the selected index and rebuild it if needed; see the setup guide."
    if text.startswith(("Model provider returned HTTP", "Could not reach the model provider")):
        return "The answer service is unavailable. Check your API configuration and connection, then try again."
    return "The answer service could not complete the request. Please try again and check the setup guide if the problem continues."


def _display_response(resp):
    """Return the exact text to display and retain in conversation history."""
    status = resp.get("status")
    answer = resp.get("answer") if isinstance(resp.get("answer"), str) else ""
    fixture = resp.get("evidence_source") == "fixture"
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
        content = _safe_error(answer)
    return f"{FIXTURE_WARNING}\n\n{content}" if fixture else content


def _render_message(message):
    with st.chat_message(message["role"], avatar=f"assets/{message['role']}_avatar.svg"):
        st.markdown(message["content"])
        for chunk in message.get("chunks", []):
            title = (f"📄 {chunk.get('section', 'Source')} · "
                     f"printed p. {chunk.get('printed_page', '?')} / PDF p. {chunk.get('pdf_page', '?')}")
            with st.expander(title, expanded=False):
                st.text(chunk.get("text", ""))


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
    except Exception:
        content = _safe_error("")
        chunks = []
    message = {"role": "assistant", "content": content, "chunks": chunks}
    st.session_state.messages.append(message)
    _render_message(message)


with st.sidebar:
    logo, name = st.columns([1, 3], vertical_alignment="center")
    with logo:
        st.image("assets/polyu_logo.svg", width=55)
    with name:
        st.markdown(f"<div class='sidebar-title'>{TITLE}</div>", unsafe_allow_html=True)
    st.button("New conversation", on_click=_new_chat, use_container_width=True)
    st.markdown("**About this assistant**")
    st.markdown("Ask questions about academic regulations using the student handbook.")
    with st.container(key="sidebar_picture"):
        st.image("assets/sidebar-picture.jpeg", width="stretch")
    with st.container(key="handbook_footer"):
        st.markdown("**Handbook**  \n2026/27 Student Handbook for Taught Programmes")
        st.markdown("Check the official handbook or contact your department for decisions about your situation.")

question = st.chat_input("Ask about PolyU academic regulations...")
if not st.session_state.messages and not question:
    st.markdown(f"<div class='welcome'>{MOTTO}</div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    _render_message(message)

if question:
    render_turn(question)

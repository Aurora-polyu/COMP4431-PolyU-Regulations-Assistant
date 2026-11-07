"""English-language Streamlit interface for the handbook answer service."""

import streamlit as st

from src.conversation import FIXTURE_WARNING, NO_EVIDENCE_ANSWER, answer_question

st.set_page_config(
    page_title="PolyU Academic Regulations Assistant",
    page_icon="polyu_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TITLE = "PolyU Academic Regulations Assistant"
SUBTITLE = "Ask about academic rules, deadlines, or eligibility using the student handbook."
EXAMPLES = [
    "When is the add/drop period?",
    "What happens if I fail a subject?",
    "Can I withdraw after the deadline?",
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap');

    :root {
        --red:       #9E2435;
        --red-deep:  #7C1D2A;
        --red-dark:  #5E1520;
        --red-bright:#B23143;
        --red-tint:  #F7EBED;
        --ink:       #2B2B2D;
        --gray:      #5C5C5E;
        --hairline:  #E7E0DD;
        --paper:     #FCFBFA;
        --serif: "Cormorant Garamond", Georgia, serif;
    }


    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: var(--serif);
        color: var(--ink);
    }
    [data-testid="stAppViewContainer"] { background: #FFFFFF; }
    [data-testid="stMainBlockContainer"] { padding-top: 1.2rem; max-width: 1000px; }


    .top-strip { height: 3px; background: var(--red); margin: -1.2rem -2rem 0 -2rem; }
    .header-bar {
        display: flex; align-items: center; gap: 16px;
        padding: 10px 0 14px 0;
        border-bottom: 1px solid var(--hairline);
        margin-bottom: 26px;
    }
    .header-logo { flex: 0 0 auto; }


    .hero-title {
        font-family: var(--serif);
        font-weight: 600;
        font-size: 2.2rem;
        color: var(--ink);
        letter-spacing: .3px;
        margin: 6px 0 4px 0;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: var(--gray);
        margin: 0 0 8px 0;
        font-style: italic;
        line-height: 1.5;
    }
    .hero-rule {
        border: none; height: 2px; margin: 10px 0 22px 0;
        background: linear-gradient(90deg, var(--red) 0%, var(--red) 22%, var(--hairline) 22.5%, var(--hairline) 100%);
    }
    .hero-rule::before { content: ""; }


    [data-testid="stButton"] button {
        background: var(--red);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.45rem 1.1rem;
        font-family: var(--serif);
        font-weight: 500;
        white-space: nowrap;
    }
    [data-testid="stButton"] button:hover { background: var(--red-deep); color: #fff; }


    [data-testid="stChatMessage"] { background: transparent; padding: 6px 0; }
    [data-testid="stChatMessageContent"] {
        max-width: 720px;
        padding: 14px 18px;
        border-radius: 16px;
        line-height: 1.8;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
        background: var(--paper);
        color: var(--ink);
        border: 1px solid var(--hairline);
        border-left: 3px solid var(--red);
        border-bottom-left-radius: 4px;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, var(--red-bright) 0%, var(--red-deep) 100%);
        color: #FFFFFF;
        border-bottom-right-radius: 4px;
        box-shadow: 0 12px 28px rgba(158, 36, 53, .26);
    }


    [data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid var(--hairline);
        border-left: 3px solid var(--red);
        border-radius: 8px;
        margin-top: 8px;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary { color: var(--red-deep); font-size: .92em; font-weight: 500; }
    [data-testid="stExpander"] details { border: none; }
    [data-testid="stExpander"] p { color: var(--ink); }


    [data-testid="stChatInput"] {
        background: #FFFFFF;
        border: 1px solid var(--hairline);
        border-radius: 14px;
        padding: 6px 10px;
        box-shadow: 0 6px 20px rgba(43,43,45,.05);
    }
    [data-testid="stChatInput"]:focus-within { border-color: var(--red); }
    [data-testid="stChatInput"] textarea { color: var(--ink); font-family: var(--serif); }


    .welcome {
        background: var(--paper);
        border: 1px solid var(--hairline);
        border-top: 3px solid var(--red);
        border-radius: 12px;
        padding: 26px 28px;
        margin: 8px 0 20px 0;
    }
    .welcome h3 { font-family: var(--serif); font-weight: 600; color: var(--ink); margin: 0 0 6px 0; }
    .welcome p  { color: var(--gray); margin: 0 0 16px 0; }
    .example-chip {
        display: inline-block;
        border: 1px solid var(--red);
        color: var(--red-deep);
        border-radius: 999px;
        padding: 7px 16px;
        margin: 0 8px 8px 0;
        cursor: pointer;
        font-family: var(--serif);
        transition: all .15s ease;
    }
    .example-chip:hover { background: var(--red); color: #fff; }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []


def _new_chat():
    st.session_state.messages = []
    st.session_state.pop("_pending_question", None)


def _safe_error(answer):
    """Map service failures to fixed guidance without displaying raw details."""
    text = answer.removeprefix(FIXTURE_WARNING).strip()
    if text.startswith("DEEPSEEK_API_KEY is not set."):
        return "The DeepSeek API key is not configured. Add it to your local .env file and restart the app."
    if text.startswith(("Retrieval failed:", "Retrieval is not available:")):
        return "The handbook search is unavailable. Check the selected index and rebuild it if needed; see the setup guide."
    if text.startswith(("DeepSeek returned HTTP", "Could not reach DeepSeek")):
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
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        for chunk in message.get("chunks", []):
            title = (f"📄 {chunk.get('section', 'Source')} · "
                     f"printed p. {chunk.get('printed_page', '?')} / PDF p. {chunk.get('pdf_page', '?')}")
            with st.expander(title):
                st.text(chunk.get("text", ""))


def render_turn(question):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    user = {"role": "user", "content": question, "chunks": []}
    st.session_state.messages.append(user)
    _render_message(user)
    try:
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


st.markdown("<div class='top-strip'></div>", unsafe_allow_html=True)
c_logo, c_new = st.columns([1.2, 0.9], vertical_alignment="center")
with c_logo:
    st.image("polyu_logo.png", width=230)
with c_new:
    st.button("New Conversation", on_click=_new_chat, use_container_width=True)

st.markdown(f"<div class='hero-title'>{TITLE}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{SUBTITLE}</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-rule'></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    _render_message(message)

pending = st.session_state.pop("_pending_question", None)
if not st.session_state.messages and not pending:
    st.markdown(f"<div class='welcome'><h3>Try asking</h3><p>{SUBTITLE}</p></div>", unsafe_allow_html=True)
    columns = st.columns(3)
    for index, example in enumerate(EXAMPLES):
        if columns[index].button(example, use_container_width=True):
            pending = example

question = st.chat_input("Ask about PolyU academic regulations...")
if pending:
    render_turn(pending)
elif question:
    render_turn(question)

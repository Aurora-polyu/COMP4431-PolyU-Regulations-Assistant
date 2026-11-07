# app.py — Member 4: Streamlit UI + 集成
# 设计参考 PolyU 官网:砖红 #9E2435、白底、校徽、三语切换(英/简/繁)。
# 英文用 Cormorant Garamond(衬线),中文用宋体(SimSun/Songti)。
# 当前用 src/mock_backend.py 的假后端;Member 3 完成后,只需改 import。
import streamlit as st

from src.mock_backend import answer_question  # TODO: 换成 from src.conversation import answer_question

st.set_page_config(
    page_title="PolyU Academic Regulations Assistant",
    page_icon="polyu_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# 三语文案
# ---------------------------------------------------------------------------
LANG_OPTIONS = [("English", "en"), ("简体中文", "zh-Hans"), ("繁體中文", "zh-Hant")]
LANG_LABELS = [label for label, _ in LANG_OPTIONS]
LANG_CODE_BY_LABEL = {label: code for label, code in LANG_OPTIONS}

STRINGS = {
    "en": {
        "title": "PolyU Academic Regulations Assistant",
        "subtitle": "Ask about academic rules, deadlines, or your eligibility — every answer cites the exact handbook section.",
        "language": "Language",
        "new_chat": "New Conversation",
        "input_placeholder": "Ask about PolyU academic regulations...",
        "insufficient": "I couldn't find enough evidence in the handbook to answer this confidently. Please rephrase or ask a different question.",
        "error": "⚠️ Something went wrong. Please try again.",
        "clarify_fallback": "Could you clarify?",
        "source": "Source",
        "printed": "printed p.",
        "pdf": "PDF p.",
        "try_asking": "Try asking",
        "examples": [
            "When is the add/drop period?",
            "What happens if I fail a subject?",
            "Can I withdraw after the deadline?",
        ],
    },
    "zh-Hans": {
        "title": "理大学术规章助理",
        "subtitle": "查询学业规则、重要日期或资格条件 —— 每个答案都会标明对应的手册章节。",
        "language": "语言",
        "new_chat": "开始新对话",
        "input_placeholder": "询问理大学业规章…",
        "insufficient": "在手册中未找到足够依据来回答此问题，请换个说法或询问其他问题。",
        "error": "⚠️ 出了点问题，请重试。",
        "clarify_fallback": "能请您说明得更具体一些吗？",
        "source": "来源",
        "printed": "印刷页",
        "pdf": "PDF页",
        "try_asking": "可以试试这样问",
        "examples": [
            "加退课的时间是什么时候？",
            "挂科了会怎样？",
            "截止日期之后还能退课吗？",
        ],
    },
    "zh-Hant": {
        "title": "理大學術規章助理",
        "subtitle": "查詢學業規則、重要日期或資格條件 —— 每個答案都會標明對應的手冊章節。",
        "language": "語言",
        "new_chat": "開始新對話",
        "input_placeholder": "詢問理大學業規章…",
        "insufficient": "在手冊中未找到足夠依據來回答此問題，請換個說法或詢問其他問題。",
        "error": "⚠️ 出了點問題，請重試。",
        "clarify_fallback": "能請您說明得更具體一些嗎？",
        "source": "來源",
        "printed": "印刷頁",
        "pdf": "PDF頁",
        "try_asking": "可以試試這樣問",
        "examples": [
            "加退課的時間是什麼時候？",
            "掛科了會怎樣？",
            "截止日期之後還能退課嗎？",
        ],
    },
}


# ---------------------------------------------------------------------------
# PolyU 皮肤:砖红 + 白 + 衬线字体
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Serif+SC:wght@400;500&display=swap');

    :root {
        --red:       #9E2435;   /* PolyU 砖红 */
        --red-deep:  #7C1D2A;
        --red-dark:  #5E1520;
        --red-bright:#B23143;
        --red-tint:  #F7EBED;
        --ink:       #2B2B2D;
        --gray:      #5C5C5E;
        --hairline:  #E7E0DD;
        --paper:     #FCFBFA;
        --serif: "Cormorant Garamond", Georgia, "Songti SC", "STSong", "SimSun",
                 "Noto Serif SC", serif;
    }

    /* 全局:英文衬线 + 中文宋体 */
    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: var(--serif);
        color: var(--ink);
    }
    [data-testid="stAppViewContainer"] { background: #FFFFFF; }
    [data-testid="stMainBlockContainer"] { padding-top: 1.2rem; max-width: 1000px; }

    /* ── 顶部横条 + 页头栏 ── */
    .top-strip { height: 3px; background: var(--red); margin: -1.2rem -2rem 0 -2rem; }
    .header-bar {
        display: flex; align-items: center; gap: 16px;
        padding: 10px 0 14px 0;
        border-bottom: 1px solid var(--hairline);
        margin-bottom: 26px;
    }
    .header-logo { flex: 0 0 auto; }

    /* ── 页头标题区 ── */
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

    /* 语言下拉:确保下拉面板宽、字不截断 */
    [data-testid="stSelectbox"] > div[data-baseweb="select"] > div {
        background: #FFFFFF;
        border: 1px solid var(--hairline);
        border-radius: 999px;
        padding: 4px 12px;
        color: var(--ink);
        font-family: var(--serif);
        min-width: 130px;
    }
    [data-testid="stSelectbox"] > div[data-baseweb="select"] > div > div {
        white-space: nowrap;
        overflow: visible;
    }
    [data-testid="stSelectbox"] > div[data-baseweb="select"] > div:hover { border-color: var(--red); }
    /* 下拉展开的面板(浮层) */
    [data-baseweb="popover"] [data-baseweb="menu"] li,
    [data-testid="stSelectbox"] [role="listbox"] li {
        font-family: var(--serif);
        white-space: nowrap;
        min-width: 130px;
        color: var(--ink);
    }

    /* 按钮:四角圆滑矩形,禁止换行(避免 New Conversation 被切成两段) */
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

    /* ── 聊天气泡 ── */
    [data-testid="stChatMessage"] { background: transparent; padding: 6px 0; }
    [data-testid="stChatMessageContent"] {
        max-width: 720px;
        padding: 14px 18px;
        border-radius: 16px;
        line-height: 1.8;
    }
    /* AI 气泡:纸白 + 描边 + 左侧红点 */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
        background: var(--paper);
        color: var(--ink);
        border: 1px solid var(--hairline);
        border-left: 3px solid var(--red);
        border-bottom-left-radius: 4px;
    }
    /* 用户气泡:砖红渐变 */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, var(--red-bright) 0%, var(--red-deep) 100%);
        color: #FFFFFF;
        border-bottom-right-radius: 4px;
        box-shadow: 0 12px 28px rgba(158, 36, 53, .26);
    }

    /* ── 引用来源卡片 ── */
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

    /* ── 输入框 ── */
    [data-testid="stChatInput"] {
        background: #FFFFFF;
        border: 1px solid var(--hairline);
        border-radius: 14px;
        padding: 6px 10px;
        box-shadow: 0 6px 20px rgba(43,43,45,.05);
    }
    [data-testid="stChatInput"]:focus-within { border-color: var(--red); }
    [data-testid="stChatInput"] textarea { color: var(--ink); font-family: var(--serif); }

    /* ── 空状态:欢迎卡片 ── */
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


# ---------------------------------------------------------------------------
# 状态
# ---------------------------------------------------------------------------
if "lang_code" not in st.session_state:
    st.session_state.lang_code = "en"
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 每条: {"role": "user"|"assistant", "content": str, "chunks": [...]}


def t(key):
    return STRINGS[st.session_state.lang_code][key]


def _set_lang():
    label = st.session_state.get("lang_widget")
    if label in LANG_CODE_BY_LABEL:
        st.session_state.lang_code = LANG_CODE_BY_LABEL[label]


def _new_chat():
    st.session_state.messages = []
    st.session_state.pop("_pending_question", None)


# ---------------------------------------------------------------------------
# 页头栏:校徽(最左) + 「新对话」+ 语言下拉(右上角)
# ---------------------------------------------------------------------------
st.markdown("<div class='top-strip'></div>", unsafe_allow_html=True)

c_logo, c_new, c_lang = st.columns([1.2, 0.9, 1.1], vertical_alignment="center")
with c_logo:
    st.image("polyu_logo.png", width=230)
with c_new:
    st.button(t("new_chat"), on_click=_new_chat, use_container_width=True)
with c_lang:
    st.selectbox(
        t("language"),
        LANG_LABELS,
        index=[c for _, c in LANG_OPTIONS].index(st.session_state.lang_code),
        key="lang_widget",
        on_change=_set_lang,
        label_visibility="collapsed",
    )


# ---------------------------------------------------------------------------
# 标题区
# ---------------------------------------------------------------------------
st.markdown(f"<div class='hero-title'>{t('title')}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t('subtitle')}</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-rule'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 处理一轮问答(抽成函数,供输入框和示例按钮共用)
# ---------------------------------------------------------------------------
def render_turn(question):
    st.session_state.messages.append({"role": "user", "content": question, "chunks": []})
    with st.chat_message("user"):
        st.markdown(question)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    with st.chat_message("assistant"):
        try:
            resp = answer_question(question, history)
            status = resp.get("status", "error")

            if status == "answered":
                content = resp["answer"]
            elif status == "needs_clarification":
                clarification = resp.get("clarification_question") or t("clarify_fallback")
                content = "\n\n".join(part for part in (resp.get("answer"), clarification) if part)
            elif status == "insufficient_evidence":
                content = t("insufficient")
            else:
                content = t("error")
            st.markdown(content)

            chunks = resp.get("cited_chunks", [])
            for c in chunks:
                title = "📄 {} · {}{} / {}{}".format(
                    c.get("section", t("source")),
                    t("printed"), c.get("printed_page", "?"),
                    t("pdf"), c.get("pdf_page", "?"),
                )
                with st.expander(title):
                    st.write(c.get("text", ""))

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": content,
                    "chunks": chunks,
                }
            )
        except Exception:
            content = t("error")
            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content, "chunks": []})


# ---------------------------------------------------------------------------
# 历史消息
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("chunks"):
            for c in msg["chunks"]:
                title = "📄 {} · {}{} / {}{}".format(
                    c.get("section", t("source")),
                    t("printed"), c.get("printed_page", "?"),
                    t("pdf"), c.get("pdf_page", "?"),
                )
                with st.expander(title):
                    st.write(c.get("text", ""))


# ---------------------------------------------------------------------------
# 空状态欢迎卡片(带示例问题) 或 输入框
# ---------------------------------------------------------------------------
pending = st.session_state.pop("_pending_question", None)

if not st.session_state.messages and not pending:
    st.markdown(
        f"<div class='welcome'><h3>{t('try_asking')}</h3><p>{t('subtitle')}</p></div>",
        unsafe_allow_html=True,
    )
    ex_cols = st.columns(3)
    for i, ex in enumerate(t("examples")):
        if ex_cols[i].button(ex, use_container_width=True):
            pending = ex

question = st.chat_input(t("input_placeholder"))

if pending:
    render_turn(pending)
elif question:
    render_turn(question)

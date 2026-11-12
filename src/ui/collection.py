"""My Collection: save an answered message and browse saved answers later.

Replaces the branch-1 stubs that ``app.py`` calls. The storage layer lives in
``src/user_data.py`` (Member A); citation helpers live in ``src/ui/sources.py``.
See ``docs/tasks/member-b-collection-design.md`` for the agreed behaviour.
"""

import streamlit as st

from src import user_data
from src.ui.sources import render_source_popovers, strip_citation_markers

EDITION = "2026/27"
BANNER = "Saved answers are copies. Check the official handbook before acting."
EMPTY_STATE = "Nothing saved yet. Use Save under an answer."
NO_MATCH = "No saved answers match your search."


def _save_message(message):
    """Save an answered message to the collection."""
    message_id = message.get("id")
    if not message_id:
        return
    chunks = message.get("chunks") or []
    if not isinstance(chunks, list):
        chunks = []
    user_data.save_answer(
        message_id=message_id,
        question=message.get("question") or "",
        answer=strip_citation_markers(message.get("content") or "", chunks),
        status=message.get("status"),
        evidence_source=message.get("evidence_source"),
        sources=chunks,
    )


@st.dialog("Saved to your collection", width="small")
def _show_saved_confirmation():
    with st.container(key="save_success"):
        st.markdown(
            "<div class='save-success-icon' aria-hidden='true'>"
            "<svg width='30' height='36' viewBox='0 0 24 28' fill='none' xmlns='http://www.w3.org/2000/svg'>"
            "<path d='M5 3.5A2.5 2.5 0 0 1 7.5 1h9A2.5 2.5 0 0 1 19 3.5V26l-7-4.5L5 26V3.5Z' fill='#9E2435'/>"
            "</svg></div>", unsafe_allow_html=True,
        )
        st.markdown("### Ready whenever you need it")
        st.write("Your answer and its sources are saved in My Collection.")
        if st.button("View my collection", key="view_saved_collection", type="primary", use_container_width=True):
            st.session_state.view = "Collection"
            st.rerun()
        if st.button("Continue chatting", key="continue_after_save", use_container_width=True):
            st.rerun()


def render_save_button(message):
    """Show Save / Saved for an answered assistant message."""
    if message.get("role") != "assistant" or message.get("status") != "answered":
        return
    message_id = message.get("id")
    if not message_id:
        return

    saved_id = user_data.is_saved(message_id)
    if st.button(
        "Saved" if saved_id else "Save",
        key=f"save_{message_id}",
        disabled=bool(saved_id),
    ):
        _save_message(message)
        _show_saved_confirmation()


def _source_title(chunk):
    section = chunk.get("section") or "Source"
    return (
        f"{section} · printed p. {chunk.get('printed_page', '?')} "
        f"/ PDF p. {chunk.get('pdf_page', '?')}"
    )


def collection_to_markdown(items):
    """Render saved answers as a readable Markdown file.

    Deterministic: only item fields are used, never the current time.
    """
    items = list(items or [])
    lines = [
        "# My Collection — PolyU Academic Regulations Assistant",
        "",
        f"Handbook edition: {EDITION}",
        f"Saved answers: {len(items)}",
        "",
    ]
    if not items:
        lines += ["No saved answers yet.", ""]
        return "\n".join(lines)

    lines += [f"> {BANNER}", ""]

    for index, item in enumerate(items, start=1):
        question = (item.get("question") or "").strip() or "(no question)"
        lines += ["---", "", f"## {index}. {question}", ""]
        lines.append(f"- Saved: {item.get('created_at') or ''}")
        if item.get("status"):
            lines.append(f"- Status: {item['status']}")
        sources = item.get("sources") or []
        lines.append(f"- Sources: {len(sources)}")
        lines += ["", "**Answer**", "", (item.get("answer") or "").strip(), ""]

        note = (item.get("note") or "").strip()
        lines += ["**Note**", "", note or "(none)", ""]

        if sources:
            lines += ["**Sources**", ""]
            for chunk in sources:
                if not isinstance(chunk, dict):
                    continue
                lines += [f"### {_source_title(chunk)}", ""]
                for passage_line in (chunk.get("text") or "").splitlines() or [""]:
                    lines.append(f"> {passage_line}" if passage_line else ">")
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _remove_saved(saved_id):
    user_data.remove_saved(saved_id)


def _render_item(item):
    saved_id = item["id"]
    saved_at = item.get("created_at") or ""
    question = item.get("question") or "(no question)"
    with st.container(key=f"collection_item_{saved_id}"):
        details, actions = st.columns([10, 1], vertical_alignment="top")
        with details:
            with st.expander(f"{question}  ·  Saved {saved_at}"):
                st.caption(f"Handbook {EDITION}")

                answer = (item.get("answer") or "").strip()
                if answer:
                    st.markdown(answer)

                sources = item.get("sources") or []
                if sources:
                    render_source_popovers(sources)

                note = st.text_area(
                    "Note",
                    value=item.get("note") or "",
                    key=f"note_{saved_id}",
                    placeholder="Add a note for yourself",
                )
                if note != (item.get("note") or ""):
                    user_data.update_note(saved_id, note)
                    item = {**item, "note": note}
                    st.toast("Note updated")

        with actions:
            with st.popover(f"Options for {question}", key=f"saved_menu_{saved_id}"):
                st.download_button(
                    "Download as Markdown",
                    data=collection_to_markdown([item]),
                    file_name=f"saved-answer-{saved_id}.md",
                    mime="text/markdown",
                    key=f"download_saved_{saved_id}",
                    use_container_width=True,
                )
                st.button(
                    "Remove",
                    key=f"remove_{saved_id}",
                    on_click=_remove_saved,
                    args=(saved_id,),
                    use_container_width=True,
                )


def render_collection_view():
    """Full Collection view: search, download, saved items, notes and removal."""
    st.title("My Collection")
    st.caption(BANNER)

    query = st.text_input(
        "Search saved answers",
        key="collection_search",
        placeholder="Search question, answer or note",
    )
    items = user_data.list_saved(search=query)

    if not items:
        if query:
            st.info(NO_MATCH)
        else:
            st.info(EMPTY_STATE)
        return

    with st.container(key="collection_cards"):
        for item in items:
            _render_item(item)

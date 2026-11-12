"""Display helpers for citation stripping and source passages."""

import re

import streamlit as st


def strip_citation_markers(content, chunks):
    """Hide cited passage IDs from display without changing conversation history."""
    ids = {chunk.get("chunk_id") for chunk in chunks
           if isinstance(chunk, dict) and isinstance(chunk.get("chunk_id"), str)}

    def replace(match):
        return "" if match.group(1) in ids else match.group(0)

    return re.sub(r"[ \t]*\[([^\[\]\n]+)\]", replace, content)


def render_source_popovers(chunks):
    for chunk in chunks:
        title = (f"{chunk.get('section', 'Source')} · "
                 f"printed p. {chunk.get('printed_page', '?')} / PDF p. {chunk.get('pdf_page', '?')}")
        with st.popover(title, width="stretch"):
            with st.container(height=300, border=False):
                st.text(chunk.get("text", ""))

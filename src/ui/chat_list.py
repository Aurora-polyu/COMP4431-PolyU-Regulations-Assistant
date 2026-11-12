"""Sidebar chat history and per-turn persistence."""

import streamlit as st

from src import user_data

TITLE_LENGTH = 60
LIST_LIMIT = 15


def persist_turn(user_message, assistant_message):
    if st.session_state.get("temporary"):
        return None
    conversation_id = st.session_state.get("chat_id")
    if conversation_id is None:
        title = " ".join((user_message.get("content") or "").split())[:TITLE_LENGTH]
        conversation_id = user_data.create_conversation(title or "New chat")
        st.session_state.chat_id = conversation_id
    user_data.append_message(conversation_id, user_message)
    user_data.append_message(conversation_id, assistant_message)
    return conversation_id


def _open_conversation(conversation_id):
    messages = user_data.load_conversation(conversation_id)
    st.session_state.messages = messages
    st.session_state.chat_id = conversation_id
    st.session_state.temporary = False
    st.session_state.view = "Chat"
    for message in messages:
        message_id = message.get("id")
        if message.get("role") == "assistant" and message_id:
            st.session_state[f"rate_{message_id}"] = user_data.get_rating(message_id)


def _reset_chat():
    for message in st.session_state.get("messages", []):
        message_id = message.get("id")
        if message_id:
            st.session_state.pop(f"rate_{message_id}", None)
    st.session_state.messages = []
    st.session_state.chat_id = None
    st.session_state.temporary = False


def render_chat_list():
    conversations = user_data.list_conversations(
        limit=LIST_LIMIT, search=st.session_state.get("search", "") or ""
    )
    current_id = st.session_state.get("chat_id")
    for conversation in conversations:
        conversation_id = conversation["id"]
        title = conversation["title"]
        active = conversation_id == current_id
        with st.container(key=f"chat_row_{conversation_id}"):
            open_column, menu_column = st.columns([5, 1], vertical_alignment="center")
            with open_column:
                if st.button(
                    title,
                    key=f"open_chat_{conversation_id}",
                    type="primary" if active else "secondary",
                    use_container_width=True,
                ):
                    _open_conversation(conversation_id)
                    st.rerun()
            with menu_column:
                with st.popover("…", key=f"chat_menu_{conversation_id}"):
                    new_title = st.text_input(
                        "New title", value=title, key=f"rename_input_{conversation_id}"
                    )
                    if st.button("Rename", key=f"rename_chat_{conversation_id}", use_container_width=True):
                        renamed = new_title.strip()
                        if renamed:
                            user_data.rename_conversation(conversation_id, renamed)
                        st.rerun()
                    if st.button("Delete", key=f"delete_chat_{conversation_id}", use_container_width=True):
                        user_data.delete_conversation(conversation_id)
                        if active:
                            _reset_chat()
                        st.rerun()

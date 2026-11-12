# Architecture

The Streamlit interface in `app.py` offers chat history, suggested questions, saved answers, feedback, and source passages. Normal chats and user actions are stored in `data/user_data.sqlite` by `src/user_data.py`; each chat turn is committed as one transaction. Temporary chats remain in session memory, with save and feedback actions unavailable. The Settings control clears the local tables.

1. `src/conversation.py` uses recent history to form a standalone query for follow-ups.
2. `src/retriever.py` combines Chroma vector search with BM25 using reciprocal rank fusion. The index manifest ties the index to its chunk file and embedding model revision.
3. `src/llm_client.py` sends the question, recent history, and retrieved passages to the configured provider. The conversation service checks the structured response and validates citation IDs against the retrieved set.
4. The interface displays cited passages, clarification requests, insufficient-evidence responses, or safe error messages. Fictional evidence is labelled as development data.
5. Collection and feedback hooks use the local database. `scripts/export_feedback.py` exports feedback for review. The local MCP server exposes handbook search and section lookup; see [MCP setup](mcp.md).

Citation checks do not prove that each claim is supported or that retrieval is complete. Verify answers against the handbook. See [Data and indexing](data-and-indexing.md) for the preparation pipeline.

# Architecture

The assistant answers questions in English using the 2026/27 Student Handbook for Taught Programmes. Its Streamlit interface is in `app.py`; it keeps conversation history in the session and shows cited passages with both printed and PDF page numbers.

1. `src/conversation.py` uses recent history to form a standalone retrieval query when needed, then calls the handbook retriever.
2. `src/retriever.py` combines vector search over a Chroma index with BM25 keyword ranking using reciprocal rank fusion. The index manifest ties the index to the chunk file and embedding model revision.
3. The conversation service sends retrieved passages and the question to the model provider through `src/llm_client.py`. It checks the structured response and validates cited IDs against the retrieved passages using `src/citations.py`.
4. The interface displays the answer and valid cited passages, asks for clarification, reports insufficient evidence, or gives a safe error message. Fictional evidence identified by its chunk ID remains visibly labelled as development data.

The checks do not prove that every claim is supported or that extraction and retrieval are complete. Users must verify answers against the handbook. The data preparation workflow is described in [Data and indexing](data-and-indexing.md).

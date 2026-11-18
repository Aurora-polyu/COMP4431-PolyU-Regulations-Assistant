# PolyU Academic Regulations Assistant

A retrieval-augmented generation (RAG) chatbot that answers questions about PolyU academic regulations, built for the COMP4431 group project. It searches the [2026/27 Student Handbook for Taught Programmes](https://www.polyu.edu.hk/ar/docdrive/polyu-students/student-handbook/Student_Handbook_2026-27_English.pdf) with hybrid retrieval (embeddings + BM25) and answers with cited passages and printed page numbers, so every claim can be checked against the source.

**This is an unofficial student project and is not affiliated with or endorsed by PolyU.** Answers may contain errors or omit important conditions, even when they include citations. Check the official handbook and consult the responsible PolyU office before making decisions.

## Local setup

You need Python 3.12 and an API key for a compatible chat-completions provider.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your API key as `MODEL_API_KEY` in `.env`. The default model is `deepseek-flash`. To use a compatible provider, set `MODEL_BASE_URL` to its API base URL and `MODEL_NAME` to its model name; the app uses the provider's `/chat/completions` endpoint.

Build the search index from the included handbook passages, then start the app:

```sh
python scripts/build_index.py --chunks data/chunks.jsonl --index-dir "$PWD/handbook-index"
export RETRIEVAL_INDEX_DIR="$PWD/handbook-index"
streamlit run app.py
```

The first index build downloads the `BAAI/bge-small-en-v1.5` embedding model. Rebuild the index if you move or change `data/chunks.jsonl`. Set `RETRIEVAL_INDEX_DIR` in your shell each time you start the app.

Choose a suggested question or ask your own, then open the sources to read the supporting passages. Use **New chat** to start another conversation. Chats are saved automatically in `data/user_data.sqlite`; you can search, reopen, rename, and delete them. Save answered responses to Collection, where you can search them, add notes, and export them. Ratings and reports are stored locally for review.

Questions, recent conversation history, and retrieved passages are sent to the configured model provider. In the sidebar, choose **Delete all my data**, then **Confirm delete**, to clear chats, saved answers, and feedback from the local database.

Export locally stored feedback for review:

```sh
python scripts/export_feedback.py --out feedback.csv
```

The export includes questions, answers, and supporting chunk IDs. For local MCP access, see [MCP setup](docs/mcp.md). Check important answers against the official handbook or with the responsible PolyU office.

## Checks and troubleshooting

To run the tests, place the handbook PDF at `data/handbook.pdf` and run:

```sh
python -m pytest -q -rs
```

Tests that require the PDF may be skipped if it is missing. If the app cannot find the index, check `RETRIEVAL_INDEX_DIR` and rebuild the index if necessary. If answers fail, check your API key and network connection.

More details: [Architecture](docs/architecture.md), [Data and indexing](docs/data-and-indexing.md), [Testing](docs/testing.md), and [Roadmap](docs/roadmap.md).

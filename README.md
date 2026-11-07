# PolyU Academic Regulations Assistant

A COMP4431 project that answers questions about PolyU's academic regulations using the [2026/27 Student Handbook for Taught Programmes](https://www.polyu.edu.hk/ar/docdrive/polyu-students/student-handbook/Student_Handbook_2026-27_English.pdf). Answers include source passages and page numbers for reference.

**This is an unofficial student project.** Answers may contain errors or omit important conditions, even when they include citations. Check the official handbook and consult the responsible PolyU office before making decisions.

## Local setup

You need Python 3.12 and an API key for DeepSeek or a compatible chat-completions provider.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your API key as `DEEPSEEK_API_KEY` in `.env`. The default provider is DeepSeek and the default model is `deepseek-flash`. To use a compatible provider, set `DEEPSEEK_BASE_URL` to its API base URL and `DEEPSEEK_MODEL` to its model name; the app uses the provider's `/chat/completions` endpoint.

Build the search index from the included handbook passages, then start the app:

```sh
python scripts/build_index.py --chunks data/chunks.jsonl --index-dir "$PWD/handbook-index"
export RETRIEVAL_INDEX_DIR="$PWD/handbook-index"
streamlit run app.py
```

The first index build downloads the `BAAI/bge-small-en-v1.5` embedding model. Rebuild the index if you move or change `data/chunks.jsonl`. Set `RETRIEVAL_INDEX_DIR` in your shell each time you start the app.

Ask a question and expand its sources to see the supporting passages and page numbers. Use **New conversation** to start over. Check important answers against the official handbook or with the responsible PolyU office.

## Checks and troubleshooting

To run the tests, place the handbook PDF at `data/handbook.pdf` and run:

```sh
python -m pytest -q -rs
```

Tests that require the PDF may be skipped if it is missing. If the app cannot find the index, check `RETRIEVAL_INDEX_DIR` and rebuild the index if necessary. If answers fail, check your API key and network connection.

More details: [Architecture](docs/architecture.md), [Data and indexing](docs/data-and-indexing.md), and [Testing](docs/testing.md).

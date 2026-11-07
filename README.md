# PolyU Academic Regulations Assistant

A COMP4431 group project to build a local chatbot that helps students understand academic regulations using the 2026/27 Student Handbook for Taught Programmes.

## Project structure

- `data/` — handbook and processed data
- `scripts/` — preprocessing and setup scripts
- `src/` — application, retrieval, and conversation code
- `tests/` — tests and evaluation materials
- `presentation/` — presentation and demo materials
- `PROJECT_IMPLEMENTATION_PLAN.md` — project scope, architecture, and team responsibilities

The project is at the initial structure stage; implementation and setup instructions will be added as the team develops it. Confirm permission to share the handbook before adding it to the repository.

## Stage 1 retrieval mock

`data/sample_chunks.json` contains **fictional examples**, not handbook content or academic regulations. The mock returns these chunks in their fixture order for any nonblank query; it does not perform search or rank relevance. Use it to develop the answer service until the real retriever replaces it:

```python
from src.mock_retriever import retrieve

chunks = retrieve("example question", top_k=2)
for chunk in chunks:
    print(chunk["section"], chunk["printed_page"], chunk["pdf_page"], chunk["text"])
```

A blank query returns an empty list, and a non-positive `top_k` raises `ValueError`. Run `python -m unittest discover -s tests` to check the fixture and interface. See [the Stage 1 protocol](docs/member2_stage1_protocol.md) for the contract and handoff steps.

# PolyU Academic Regulations Assistant — Project Design & Implementation Plan

**Course:** COMP4431 · **Project:** PolyU Academic Regulations Assistant  
**Planning status:** Design decisions agreed; implementation pending.  
**Development:** Four technical contributors working in parallel; presentation and recorded demo are shared.  
**Workflow:** Task/dependency based, **no internal date-based schedule**.

## 1. Purpose and scope

Build a lightweight, English-only, local web chatbot that helps PolyU students find and understand general academic regulations, apply relevant conditions to student scenarios, and explore follow-up questions.

- **Sole factual source:** *Student Handbook for Taught Programmes 2026/27* (the supplied 137-page PDF).
- **Coverage:** All academic regulations **contained in that handbook**, not every programme-specific regulation in existence.
- **Answer policy:** Strictly evidence-grounded. Give general conditional answers when possible; ask clarifying questions only when essential. Do not invent unsupported rules or eligibility determinations.
- **Known boundary:** The handbook refers some specific requirements to separate Programme Requirement Documents; these are *not* additional knowledge sources for this project.
- **User language:** English only. No university login, live student-record integration, external web retrieval, or persistent user database.

## 2. Finalized lightweight architecture

```text
2026/27 handbook PDF
     |
     v
PyMuPDF text extraction -> section/page-aware chunks
     |                     (one-time local preprocessing)
     v
Local embedding model + ChromaDB vector index
     |                       
     +---- BM25 keyword index
                 \
Student message -> follow-up-aware retrieval query -> vector search + BM25
                                             -> RRF fusion -> evidence chunks
                                                              |
Conversation history -----------------------------------------> DeepSeek V4 Pro
                                                              |
                                              evidence-based answer + cited chunk IDs
                                                              |
                                     backend validates citation IDs and formats sources
                                                              |
                           Streamlit chat + expandable full-chunk source evidence
```

### Technical stack

| Function | Technology | Notes |
|---|---|---|
| Local web interface | Streamlit | `st.chat_input`, `st.chat_message`, `st.expander`, session state |
| Backend | Python | Keep orchestration simple; no dedicated web server needed |
| PDF text extraction | PyMuPDF | Use selectable text; check tables and numerical requirements manually |
| Embeddings | Local Sentence Transformers | Candidate: `BAAI/bge-small-en-v1.5`; confirm with a quick retrieval benchmark before freezing |
| Vector store | ChromaDB | Store chunk text as documents; metadata separately |
| Keyword retrieval | BM25 | English tokenization; preserve form IDs such as AR160 |
| Fusion | Reciprocal Rank Fusion (RRF) | Merge vector and BM25 rankings; deduplicate by `chunk_id` |
| Answer generation | DeepSeek V4 Pro API | Confirm available API model identifier and endpoint in the team's account; configure with environment variables |
| Secrets | `.env` per developer | Never commit keys or rotate keys in code; shared account, distinct individual keys if available |
| Factual data | The supplied handbook only | No network or general LLM knowledge as a factual authority |

**Preprocessing:** Run only when the handbook or chunking/embedding parameters change, not on each query. Preserve the exact source PDF version and page mapping. Because handbook pagination differs from PDF pagination, track both. Prefer chunks that do not span printed pages so each citation resolves to one page. Consider 400–700 token chunks as a starting point, not a rigid target.

## 3. Interfaces to freeze before parallel work

### Canonical document chunk

```json
{
  "chunk_id": "sec5_C_001",
  "section": "5.C Retaking of Failed Subjects",
  "printed_page": 33,
  "pdf_page": 45,
  "text": "..."
}
```

- `pdf_page` is **1-based**, suitable for human-friendly PDF page navigation if later added.
- In ChromaDB, store `text` in the document field and the other fields as metadata; do not duplicate the passage inside metadata.
- Retrieval returns the same fields plus optional `rank` or `score` (a retrieval score, **not** a probability of correctness).

### Retrieval service (Member 2 exposes)

```python
retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]
```

Returns ranked, deduplicated passages with source metadata. Provide a simple mock retrieval response for Member 3's early development.

### Conversation/answer service (Member 3 exposes)

```python
answer_question(question: str, history: list[dict]) -> ChatResponse
```

Suggested `ChatResponse` fields:

```json
{
  "answer": "...",
  "citation_chunk_ids": ["sec5_C_001"],
  "cited_chunks": [{"chunk_id": "sec5_C_001", "section": "5.C Retaking of Failed Subjects", "printed_page": 33, "pdf_page": 45, "text": "..."}],
  "clarification_question": null,
  "status": "answered"
}
```

Supported statuses: `answered`, `needs_clarification`, `insufficient_evidence`, `error`. The service uses the retrieval interface internally and returns the validated cited chunks for display. Backend citation checks ensure referenced IDs belong to retrieved chunks. **A valid ID alone does not prove that a passage supports a claim**; benchmark this separately.

### UI (Member 4 consumes)

Render the answer, section, printed page, and an `st.expander` with **the complete text of each cited retrieved chunk**. UI code does not perform retrieval or independently call the LLM. Use mock `ChatResponse` objects before integration. Provide a New Conversation control (clears the current session).

## 4. Parallel responsibilities

| Owner | Primary ownership | Definition of done |
|---|---|---|
| **Member 1 — Handbook Processing & Data** | PDF extraction, section/page mapping, chunking, and manual checks of tables and numerical rules | Reproducible preprocessing produces validated chunks with stable IDs and correct metadata |
| **Member 2 — Search & Retrieval** | Local embeddings, ChromaDB, BM25, RRF, index build, and `retrieve()` | Reproducible index build; ranked, deduplicated retrieval passes smoke tests |
| **Member 3 — LLM & Conversation** | DeepSeek client, prompt constraints, follow-up context, selective clarification, answer composition, citation validation, and `answer_question()` | Works with mock retrieved passages and handles missing evidence and follow-ups without fabricating rules |
| **Member 4 — UI & Integration** | Streamlit interface, expandable citations, session handling, end-to-end wiring, and error messages | Clean local chat experience with working full-source expanders and New Conversation |

**Shared responsibility:** All four members create and manually verify the evaluation questions, test the integrated system, and fix failures in their own modules. Share presentation, slides, recorded demo, and rehearsal work; designate one member to coordinate the final materials.

**Parallelism rule:** Agree on the data contracts and stub each interface first. Member 1 processes the PDF, Member 2 uses sample chunks, Member 3 uses mock retrieval, and Member 4 uses mock answer responses. Integration should require replacing mocks, not rewriting modules.

## 5. Evaluation

Prepare **30 manually checked questions** based only on the handbook:

| Type | Count |
|---|---:|
| Direct factual questions | 8 |
| Conditional student scenarios | 8 |
| Multi-section questions | 5 |
| Conversational follow-ups | 4 |
| Unsupported or ambiguous questions | 5 |
| **Total** | **30** |

Track: Retrieval Recall@5, answer correctness, citation claim support, unsupported-answer handling, and end-to-end latency. Proposed targets (not claimed results): ≥90% Recall@5; ≥90% answer correctness; aim for 100% grounded citations and appropriate abstention. Inspect errors manually before drawing conclusions.

Select **2–3 final live demo scenarios after testing**: straightforward retrieval, conditional scenario, and follow-up or insufficient-evidence handling.

## 6. GitHub collaboration protocol

**Repository owner:** Create the GitHub repository and invite the other three members.

Recommended repository structure:

```text
COMP4431-PolyU-Assistant/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── handbook.pdf                 # only if repository-sharing is permitted
├── scripts/
│   └── build_index.py
├── src/
│   ├── pdf_processor.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── llm_client.py
│   ├── conversation.py
│   └── citations.py
├── tests/
│   ├── benchmark.json
│   ├── test_retrieval.py
│   └── test_end_to_end.py
└── presentation/
```

1. Keep `main` stable; use `feature/data`, `feature/retrieval`, `feature/llm`, and `feature/ui` branches.
2. Commit agreed interfaces and minimal stubs early so everyone can import them.
3. Open pull requests into `main` for module completion; have at least one teammate review interfaces and test results.
4. Keep `.env`, real API keys, virtual environments, cache files, local ChromaDB indexes, and generated artifacts out of Git. Supply `.env.example` and a reproducible `build_index.py` instead.
5. Pin dependencies in `requirements.txt` after compatibility testing. Document `python scripts/build_index.py` and `streamlit run app.py` in `README.md`.
6. Verify the right to redistribute the handbook PDF in the repository; if uncertain, use a private repo and/or document where each team member obtains the authorized source.

## 7. Acceptance checklist

- [ ] The exact 2026/27 handbook is the only regulatory knowledge source.
- [ ] Preprocessing is reproducible and retains correct printed/PDF page metadata.
- [ ] Hybrid retrieval finds both paraphrases and exact regulation/form IDs.
- [ ] DeepSeek answers strictly from retrieved evidence and uses selective clarification.
- [ ] The UI displays full retrieved chunks in expandable citation sections.
- [ ] API keys are never stored in tracked files.
- [ ] All 30 benchmark questions are run and results are recorded honestly.
- [ ] Integrated chatbot runs locally and handles API/retrieval failures gracefully.
- [ ] Slides, recorded demo, source code, and submission package are ready under course requirements.

## 8. Pending technical checks (not scope changes)

- Confirm the DeepSeek account can access the intended V4 Pro model and record the **exact API model ID**.
- Pick the final local English embedding model after a small retrieval smoke test.
- Verify table extraction, pagination, source version, and exact numeric rules against the PDF.
- Confirm GitHub repository access and handbook distribution permissions.

# Member 2 Stage 3: Retrieval Verification and Evaluation Preparation

## Goal and current status

Verify the implemented retriever with the real embedding model, prepare handbook-based evaluation questions, and document the retrieval branch for review. These tasks can proceed while Members 1 and 3 confirm the existing contract. The handoff to both members has already been done; their confirmations must not be assumed.

The handbook PDF is available locally. The current sample chunks are fictional, and the current candidate model is `BAAI/bge-small-en-v1.5`. Neither a synthetic smoke test nor the existing unit tests establishes handbook retrieval quality.

## 1. Real-model smoke test

Use the Python 3.12 environment and pinned dependencies described in the [README](../README.md). From the repository root, build an index from the synthetic fixture and run the tests:

```sh
python scripts/build_index.py
python -m unittest discover -s tests
```

The build may download the model. It creates a new generation in the ignored local `chroma_db/` directory; it does not use handbook data. Run the following in the same environment:

```python
from src.retriever import retrieve

for question in ("How can a student take a break from their studies?", "ZX101"):
    print("\nQuery:", question)
    for rank, chunk in enumerate(retrieve(question, top_k=3), 1):
        print(rank, chunk["chunk_id"], chunk["section"])
```

For each query, record the returned IDs and order, whether `sample_leave_001` appears and its rank, and any error or unexpected result. The paraphrase may also reasonably retrieve `sample_leave_002`. Record the date, model and revision from the index manifest, test outcome, and any setup limitations. These are qualitative smoke checks on only three fictional passages, not a benchmark or a basis for claims about real regulations.

## 2. Prepare handbook evaluation questions

Draft Member 2's contribution to the shared set of 30 questions, using the local 2026/27 handbook as the only factual source. The team allocation remains 8 direct factual, 8 conditional scenarios, 5 multi-section, 4 conversational follow-ups, and 5 unsupported or ambiguous questions. Coordinate the final selection and manual checking with the team; Member 2 does not need to create all 30 alone.

- Include paraphrases and exact identifiers where the handbook contains them. For each answerable question, manually record the expected evidence, section, printed page and 1-based PDF page; check any numerical conditions and tables against the PDF.
- For multi-section questions, list each distinct required evidence item. For follow-ups, record the preceding conversation and the intended context-aware retrieval query. For unsupported or ambiguous cases, record why a complete answer is unavailable or what clarification is needed; do not invent a supporting passage.
- Prepare a results table with question ID and type, question and context, expected evidence and pages, eventual expected chunk IDs, retrieved top-five IDs and ranks, per-question recall, latency and notes. Keep question and answer material local until handbook-sharing permission is confirmed.
- Once chunks are available, map each required evidence item to validated chunk IDs. Agree and record a scoring rule with the team before reporting: for example, per-question Recall@5 can be the fraction of required evidence items represented by at least one acceptable retrieved chunk, averaged across answerable questions. A single retrieved chunk can satisfy multiple evidence items when it supports each one; do not require a different chunk for each item. Identify acceptable chunks for each item in advance, including alternatives and any chunk that supports multiple items. Report unsupported cases separately rather than assigning them a fabricated recall denominator. If the team chooses another definition, state it explicitly.

## 3. Record findings and prepare branch review

Summarize the test and smoke-test outcomes, commands, model revision, limitations, and unresolved issues in a reviewable record. Review the `feature/retrieval` changes and documentation for consistency, and confirm that secrets, the handbook, generated data, local indexes and environments are not included in Git. The [project plan](../PROJECT_IMPLEMENTATION_PLAN.md) calls for a pull request into `main` and at least one teammate review of interfaces and test results. Include any pending teammate confirmations in the review notes; do not represent them as complete.

## After confirmation and validated data

These steps depend on work from the other members and are outside the independent preparation above:

1. Once Member 1 supplies validated handbook chunks, verify the contract and page mapping, build a **separate** local index, and map the prepared evidence to stable chunk IDs. Record the source and model revisions used.
2. Run the agreed handbook retrieval evaluation, record Recall@5 and latency, inspect misses, and address retrieval issues. Compare models if needed before selecting the final embedding model. The project's proposed targets are goals, not results.
3. Once Member 3 is ready, integrate the real `retrieve()` interface and check normal retrieval, missing or stale index errors, and insufficient-evidence handling together. Answer correctness, citation support, and end-to-end behavior require integrated evaluation by the team.

## Stage 3 completion checklist

- [ ] Real-model synthetic smoke test and unit tests run; results and limitations recorded.
- [ ] Member 2's handbook questions and expected evidence prepared and manually checked; a results template and proposed scoring rule are ready for team agreement.
- [ ] Branch and documentation reviewed; findings and pending confirmations available for teammate review.
- [ ] Handoff to Members 1 and 3 already completed; confirmations tracked separately.

Stage 3 preparation can be completed without teammate confirmations or real handbook chunks. The handbook benchmark, final model choice, and integration remain subsequent dependent work.

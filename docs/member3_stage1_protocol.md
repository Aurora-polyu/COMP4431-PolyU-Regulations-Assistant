# Member 3 Stage 1: Answer-Service Contract and Retrieval Review

## Goal and scope

Freeze the contract for the conversation and answer service so that Member 2, Member 4 and the evaluation work can all develop against it, and return a review of the Member 2 Stage 1 retrieval contract. This stage does not call the language model yet; the service is developed against `src/mock_retriever.py`, whose chunks are fictional and must never be presented as handbook evidence.

Member 3 owns the DeepSeek client, prompt constraints, follow-up context handling, selective clarification, answer composition, citation validation and `answer_question()`.

## Confirmation of the Member 2 Stage 1 contract

The Stage 1 contract is accepted as published. No change to the call signature is requested.

| Item | Confirmation |
|---|---|
| `retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]` | Accepted. The answer service calls it with a nonblank query and a positive `top_k`. |
| `chunk_id` | Accepted. Used as the key for citation validation and for matching cited chunks to retrieved chunks. |
| `section` | Accepted. Displayed to the user next to each citation. |
| `printed_page` | Accepted. Displayed as the human-readable page number. |
| `pdf_page` | Accepted. Kept for source lookup during development and possibly the presentation. |
| `text` | Accepted. Required in full: the UI expands each cited chunk and shows this complete passage. |
| Blank query returns `[]` | Accepted. The answer service never sends a blank query, but treats `[]` as "no passage retrieved", not as an error. |
| `top_k <= 0` raises `ValueError` | Accepted. The service always passes `top_k=5`. |
| Fixed fixture order, no relevance ranking | Accepted. The answer service does not rely on rank order and never treats order or score as evidence strength. |
| Fictional fixture content | Accepted with a safeguard, see issue 3. |

## Integration issues and proposed changes

These are requests to Member 2. Member 2's files have not been modified.

1. **Shared, lightweight contract types.** `RetrievedChunk` is currently defined in `src/mock_retriever.py` and imported by `src/retriever.py`, and `RetrievalError` is defined only in `src/retriever.py`. The answer service needs the chunk type and the error type but must not import `src.retriever` to get them, because that import pulls in `chromadb` and `sentence-transformers` and would make the answer service untestable without the full retrieval environment. Proposal: add a small `src/contracts.py` holding `RetrievedChunk` and `RetrievalError`, and import both from there in `src/mock_retriever.py` and `src/retriever.py`. The dependency direction then reads real and mock to contracts, instead of real to mock. The call signature does not change.

2. **Named error semantics in the Stage 1 contract.** Stage 2 states that a missing, stale, unreadable or incompatible index produces "an actionable retrieval error" but does not name the type; Stage 1 names no exception at all. The answer service must map this failure to `status: "error"` and keep it distinct from `status: "insufficient_evidence"`. Proposal: document in the Stage 1 contract that (a) environment, index and model failures raise `RetrievalError`, (b) invalid arguments raise `ValueError`, and (c) an empty list for a nonblank query means no passage was retrieved and is not an error.

3. **Fixture output must not be mistakeable for handbook evidence.** The mock returns chunks shaped exactly like real ones. A UI wired to the mock during a rehearsal or a live demo would answer with fictional "regulations" without any visible warning. Proposal: the answer service detects fixture chunks (`chunk_id` beginning `sample_`, or every chunk originating from `src.mock_retriever`) and sets an additive response field `evidence_source: "fixture"` (otherwise `"handbook"`). The answer service will also prefix any such answer with a development warning. No change to Member 2's code is needed; this is handled in the answer service. Member 4 may use the field for a banner but is not required to.

4. **Warm-up and latency.** The live demo is five minutes including the demo. The real retriever loads the embedding model and index on the first call. Please record cold-start and warm-query latency in the Stage 3 findings, and confirm that a single warm-up call at application start is sufficient. If the first real answer takes noticeably longer than later ones, the demo script should warm the system before the presentation starts.

5. **Page mapping must be checked with a real handbook page.** In the supplied handbook the printed page number and the PDF page number differ (PDF page 11 carries printed page 2). Citations show `printed_page`, so a systematic offset would be visible to the audience. Please confirm with Member 1 that both fields are populated from the handbook and that `printed_page` is the number printed on the page.

6. **Top-k behaviour for multi-section questions.** The answer service calls `retrieve` with `top_k=5` and, for multi-section questions, may issue two complementary queries rather than one large `top_k`. Please confirm that repeated calls with different queries are acceptable and that warm latency per call is low enough to do this.

Not requested: a `score` or `rank` field. The answer service does not need retrieval scores and will not use them as evidence strength.

## Answer-service contract

```python
answer_question(question: str, history: list[dict]) -> ChatResponse
```

`history` is a list of previous turns, each `{"role": "user" | "assistant", "content": str}`. The service uses only the last six turns and does not require an external session store.

```json
{
  "answer": "string",
  "citation_chunk_ids": ["sec5_C_001"],
  "cited_chunks": [
    {
      "chunk_id": "sec5_C_001",
      "section": "5.C Retaking of Failed Subjects",
      "printed_page": 33,
      "pdf_page": 45,
      "text": "complete passage text"
    }
  ],
  "clarification_question": null,
  "status": "answered",
  "evidence_source": "handbook"
}
```

| Field | Rule |
|---|---|
| `answer` | Generated text, evidence-grounded. Empty only when `status` is `error` or `needs_clarification` is null-and-no-answer is impossible; use a short unable-to-answer sentence instead. |
| `citation_chunk_ids` | The IDs the answer relies on. Every ID must be present in the retrieved set. |
| `cited_chunks` | The full retrieved chunk objects for those IDs, with complete `text`, in the same order as `citation_chunk_ids`. Never truncated, never reconstructed. |
| `clarification_question` | Non-null only when `status` is `needs_clarification`. At most one question, asked only when the answer genuinely depends on it. |
| `status` | One of `answered`, `needs_clarification`, `insufficient_evidence`, `error`. |
| `evidence_source` | `handbook` or `fixture`. Additive to the project plan; the UI may ignore it. |

Status rules:

- `answered`: the retrieved evidence supports a complete answer and at least one validated citation is attached.
- `needs_clarification`: the question is ambiguous in a way that changes the answer, and asking one short question is cheaper and more accurate than answering several branches.
- `insufficient_evidence`: retrieval returned nothing useful, or the retrieved passages do not support an answer. The service says so plainly and does not guess.
- `error`: retrieval or model infrastructure failed. The message names the likely cause and the recovery step; it never falls back to unsupported content.

### Citation validation

1. The model is given only the retrieved chunks, each with its `chunk_id`.
2. The model is instructed to return the IDs it used.
3. The service drops any returned ID that is not in the retrieved set.
4. If the model produces an answer but no ID survives validation, the response is converted to `insufficient_evidence`.
5. `cited_chunks` is built from the original retrieved objects, so the displayed passage is exactly what retrieval returned.

### Grounding policy (system prompt constraints)

- Answer only from the retrieved passages. No general knowledge, no inference beyond the text.
- Quote numbers, thresholds and form or subject codes exactly as they appear.
- Do not decide individual eligibility. State the rule and its conditions, and point to the responsible office where the handbook does.
- If passages conflict or are incomplete, say so instead of resolving the conflict.
- If the evidence is absent, say it is not covered by the provided handbook and suggest the Academic Registry or programme office.
- Follow-up questions are rewritten into a standalone retrieval query using the recent turns before retrieval.

## Failure handling

| Failure | Behaviour |
|---|---|
| `RetrievalError` | `status: "error"`, message names the index and suggests rebuilding or reconfiguring. |
| Empty retrieval result | `status: "insufficient_evidence"`, no model call needed. |
| Model API error | One retry with a short backoff, then `status: "error"`. |
| Missing or invalid API key | Fail at start-up with a clear message; do not silently answer without a model. |
| Malformed model output | Retry once with a stricter instruction, then `insufficient_evidence`. Never fabricate citations to satisfy the format. |

## Environment

- `DEEPSEEK_API_KEY` in a local `.env`, which is already ignored by `.gitignore`. No key is committed, quoted in chat, or written into code.
- The exact DeepSeek API model identifier is still to be confirmed against the team's account, as recorded in the project plan.
- A `.env.example` with placeholder values will be added so that setup is reproducible.

## Pending confirmations

- Member 2: issues 1 to 6 above, and confirmation that the Stage 1 contract is otherwise unchanged.
- Member 1: contract confirmation and the printed-page mapping (issue 5).
- Member 4: response shape and the optional `evidence_source` field.
- Team: exact DeepSeek model identifier and endpoint.

## Stage 1 checklist

- [x] Member 2 Stage 1 contract reviewed; call signature and fields accepted.
- [x] Integration issues and proposed changes recorded.
- [x] Answer-service contract, statuses and citation rules documented.
- [ ] Member 2 changes in `src/contracts.py` agreed.
- [ ] Team confirms the DeepSeek model identifier.
- [ ] Answer service implemented against the mock and reviewed.

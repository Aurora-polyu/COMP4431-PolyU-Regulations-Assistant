# Member 2 Stage 1: Retrieval Interface and Sample Data

## Goal and scope

Prepare a shared contract so Member 1 can produce compatible handbook chunks and Member 3 can develop the answer service independently. This stage provides synthetic data and a mock retriever; it does not build indexes or search the handbook.

## Chunk contract

Each chunk contains:

| Field | Type | Meaning |
|---|---|---|
| `chunk_id` | string | Unique, stable chunk identifier |
| `section` | string | Section identifier and title |
| `printed_page` | integer | Positive printed handbook page number |
| `pdf_page` | integer | Positive, 1-based PDF page number |
| `text` | string | Complete passage text |

Member 1 should confirm this contract and provide validated chunks with correct page mapping. The current example values are fictional and are not handbook regulations.

## Workflow and handoff

1. Review the contract above with Member 1 and coordinate any change with Member 3.
2. Use `data/sample_chunks.json` as the synthetic development fixture. It contains related fictional passages and a fictional form identifier; its order defines the mock's output order.
3. Member 3 can import `retrieve` from `src.mock_retriever`. It accepts `query: str` and `top_k: int = 5`, and returns a list of chunks matching the contract. Nonblank queries return up to `top_k` chunks in fixture order, without relevance ranking. Blank queries return an empty list; non-positive `top_k` raises `ValueError`.
4. Confirm with Member 3 that the answer service can consume the full text and both page fields. Replace the mock import with the real retriever during integration; do not use the fictional output as evidence for real answers.
5. Run `python -m unittest discover -s tests` from the project root. Stage 1 is complete after the checks pass and both teammates have confirmed the contract and handoff.

The implementation is ready for review; teammate confirmation and handoff still need to take place.

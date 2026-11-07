# Stage C answer-service verification record

**Date:** 2026-11-07 (Hong Kong)

**Reviewer:** Codex

**Decision:** The answer-service integration gate passes for the checks below, with the retrieval, coverage and UI limitations recorded here. This is not the Stage E benchmark or a guarantee that all generated claims are grounded. The current Streamlit UI still uses `src.mock_backend`; it is not an integrated handbook application and must not be presented as one. Stage D must connect and test the real service and display fixture warnings and errors for all statuses.

## Configuration and provenance

The approved PDF and chunks were rechecked: PDF SHA-256 `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464`; chunks SHA-256 `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`. The unchanged Stage B index at `/private/tmp/gp-stage-b-index.pTotFHEc` has generation `5d8469f9af98404396d5153ac7578419`, 186 chunks, the matching absolute source path and hash, and model `BAAI/bge-small-en-v1.5` at revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. This is temporary storage and may be removed by the operating system. Python 3.12.13 in the project `.venv` and DeepSeek model `deepseek-flash` were used. The API key was loaded locally; it was not recorded.

The live process set `RETRIEVAL_INDEX_DIR` before startup, cleared `RETRIEVAL_BACKEND` and `RETRIEVAL_MODEL`, and used `HF_HUB_OFFLINE=1`. The real retriever was wrapped only to record its query and exact returned records; the actual answer service and DeepSeek client were used. Retrieval configuration must be set in the process environment before startup because the retriever is selected before the client loads `.env` on the first call.

## Live checks

Top-five IDs below are ordered by rank. The complete cited records matched the returned retrieval records, including text and both page numbers. Source passages and their page mappings were checked against the PDF in Stage A/B; the specific claims below were checked against those passages. The Section 12.D clinic contact relationship is a source-layout annotation checked against the PDF, not an assumption about flattened table order.

| Case and input | Top-five retrieved IDs | Outcome and review |
|---|---|---|
| Medical Clinic telephone and room | `sec12_D_002`, `sec12_C_008`, `sec12_D_001`, `sec12_C_009`, `sec3_E_001` | `answered`; cited `sec12_D_002`, printed 101 / PDF 120. Phone 2766 5433 and Room A001 agree with the source. |
| Rules and conditions for retaking a failed subject | `sec5_C_001`, `sec5_D_001`, `sec5_B_004`, `sec6_B_001`, `sec6_E_001` | `answered`; cited `sec5_C_001`, printed 33 / PDF 45. Grades F/S/U, 21-credit limit, two-retake limit, compulsory-subject consequences, departmental qualifications, eStudent, AR160, timing and final-attempt GPA rule agree with that passage. |
| Follow-up: “How many times can I do that?” after the preceding answer | `sec5_C_001`, `sec6_B_001`, `sec5_D_001`, `sec5_B_004`, `sec5_F_001` | Rewritten query: “maximum number of retakes allowed for a failed subject”. `answered`; cited `sec5_C_001`, printed 33 / PDF 45. The two-retake limit and compulsory-subject consequence agree with the passage. |
| “How can I take a break from my studies and when must I apply?” | `sec4_M_003`, `sec4_K_001`, `sec5_G_001`, `sec4_L_001`, `sec11_D_001` | The required deferment passage was absent, as in Stage B. An initial call returned `insufficient_evidence` with uncited withdrawal details. After the first fix, a clarification misleadingly suggested withdrawing from a subject was an example of missing classes. The prompt was refined; three subsequent calls asked whether the student meant missing classes temporarily, pausing the programme, or leaving permanently, with no rule presented as an answer. `needs_clarification`; no citations. These spot checks do not prove all ambiguous wording is handled safely. |
| “What is the parking policy on Mars for PolyU students?” | `sec11_C_002`, `sec12_C_006`, `sec5_H_001`, `sec12_C_005`, `sec12_A_003` | `insufficient_evidence`, no citations. The initial model response contained unrelated parking rules; the service now returns only a standard evidence-limited response. |

The final prompt refinement affected the clarification instructions; the direct, conditional, follow-up and unsupported rows reflect the immediately preceding live run. Model output varies; a valid citation ID is not proof that each claim is supported. Stage B's natural-language deferment miss and permanent-withdrawal miss remain unresolved. Stage A's accepted table-coverage limitation remains in force.

## Changes and failure checks

- Model-declared insufficient evidence now returns a standard response about the *retrieved passages*, without exposing uncited model claims or asserting that the whole handbook lacks the answer.
- Clarification returns only the clarification question, rather than a premature rule; fixture warnings remain present. Mixed handbook/fixture passages set `evidence_source` to `fixture`. After evidence is retrieved, fixture warnings also survive model errors, malformed responses and insufficient evidence. Detection relies on the existing `sample_` chunk-ID convention; it is not a general provenance classifier.
- Missing/invalid model status and a clarification status without a question now produce `error`. Unknown citation IDs are discarded, and an answer without any valid citation is not returned as answered. Existing tests exercise malformed JSON, empty retrieval, API failure, follow-up rewrite and mixed fixtures.
- Through the real service and retriever, a missing index and a disposable manifest with a deliberately stale hash both produced `error` before the injected model was called. No active index or source was modified. API failures and malformed model responses were tested with injected doubles, not by corrupting credentials or the live service.
- The UI currently replaces backend text on insufficient-evidence and error statuses. Its handling of `evidence_source`, fixture warnings, safe errors and history is a mandatory Stage D check; no UI gate is claimed here.

## Automated verification

The focused conversation, citation, client, retrieval and contract suite passed after the service changes. The full suite, including the handbook-dependent checks, was run with `HANDBOOK_PDF` pointing to the approved PDF: **75 passed, 16 subtests passed**, with five SWIG deprecation warnings. The first full run identified an older test double that omitted the required model status; it was updated before the passing run. Temporary live-check files and indexes are not required for the service changes.

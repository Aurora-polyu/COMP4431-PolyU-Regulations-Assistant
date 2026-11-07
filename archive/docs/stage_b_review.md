# Stage B retrieval verification record

**Date:** 2026-11-07 (Hong Kong)
**Reviewer:** Codex
**Gate:** Passed for index provenance, representative contract/pagination checks and explicit error handling, with the retrieval miss below carried forward. The benchmark and retrieval quality assessment are pending team agreement and evaluation. This is not evidence of answer correctness or complete table coverage.

## Provenance and setup

- Stage A approved PDF SHA-256: `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464`; current chunk SHA-256: `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`. Both were checked immediately before building.
- Index: `/private/tmp/gp-stage-b-index.pTotFHEc` (local temporary storage; retain for Stage C, but the operating system may clear temporary files). The absolute source path in its manifest is `/Users/auroralee/Desktop/COMP4431/GP-integration/data/chunks.jsonl`; that path and its contents must remain available and unchanged.
- Manifest: format 2; 186 chunks; generation `5d8469f9af98404396d5153ac7578419`; model `BAAI/bge-small-en-v1.5`; immutable revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`; query prefix `Represent this sentence for searching relevant passages: `. Build date is recorded here, not in the manifest.
- Python 3.12.13, project `.venv`, macOS; normalized embeddings, cosine distance, BM25Plus and reciprocal rank fusion (`k=60`). The build used the cached model with `HF_HUB_OFFLINE=1`. An earlier attempt was interrupted during dependency import, before an index was published.

```sh
shasum -a 256 data/handbook.pdf data/chunks.jsonl
HF_HUB_OFFLINE=1 env -u RETRIEVAL_BACKEND -u RETRIEVAL_MODEL .venv/bin/python scripts/build_index.py --chunks data/chunks.jsonl --index-dir /tmp/gp-stage-b-index.pTotFHEc
.venv/bin/python -m pytest -q -rs tests/test_retriever.py tests/test_contracts.py
export RETRIEVAL_INDEX_DIR=/private/tmp/gp-stage-b-index.pTotFHEc
unset RETRIEVAL_BACKEND RETRIEVAL_MODEL
```

Set the environment before launching the app or answer service. A shell export in one process does not persist in another. Do not select the mock retriever or a sample index for handbook use. The retrieval and contract tests passed: **14 passed, 6 subtests passed**.

## Real-index checks

Each row lists rank, chunk ID, printed page / PDF page, and section as returned; section labels may contain source-layout annotations. The current indexed records were checked against all five fields in `data/chunks.jsonl`. For the 36 distinct returned passages, whitespace-normalized full text matched the stated PDF page's text layer and the printed number appeared on that page. The relevant source pages and table relationships had also been checked visually in Stage A. Text-layer comparison does not itself prove table semantics, relevance or answer support.

Times are seconds around `retrieve()` after importing the retriever, in a single process. The first call includes loading the local model and index; later calls are warm. These are individual spot checks, not a latency benchmark.

### A1 — 4.6675 s

What are the telephone number and room of the Medical Clinic?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec12_D_002` | 101 / 120 | 12.D University Health Service [Source-layout annotation: PDF clinic contact table: Medical Clinic: 2766 5433, Room A001; Traditional Chinese Medicine Clinic: 2766 5553, Room A125; Dental Clinic: 2330 9414, Room GH020.] |
| 2 | `sec12_C_008` | 96 / 115 | 12.C Student Affairs Office [Source-layout annotation: PDF contact layout: the counselling email address is stud.counselling@polyu.edu.hk (the source line wrap splits the address).] |
| 3 | `sec12_D_001` | 100 / 119 | 12.D University Health Service |
| 4 | `sec12_C_009` | 97 / 116 | 12.C Student Affairs Office [Source-layout annotation: PDF table layout: when days and times are grouped separately within a facility row, pair them in their displayed order. Global Student Hub: Monday to Sunday 9.00 am–11.00 pm; other general holidays closed. The Kwong On Jubilee Sports Centre row continues on PDF page 117 (printed page 98).] |
| 5 | `sec3_E_001` | 7 / 17 | 3.E Academic Registry and Various Offices |

### A2 — 0.0112 s

What are the telephone number and room of the Dental Clinic?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec12_C_008` | 96 / 115 | 12.C Student Affairs Office [Source-layout annotation: PDF contact layout: the counselling email address is stud.counselling@polyu.edu.hk (the source line wrap splits the address).] |
| 2 | `sec12_D_002` | 101 / 120 | 12.D University Health Service [Source-layout annotation: PDF clinic contact table: Medical Clinic: 2766 5433, Room A001; Traditional Chinese Medicine Clinic: 2766 5553, Room A125; Dental Clinic: 2330 9414, Room GH020.] |
| 3 | `sec12_C_009` | 97 / 116 | 12.C Student Affairs Office [Source-layout annotation: PDF table layout: when days and times are grouped separately within a facility row, pair them in their displayed order. Global Student Hub: Monday to Sunday 9.00 am–11.00 pm; other general holidays closed. The Kwong On Jubilee Sports Centre row continues on PDF page 117 (printed page 98).] |
| 4 | `sec12_D_001` | 100 / 119 | 12.D University Health Service |
| 5 | `app3_H_001` | 117 / 137 | Appendix 3.H Emergency Contact and Other Useful Telephone Numbers [Source-layout annotation: PDF emergency contact table: 24-Hour Campus Emergency Hotline: 2766 7999; Campus Control Centre: 2766 7666; Health and Safety Office: 3400 8396; University Health Service: 2766 5433.] |

### A3 — 0.0124 s

What is the 24-hour Campus Emergency Hotline, and how does it differ from the Campus Control Centre number?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `app3_H_001` | 117 / 137 | Appendix 3.H Emergency Contact and Other Useful Telephone Numbers [Source-layout annotation: PDF emergency contact table: 24-Hour Campus Emergency Hotline: 2766 7999; Campus Control Centre: 2766 7666; Health and Safety Office: 3400 8396; University Health Service: 2766 5433.] |
| 2 | `app1_B_001` | 110 / 130 | Appendix 1.B Rainstorm Warning |
| 3 | `sec12_C_003` | 91 / 110 | 12.C Student Affairs Office |
| 4 | `sec12_A_001` | 79 / 98 | 12.A Information Technology Services Office |
| 5 | `app1_B_002` | 111 / 131 | Appendix 1.B Rainstorm Warning |

### A4 — 0.0102 s

What is the deadline for applying for deferment of study using AR7?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec4_H_001` | 16 / 27 | 4.H Deferment of Study* |
| 2 | `sec4_D_002` | 14 / 25 | 4.D Normal Duration for Completion of a Programme |
| 3 | `sec4_H_002` | 17 / 28 | 4.H Deferment of Study* |
| 4 | `sec4_K_003` | 21 / 32 | 4.K Student Status |
| 5 | `sec5_A_002` | 29 / 41 | 5.A Subject Registration |

### A5 — 0.1131 s

Which form is used for a transcript of studies and which for a testimonial?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec7_B_001` | 49 / 63 | 7.B Testimonial |
| 2 | `sec7_A_001` | 49 / 63 | 7.A Transcript of Studies |
| 3 | `sec5_B_004` | 32 / 44 | 5.B Subject Exemption and Credit Transfer |
| 4 | `sec8_I_002` | 62 / 77 | 8.I Other Fees/Charges [Source-layout annotation: PDF footnote layout: 'footnote 11' is footnote 1, on gown hiring; '100/copy2' means HK$100/copy with footnote 2, not 100 per copy squared.] |
| 5 | `sec4_C_001` | 10 / 21 | 4.C Use, Access and Change of Student Data |

### P1 — 0.0109 s

How can I take a break from my studies and when must I apply?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec4_M_003` | 25 / 36 | 4.M Undergraduate Degree Programmes with Minor/Double Major/Secondary Major/Fast-track Programmes Study Options |
| 2 | `sec4_K_001` | 19 / 30 | 4.K Student Status |
| 3 | `sec5_G_001` | 35 / 47 | 5.G Withdrawal of Subjects |
| 4 | `sec4_L_001` | 21 / 32 | 4.L Withdrawal of Study* |
| 5 | `sec11_D_001` | 71 / 89 | 11.D Academic Studies |

### P2 — 0.0126 s

What happens to my study load when I am placed on academic probation?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec6_C_001` | 38 / 51 | 6.C Academic Probation |
| 2 | `sec5_A_001` | 28 / 40 | 5.A Subject Registration |
| 3 | `sec11_B_002` | 69 / 87 | 11.B Penalties for Offences |
| 4 | `sec4_K_001` | 19 / 30 | 4.K Student Status |
| 5 | `sec4_K_002` | 20 / 31 | 4.K Student Status |

### D1 — 0.0096 s

What is the maximum number of times I can retake a subject?

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec5_C_001` | 33 / 45 | 5.C Retaking of Failed Subjects |
| 2 | `sec5_A_001` | 28 / 40 | 5.A Subject Registration |
| 3 | `sec5_F_001` | 35 / 47 | 5.F Taking Additional Subjects |
| 4 | `sec4_E_001` | 14 / 25 | 4.E Maximum Period of Registration (Applicable to Students Admitted in or before 2019/20) |
| 5 | `sec5_B_003` | 31 / 43 | 5.B Subject Exemption and Credit Transfer |

### I1 — 0.0186 s

AR3 AR4

| Rank | Chunk ID | Printed / PDF | Section |
|---:|---|---|---|
| 1 | `sec4_F_001` | 14 / 25 | 4.F Leave of Absence |
| 2 | `sec7_B_001` | 49 / 63 | 7.B Testimonial |
| 3 | `sec7_A_001` | 49 / 63 | 7.A Transcript of Studies |
| 4 | `sec7_D_002` | 52 / 66 | 7.D Certification of Award & Replacement Award Parchment |
| 5 | `sec5_B_002` | 30 / 42 | 5.B Subject Exemption and Credit Transfer |

## Expected evidence and observations

The five Stage A cases and the following additional checks are proposed qualitative cases, not an agreed benchmark. Mappings were reviewed against the current chunk file and the source PDF; page numbers are printed / PDF.

| Case | Required evidence items and acceptable current chunk IDs | Observed top-five outcome |
|---|---|---|
| A1 | Medical Clinic phone and room: `sec12_D_002`, 101 / 120 | Rank 1 |
| A2 | Dental Clinic phone and room: `sec12_D_002`, 101 / 120 | Rank 2 |
| A3 | Emergency hotline and Campus Control Centre numbers: `app3_H_001`, 117 / 137 | Rank 1 |
| A4 | AR7 deferment deadline: `sec4_H_001`, 16 / 27 | Rank 1 |
| A5 | Transcript form: `sec7_A_001`; testimonial form: `sec7_B_001`, both 49 / 63 | Ranks 2 and 1 |
| P1 | Deferment application and deadline: `sec4_H_001`, 16 / 27 | **Miss:** not in top five. The question's “break” wording may also describe other processes; clarify intent and investigate paraphrase handling during evaluation. |
| P2 | Probation study-load rule: `sec6_C_001`, 38 / 51, or `sec5_A_001`, 28 / 40 | Ranks 1 and 2 |
| D1 | Retake limit and qualifications: `sec5_C_001`, 33 / 45 | Rank 1 |
| I1 | AR3 transcript: `sec7_A_001`; AR4 testimonial: `sec7_B_001`, both 49 / 63 | Ranks 3 and 2; unrelated `sec4_F_001` ranked first |

A possible team scoring rule is per-question Recall@5: the fraction of predefined required evidence items represented by at least one acceptable top-five chunk, averaged across answerable questions. A chunk may satisfy multiple items; unsupported cases are reported separately. Acceptable alternatives and question intent must be agreed before scoring. Do not report these exploratory checks as benchmark results or model selection evidence. Review mappings again if chunks change.

## Contract and failure checks

- Blank input returned `[]`; `top_k` 0 and -1 raised `ValueError`. `top_k=1` returned one result and `top_k=500` returned all 186. All observed results had exactly the five contract fields.
- Missing index, missing source, changed source, incompatible model setting, and missing Chroma generation each raised `RetrievalError`; source and generation cases used disposable paths and manifest copies. The unavailable-model case was simulated by injecting an `OSError` into the model loader and also raised `RetrievalError`. No fictional fallback occurred.
- The real index and approved sources were not modified for error tests. A missing-generation check can create files in its disposable directory; that directory was removed afterward.
- The evaluator script's `fitz` import emitted a deprecation `FutureWarning`; PDF source checking also used the supported `pymupdf` import. Earlier Stage A warnings and accepted limitations remain documented in `stage_a_review.md`.

## Follow-up

Investigate P1 and assess exact identifiers such as I1 in the agreed benchmark. Keep source-derived section annotations distinct from verbatim passage text. Rebuild the index and recheck mappings after any source or model change. Stage C must independently verify answer and citation support; these checks do not establish end-to-end correctness.

## Follow-up: investigation of the study-break query (2026-11-07)

The existing index and model were used unchanged. To inspect each channel, the full vector ranking was requested from Chroma and BM25Plus scores were sorted over documents with at least one matching query token. The production fusion uses only each channel's first 20 results for `top_k=5`. Ranks below are one-based; a dash means the passage is outside the fused top five.

| Question | Deferment `sec4_H_001`: vector / BM25 / fused | Class leave `sec4_F_001`: vector / BM25 / fused | Withdrawal `sec4_L_001`: vector / BM25 / fused |
|---|---|---|---|
| How can I take a break from my studies and when must I apply? | 20 / 44 / — | 10 / 98 / — | 1 / 51 / 4 |
| How can I temporarily pause my studies? | 36 / 61 / — | 16 / no token match / — | 1 / 64 / 3 |
| Can I take time off from my programme? | 26 / 28 / — | 4 / 98 / — | 5 / 74 / — |
| How do I defer my studies and what is the deadline? | 1 / 17 / 2 | 53 / 136 / — | 9 / 77 / — |
| How do I request a leave of absence? | 53 / 15 / — | 1 / 1 / 1 | 12 / 65 / — |
| How do I withdraw from my programme? | 34 / 22 / — | 12 / 63 / — | 2 / 42 / — (rank 8) |

The original query has a vocabulary mismatch: it does not contain “deferment” or “absence”, and common query words contribute to keyword matches. The vector channel associates it most strongly with withdrawal, while the deferment passage appears only at its candidate cutoff; keyword overlap and reciprocal-rank fusion leave that passage outside the top five. The same weakness appears in other natural temporary-break and withdrawal phrasings. A high vector rank alone is not guaranteed to survive fusion.

The source distinguishes **deferment of study** (AR7, printed page 16 / PDF 27), a **temporary absence from class** (AR8, printed page 14 / PDF 25), and **official withdrawal** (printed page 21 / PDF 32). “Take a break from my studies” does not establish which process or duration is intended. The answer service should seek clarification when context leaves that distinction unresolved and should not present withdrawal as necessarily intended. Whether the service actually does this remains to be tested in Stage C.

Two exploratory ranking changes were simulated without changing production code or the index. Removing common question words from BM25 did not bring the deferment passage into the top five for the original query and placed the withdrawal passage outside the top five for the withdrawal query. Adding `deferment leave absence` to the three temporary-break queries brought both relevant passages into the original query's top five, but did not bring the deferment passage into the top five for either other paraphrase; it also requires a narrow, manually triggered query rewrite. These small exploratory results do not establish a safe general improvement, so neither change was deployed. Existing A1–A5, retake and AR3/AR4 cases were also checked under the stop-word experiment; all expected evidence remained in their top five, but that does not offset the observed withdrawal regression.

**Disposition:** The production retriever and public contract remain unchanged. The paraphrase weakness and fusion behavior need broader, pre-specified evaluation before selecting a fix; include temporary class absence, programme deferment and permanent withdrawal as separate intents, plus ambiguous cases that require clarification. The Stage B integration gate remains a contract/provenance gate, not a claim that retrieval quality is adequate for every user question. Do not treat these exploratory rankings as an agreed benchmark or a production-quality fix.

## Refined study-break check and gate decision (2026-11-07)

At the project user's request, replace P1 as the **deferment smoke-check question** with: “I need to pause my programme for a semester. How do I apply, and what is the deadline?” The source-checked expected passage remains `sec4_H_001`, printed page 16 / PDF page 27. The original question and its miss remain above as historical evidence and an ambiguity/clarification case; rewording does not repair or erase that retrieval weakness.

The unchanged Stage B index and retriever returned the following:

| Rank | Chunk | Section | Printed / PDF page |
|---:|---|---|---|
| 1 | `sec4_K_002` | 4.K Student Status | 20 / 31 |
| 2 | `sec6_K_002` | 6.K Application for Graduation | 48 / 61 |
| 3 | `sec4_K_003` | 4.K Student Status | 21 / 32 |
| 4 | `sec4_H_001` | 4.H Deferment of Study | 16 / 27 |
| 5 | `sec4_I_001` | 4.I Zero Subject Enrolment and Retention of Study Place | 17 / 28 |

The expected deferment passage is in the top five at rank 4. For context, two additional exploratory checks returned `sec4_F_001` (temporary class absence) at rank 1 for “I need to miss classes temporarily. How do I apply for leave of absence?”, but did **not** return `sec4_L_001` (official withdrawal) in the top five for “I want to leave my programme permanently. How do I withdraw?”. The latter remains a retrieval-quality limitation; do not infer withdrawal quality from the refined deferment result.

**Decision:** Stage B passes its stated integration gate: the index is tied to the approved data, representative retrieval returns contract-compliant passages with checked pagination, and the documented failure cases raise explicit errors. Retrieval quality and the agreed benchmark remain pending, and the ambiguous query and withdrawal miss must be carried into subsequent evaluation. This pass does not establish that all natural questions retrieve the needed evidence or that answers and citations are correct. No retrieval-system code or index was changed for this refinement.

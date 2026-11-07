# Stage A handbook validation record

**Date:** 2026-11-07 (Hong Kong)  
**Reviewer:** Codex  
**Gate: PASSED on 2026-11-07 by the project user**, with the documented table-coverage limitation accepted. See the gate decision at the end of this record. The table detector can miss tables; this decision is not a claim of exhaustive coverage.

## Identity and automated checks

The PDF is assumed to be the authorized local 2026/27 copy; neither the hash nor this review establishes permission to redistribute it or the tracked handbook-derived files. The following commands were run from the integration root with the dedicated `.venv`:

```sh
shasum -a 256 data/handbook.pdf data/chunks.jsonl
.venv/bin/python scripts/validate_chunks.py --chunks data/chunks.jsonl --pdf "$PWD/data/handbook.pdf"
HANDBOOK_PDF="$PWD/data/handbook.pdf" .venv/bin/python -m pytest -q -rs tests/test_member1_pipeline.py tests/test_member1_review_regressions.py
```

| Artifact / check | Result |
|---|---|
| PDF SHA-256 | `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464` — matches `source_sha256` in `data/chunks_stats.json` |
| Chunk SHA-256 | `2729978a200ca6738a4a50e44d0f5778069400a339a4f6dcc8dd50644c73665c` — matches integration baseline |
| PDF-aware validator | Passed schema, IDs, page mapping, coverage and PDF text checks; 44 short-chunk warnings, allowed at page/section boundaries |
| Member 1 tests | 20 passed; five SWIG `DeprecationWarning`s; no skips |

These checks establish neither table semantics nor complete visual coverage. No PDF, chunks, companion data or index were rebuilt or replaced.

## Page mapping

The validator and tests checked the 117 numbered body pages. Additionally, Codex compared the PDF text-layer page labels with chunk metadata immediately before and after every recorded divider: PDF 8, 10, 14, 18, 39, 49, 62, 67, 78, 82, 84, 97 and 127. Each adjacent body page had the expected consecutive printed number; no divider had a chunk. At the last boundary, PDF 126 maps to printed 107, PDF 127 is the appendix divider and the PDF text layer contains a decorative `108`, and PDF 128 maps to printed 108. PDF 127 and 128 were also visually inspected. This boundary check uses the source text layer; it is not a visual inspection of every footer.

## Initial manual source comparisons and findings

This section records the initial review. Its statements about remaining unchecked pages are superseded by the follow-up below; its defect observations still apply to the original data.

All observations below are by Codex on 2026-11-07, comparing rendered source pages with the page's chunks. “Partial” means specific relationships were checked, not every number or cell on the page. The checklist remains authoritative for unreviewed pages.

| PDF / printed | Chunks | Outcome |
|---|---|---|
| 25 / 14 | `sec4_D_002`, `sec4_E_001`, `sec4_F_001` | Form-table relationships and extension deadline preserved; maximum-registration rule matches with its cohort restriction. |
| 45 / 33 | `sec5_C_001` | Second-retake form source, recipient and deadline preserved; retake rule below verified. |
| 51 / 38 | `sec6_C_001` | Probation form source, recipients and one-week application period preserved. |
| 56–57 / 43–44 | `sec6_I_001`, `sec6_I_002` | **Defect:** the appeal-grounds table continues across pages. Printed 44 visually places the assessment-irregularity ground under subject-result appeals and the illness ground under de-registration appeals; the award-classification column is shaded. `sec6_I_002` contains both grounds as consecutive paragraphs without the column headings or shading. It cannot establish which ground applies to which appeal. Do not use it alone for appeal-ground applicability. Printed 43's first ground spans all three columns, but the flattened text does not explicitly express that relationship. |
| 70–71 / 55–56 | `sec8_C_002`, `sec8_C_003` | PPS registration, settlement and hotline values and language order match the respective source rows; rows are split across pages, with the headers repeated on PDF 71. |
| 75 / 60 | `sec8_H_002`, `sec8_H_003` | **Partial; ambiguity:** local and non-local UGC-funded tuition tables group `Full-time Part-time` before both fees. The source aligns full-time with annual fees and part-time with per-credit fees; the chunk relies on ordering and units rather than explicit pairs. Inspect the PDF for mode-to-fee claims. All cohort notes have not been individually checked. |
| 76 / 61 | `sec8_I_001` | **Partial; ambiguity:** postgraduate application categories are grouped before `800 1,200 500`; the source aligns each amount with its own row. Caution money HK$400 and appeal fee HK$200 match their source rows. Do not rely on the grouped list alone for category-to-fee mapping. |
| 77 / 62 | `sec8_I_002` | **Partial; footnote ambiguity:** source gown-hiring footnote 1 and testimonial footnote 2 appear in text as `footnote 11` and `100/copy2`; confirm against PDF before use. Selected graduation and certification amounts match. |
| 106 / 87 | `sec12_B_007`, `sec12_B_008` | Cases I–V and listed actions were compared. Case I fines HK$80, HK$160 and HK$320 match third, fourth and fifth/subsequent breaches respectively; retain the one-year accumulation condition and distinguish other cases. |
| 115 / 96 | `sec12_C_008` | **Partial:** reception and residence/sports service hours match source ordering; extracted counselling email is broken by a space (`.edu. hk`), so the address must not be copied without source verification. |
| 116 / 97 | `sec12_C_009` | **Partial; ambiguity:** opening-hour columns are flattened, including Global Student Hub's weekday/holiday conditions; source grid must be consulted for day-to-hour claims. Venue names span several rows in the sports table. |
| 117 / 98 | `sec12_C_010` | **Partial; ambiguity:** the opening-hours and booking-session columns are flattened into successive blocks. The squash-court row continues a venue from the preceding page, so this chunk lacks the venue context. Consult both PDF pages for facility/venue and opening/booking distinctions. |
| 118 / 99 | `sec12_C_011` | Joint Sports Centre daily hours, soccer-pitch exception, and general-holiday referral match the source table. |
| 119 / 100 | `sec12_C_012` | Hall room fees and the HK$900 hall caution money and HK$400 per residential year function fee match the source, including merged Homantin venue cell. |
| 128 / 108 | `app1_001`, `app1_A_001` | Cyclone/extreme-conditions class cancellation and resumption time rows, started-class rule and exceptions match the source. Preserve the heading chunk when establishing applicability. |
| 129 / 109 | `app1_A_002` | Exam postponement, resumption cutoff pairs, started-exam rule and exceptions match the source. |
| 130 / 110 | `app1_A_003`, `app1_B_001` | Rainstorm class cancellation and resumption time rows, started-class rule and exceptions match the source; general applicability is in the preceding chunk. |
| 131 / 111 | `app1_B_002` | Rainstorm examination rules, cutoff pairs, started-exam rule and exceptions match the source. |

The detector checklist is not proof that every source table was found. Pages not described above have not been visually compared in this review; partially reviewed pages require a complete cell-by-cell check. In particular, the remaining checklist includes PDF 24, 26, 29, 31–34, 35–36, 38, 42, 44, 48, 61, 65–66, 89, 109, 122–123; see the checklist itself for exact entries. Broader undiscovered table coverage remains unresolved.

## Numerical rules

| Rule | PDF / printed; chunk | Source and chunk comparison |
|---|---|---|
| Normal and maximum study load | 40 / 28; `sec5_A_001` | 15 credits per semester normally; maximum 21, with pre-assignment and exceptional-approval qualifications. |
| Probation study load | 40 / 28 and 51 / 38; `sec5_A_001`, `sec6_C_001` | Normally no more than 15 credits in the following semester, excluding summer term; academic advice required. |
| Retakes | 45 / 33; `sec5_C_001` | Maximum two retakes per subject; departments may impose stricter rules, and compulsory-subject failure after two retakes leads to de-registration. |
| Maximum registration | 25 / 14; `sec4_E_001` | Normally twice normal duration, at most eight years; applies to students admitted in or before 2019/20. |
| Caution money | 76 / 61; `sec8_I_001` | HK$400, with refund and graduation-fee conditions in source and text. |
| Late assessment and appeal | 56–57 / 43–44; `sec6_H_001`, `sec6_I_002`; 76 / 61; `sec8_I_001` | Late assessment application within five working days. Subject-result appeal HK$200 per exam paper, refundable if successful, and appeal within one calendar week; source general fee table lists HK$200. These pages do not establish a late-assessment fee; do not infer one. Other appeal types and further pages remain unchecked. |
| Library fine | 106 / 87; `sec12_B_007` | Case I: HK$80 / 160 / 320 for third / fourth / fifth and subsequent breaches, with one-year accumulation condition. |
| Probation GPA | 51 / 38; `sec6_C_001` | Below 1.70 triggers probation; 1.70 or above at end of probation semester lifts it. |

## Initial resolution needed

See the follow-up below for work completed since this initial assessment.

1. Member 1 and the integration team should resolve and verify the appeal applicability defect and other affected table relationships against the source, without overwriting the supplied chunks in place. A changed extraction needs separate review of chunk IDs, index provenance and benchmark mappings.
2. Complete the unchecked and partially checked checklist pages, checking all numbers, units, merged cells, column relationships and cross-page continuation; investigate tables the detector may have missed. Update the record with individual outcomes and reviewer.
3. Confirm redistribution permission separately. After resolving the critical defect and completing relevant manual coverage, rerun PDF-aware validation and tests on the reviewed candidate and decide the Stage A gate explicitly.

## Follow-up: visual comparisons and appeal candidate (2026-11-07)

**Reviewer:** Codex. All checklist pages have now been visually compared with the corresponding original chunks. A checked box records a comparison, not a clean extraction. The outcome and qualifications for previously partially checked pages are in the table above. No claim is made that the table detector found all tables, or that the original dataset has been repaired.

The following additional page-specific comparisons were made against the source layout. “Match” refers to the listed table relationships, not a claim about the entire page or all other possible issues.

| PDF / printed | Chunk(s) | Outcome |
|---|---|---|
| 24 / 13 | `sec4_C_004` | AR1 form source and recipient match. |
| 26 / 15 | `sec4_G_001` | AR38 form source and recipient match. |
| 29 / 18 | `sec4_I_002`, `sec4_J_001` | Continuation deadline and transfer form recipients and 31 January/30 September deadlines match; the first deadline belongs to the previous page's form. |
| 31 / 20 | `sec4_K_002` | AR121a/b source, recipient and deadline match. |
| 32 / 21 | `sec4_K_003` | AR114 source, recipient and deadline match. |
| 33 / 22 | `sec4_L_002` | AR6 application path and deadline match. |
| 34 / 23 | `sec4_L_003` | AR10 source, email recipient and three-week deadline match. |
| 35 / 24 | `sec4_M_002` | AR147 and AR164 application paths match; the source itself displays the second form without a separate title. |
| 36 / 25 | `sec4_M_003` | Both AR164 application boxes match. |
| 38 / 27 | `sec4_M_005` | AR167 application path matches. |
| 42 / 30 | `sec5_B_002` | AR41e path and AR41f/AR163 sources, recipients and deadlines match. |
| 44 / 32 | `sec5_B_004` | AR41a source, recipient, deadline and AR41c application path match. |
| 48 / 36 | `sec5_H_002` | AR118 source, recipient and two-week deadline match. |
| 61 / 48 | `sec6_K_002` | AR84c source, recipient and last-teaching-week deadline match. |
| 65 / 51 | `sec7_D_001` | AR106 source and recipient match; HK$250 certification and HK$800 replacement fees match nearby source prose. |
| 66 / 52 | `sec7_D_002`, `sec7_E_001` | AR171 and AR5 form sources and recipients match. |
| 89 / 71 | `sec11_C_002` | Campus building weekday, Saturday, Sunday and holiday hours match. |
| 109 / 90 | `sec12_C_002` | The detector flagged a list rather than a table; counselling contact methods and number match. |
| 122 / 103 | `sec12_F_001` | Facility names, locations and listed times are present; the catering rows group days and times into separate sequences. Their association requires the source grid. |
| 123 / 104 | `sec12_F_002` | Facility names, locations and listed times are present; multiple rows group days and times separately. Their association requires the source grid. |

For PDF 75–77 and 115–117, the source pages and page text were inspected again: the numeric values and times visible in the tables are present, but the previously recorded category/fee, footnote, venue and day/time ambiguities remain. The source tables on PDF 56–57 were also compared again; the original chunks remain unsafe for appeal-ground applicability. An unchanged PDF-aware validator cannot detect these visual relationships.

### Appeal repair candidate

`scripts/build_stage_a_appeal_candidate.py` creates an edition-locked, separate candidate from the unchanged baseline chunks and PDF. It splits the source text at the three appeal table cells, keeps each passage on its original PDF page and places the visually verified column meaning in its `section` label. The common first ground applies to all three appeal categories; the continuation cells apply respectively to subject-result and de-registration appeals. The labels are **derived source-layout annotations**, not verbatim headings on PDF page 57. They appear in the existing evidence formatter alongside the chunk text. This is a deliberate enrichment of section labels that requires integration review; the text remains verbatim from the cited page.

Candidate built at `/tmp/gp-stage-a-candidate.ZRnll3/chunks.jsonl` (temporary local path, not a promoted dataset): SHA-256 `0dc8d71f6efcb27ba2216dc4e1d483f747a5c7a6143ff9ae5a92d4a888753c59`; 186 chunks, versus 183 in the baseline. Reproduce with a fresh output path:

```sh
.venv/bin/python scripts/build_stage_a_appeal_candidate.py --chunks data/chunks.jsonl --pdf data/handbook.pdf --out /path/to/new/chunks.jsonl
.venv/bin/python scripts/validate_chunks.py --chunks /path/to/new/chunks.jsonl --pdf "$PWD/data/handbook.pdf"
```

The candidate validator passed with 47 short-chunk warnings; splitting accounts for three additional warnings. The added regression test checks that the page texts reassemble without loss, labels correspond to the inspected columns, IDs are unique, and all non-appeal chunks are unchanged. The regression and Member 1 tests passed together (21 passed, five SWIG deprecation warnings); the builder also rejected an attempt to overwrite its input. The labels were verified visually against PDF 56–57; test assertions are not a substitute for that source comparison.

All IDs in section 6.I after the split change, including IDs that previously identified other content. Existing indexes and benchmark mappings must not be reused with the candidate. The existing tracked data and index have not been modified. The candidate is not a complete resolution of the original data gate: it has not been promoted or independently reviewed, and fee and opening-hour table ambiguities remain. Keep the original affected evidence restricted and the gate **NOT PASSED** until the team reviews a complete treatment, validates the actual selected artifacts and addresses the remaining critical relationships.

## Promotion of the appeal correction (2026-11-07)

At the user's request the candidate was promoted to `data/chunks.jsonl`, with matching recomputed statistics in `data/chunks_stats.json`. The original PDF, page map and table report were not changed. The current chunk SHA-256 is `0dc8d71f6efcb27ba2216dc4e1d483f747a5c7a6143ff9ae5a92d4a888753c59`; the former hash was `2729978a200ca6738a4a50e44d0f5778069400a339a4f6dcc8dd50644c73665c`. A fresh build from the authorized PDF now deterministically applies the reviewed source-layout annotations and reproduces the promoted candidate; it refuses to apply them if the raw extraction differs.

The previous references to an unpromoted candidate and the original appeal chunks in earlier entries are historical. `sec6_I_002` now describes the common ground, `sec6_I_003` the subject-results ground, and `sec6_I_004` the de-registration ground. These descriptions are source-derived labels; the cited text remains from the stated source page. Old section 6.I IDs have been renumbered and may now identify different content. Rebuild every index using the new chunk hash and review or remap any benchmarks or saved citations before use. This promotion does not resolve the separately recorded tuition, facilities-hours and other table ambiguities; the Stage A gate remains not passed.

Post-promotion verification: the PDF-aware validator passed with 47 allowed short-chunk warnings; the full test suite completed with **69 passed, 8 subtests passed and five SWIG deprecation warnings**. The existing reproducibility test confirmed that a fresh build matches the promoted chunks.

## Fee and opening-hours table corrections (2026-11-07)

**Reviewer:** Codex. The source table pages were visually rechecked and the following edition-specific source-layout annotations were added to the section labels. Annotations are derived from the layout and are not presented as verbatim text from the page. The chunk `text`, IDs, printed and PDF page numbers remain unchanged from the appeal-corrected dataset.

| PDF / printed | Chunk | Correction |
|---|---|---|
| 75 / 60 | `sec8_H_002` | Explicitly pairs full-time and part-time UGC-funded bachelor's fee rates with local/non-local status and units. |
| 76 / 61 | `sec8_I_001` | Pairs the MBA, Faculty of Business doctorate and other taught-postgraduate admission categories with their respective fees and retains the non-JUPAS condition. |
| 77 / 62 | `sec8_I_002` | Identifies the gown footnote as footnote 1 and the testimonial's superscript 2 as footnote 2. |
| 115 / 96 | `sec12_C_008` | Records the counselling email without the PDF line-wrap space. |
| 116 / 97 | `sec12_C_009` | Explains the pairing of grouped days and hours, states the Global Student Hub hours and holiday condition, and identifies continuation of the sports venue table. |
| 117 / 98 | `sec12_C_010` | Identifies the squash-court venue from the preceding source page and distinguishes the opening-hours and booking columns, including the counter service and statutory-holiday notes. |
| 122 / 103 | `sec12_F_001` | Explicitly pairs each catering facility’s day groups with the corresponding hours or closed status. |
| 123 / 104 | `sec12_F_002` | Explicitly pairs each facility’s day groups and hours in the continued catering table. |

The PDF-aware validator checks the source text and pages, but does **not** independently prove the annotations; their relationships were verified visually against the rendered PDF. Retrieval uses passage text for search, while the answer prompt receives the annotated section label with the passage; retrieval quality for these cases remains to be evaluated in Stage B. The annotation builder is tied to the reviewed PDF and raw extraction hashes and rejects a changed baseline.

Current chunks SHA-256: `68ab7f94b6b81df2a070b9cf0ada6945b0ef8cfc28f0625516155e26895e0e77`; previous appeal-corrected SHA-256: `0dc8d71f6efcb27ba2216dc4e1d483f747a5c7a6143ff9ae5a92d4a888753c59`. The file hash changed although IDs and text did not. Existing indexes must be rebuilt; verify benchmark mappings against the current data. These targeted corrections do not establish that the detector found every table, nor validate unreviewed external or undiscovered tables.

Verification after these corrections: PDF-aware validation passed with 47 allowed short-chunk warnings. The full suite passed with **71 passed, 8 subtests passed and five SWIG deprecation warnings**. A separate comparison against the appeal-corrected artifact confirmed all 186 IDs, passage texts and page references are unchanged; the build reproducibility test regenerated the promoted file. Regression checks confirm the annotations are included in formatted answer evidence and that missing or duplicate annotations fail.

## Independent table-coverage follow-up (2026-11-07)

The [independent AI review](stage_a_independent_table_review.md) examined the earlier dataset with SHA-256 `68ab7f94b6b81df2a070b9cf0ada6945b0ef8cfc28f0625516155e26895e0e77` and found six pages omitted by the automatic table detector: PDF 20, 27, 28, 63, 120 and 137. Codex rendered those source pages and confirmed the reported structures. They are now listed in the checklist with the review's results and an explicit “Missed” label; no fabricated detector output has been added to `data/table_pages.csv`. The reviewer is an independent AI, not a human teammate sign-off.

The source-checked clinic/room and emergency phone row pairings now appear as marked editorial source-layout annotations in `sec12_D_002` and `app3_H_001`, respectively. The same PDF and original extraction hash guards apply. The updated file hash is `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`; all 186 chunk IDs, verbatim passage texts and page references remain unchanged from the independently reviewed dataset, and only these two section labels changed. Existing indexes require a rebuild because their source hash and metadata are stale.

Five source-backed candidate evaluation questions covering clinic contacts, emergency contacts, AR7 and AR3/AR4 are in ignored local `data/stage_a_review_cases.md`. They are proposed cases, not agreed benchmark results. A deterministic injected-service regression asks about emergency and control-centre numbers and checks that both annotated pairs reach the answer prompt and citation; it is not a real retrieval or model-quality evaluation.

**Coverage disposition:** The six identified inventory omissions are recorded and the two contact tables hardened. The automatic detector still misses these structures, and the review's lower-resolution sweep is not an exhaustive proof of all tables. Stage A remains pending team consideration of the residual coverage limitation, inspection/sign-off on the new findings, citation checks in later evaluation, and a separate redistribution decision. Do not treat the independent AI review as human approval or claim comprehensive table coverage.

Verification after this follow-up: PDF-aware validation passed with 47 permitted short-chunk warnings. The complete test suite passed: **72 passed, 8 subtests passed, five SWIG deprecation warnings**. The build reproducibility test passed against the promoted chunks.

## Stage A gate decision (2026-11-07)

The project user determined that the completed table-coverage review is sufficient and accepted the residual limitation: the automatic detector misses some table-like structures, and the independent visual sweep does not prove exhaustive coverage. The user decided that Stage A can pass on that basis. This is the user's decision, not a claim that every table was found or that another person signed off. The original review attribution remains Codex and the independent review attribution remains ChatGPT / GPT-6; no human reviewer names have been substituted for their work.

The passed gate applies to the PDF SHA-256 `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464` and chunks SHA-256 `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`. The latest PDF-aware validator passed, and the full suite reported 72 passed and 8 subtests passed. The six separately discovered pages and source-derived contact annotations are recorded above.

Proceed to Stage B using a newly built index tied to these chunks; investigate any newly discovered defects and stop using affected evidence if a critical problem appears. Claim-by-claim citation support and retrieval quality remain later evaluation work. Redistribution permission was confirmed by the project user in the subsequent record below.

## Redistribution confirmation (2026-11-07)

The project user confirmed that the handbook and handbook-derived project files can be redistributed. This records the user's confirmation; it is not an independently verified statement of the underlying licence or a claim about any specific publication venue. No files were shared or published as part of this confirmation.

Stage A is complete with the table-coverage limitation accepted in the gate decision above. The current data and PDF hashes remain those listed in that decision.

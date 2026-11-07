# Stage A — Independent table-coverage and source-layout review

**Project:** COMP4431 PolyU Academic Regulations Assistant  
**Source edition:** PolyU *Student Handbook for Taught Programmes 2026/27*  
**Review date:** 2026-11-07 (Hong Kong)  
**Reviewer:** ChatGPT / GPT-6 (independent AI reviewer; not a claim of human sign-off)  
**Decision recommendation:** **STAGE A GATE PENDING — do not mark passed on this review alone.**

## 1. Artifacts, method, and scope

The following uploaded files were examined as the review inputs. The names below correspond to the integration repository, not to new files created by this review:

| Repository artifact | Uploaded review copy | SHA-256 |
|---|---|---|
| `data/handbook.pdf` | `handbook.pdf` | `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464` |
| `data/chunks.jsonl` | `chunks(1).jsonl` | `68ab7f94b6b81df2a070b9cf0ada6945b0ef8cfc28f0625516155e26895e0e77` |

The uploaded chunks comprise **186 records** and the uploaded handbook **137 PDF pages**. Both hashes match the *current* artifact identities recorded in the supplied `stage_a_review.md`, rather than its older pre-correction versions.

**Procedure:** Read the existing review and its 40-page detector checklist first; render the specified PDF pages, inspect the actual printed tables, and compare them with `chunk_id`, `pdf_page`, `printed_page`, `section` and `text` from the JSONL. Conduct a lower-resolution visual sweep of PDF pages **9–137** to identify candidate missed tables, then independently render and inspect newly discovered candidates at higher resolution. The existing checklist entries were **not all rechecked cell by cell**. PyMuPDF's default `find_tables()` returns zero tables for all six newly identified pages (20, 27, 28, 63, 120, 137), corroborating why a geometry-based detector can miss these layouts; this is **not** a completeness proof for the scan.

**Boundaries:** Findings below distinguish verified pairings from limited spot checks. This review did **not** run the repository's validator/pytest suite, rebuild or mutate the PDF/chunks/index, verify external hours, or establish distribution rights. Page numbers are **PDF viewer numbers**, with printed numbers stated separately. The `section` annotations are editorial interpretations of the source layout, not direct PDF quotations.

## 2. Independent verification of the previously corrected tables

| PDF / printed | Existing chunk(s) | Result and independently verified relationship |
|---|---|---|
| **56 / 43** | `sec6_I_002` | **PASS (targeted):** the first administrative-error/material-irregularity appeal ground spans **subject result, de-registration and award classification** columns. The common-ground annotation correctly conveys this merged-cell meaning. |
| **57 / 44** | `sec6_I_003`, `sec6_I_004` | **PASS (targeted):** the assessment-conduct / marking-inconsistency ground occupies the **subject-result** column; the illness/other unforeseen factors ground occupies **de-registration**; the award-classification column is shaded/empty. The two separate annotated chunks correctly distinguish them. |
| **75 / 60** | `sec8_H_002`, `sec8_H_003` | **PASS (both main tables):** local full-time **HK$47,000/academic year**; local part-time **HK$1,570/credit**; non-local full-time **HK$200,000/academic year**; non-local part-time **HK$6,670/credit**. The annotation pairs each correct study mode, residency status and unit. The historical-cohort narrative notes were not independently audited for all cohort exceptions. |
| **76 / 61** | `sec8_I_001` | **PASS (targeted fees):** among applications not processed through JUPAS, **MBA HK$800**, **Faculty of Business doctoral programmes HK$1,200**, **other taught postgraduate programmes HK$500**. The source also shows undergraduate **HK$500**, visa application **HK$700**, caution money **HK$400**, credit transfer **HK$150/credit** and academic appeal **HK$200**, all reflected in the text. |
| **77 / 62** | `sec8_I_002` | **PASS (footnotes and selected amounts):** gown-hiring `1` and testimonial postage `2` are superscript footnote markers, not part of `11` or a squared price. The annotation explains this accurately. Certification is **HK$250/qualification**, graduation **HK$400**, replacement parchment **HK$800/qualification**, transcript/testimonial **HK$100/copy**. |
| **115 / 96** | `sec12_C_008` | **PASS (targeted contact repair):** the source line-wrap splits `stud.counselling@polyu.edu.hk`; the annotation restores the intended email. Reception is Monday–Friday **9:00 am–12:45 pm** and **2:00–6:00 pm**, closed Saturday/general holidays. Other table cells were not exhaustively checked. |
| **116 / 97** | `sec12_C_009` | **PASS (targeted hours/continuation):** Global Student Hub is Monday–Sunday **9:00 am–11:00 pm**, closed on **other general holidays**; the `Kwong On Jubilee Sports Centre` venue continues to PDF 117. The annotation's global-hub/continuation claims match the source. Remaining sports rows were only spot checked. |
| **117 / 98** | `sec12_C_010` | **PASS (targeted continuation/columns):** first squash-court row belongs to Kwong On Jubilee Sports Centre from the preceding page, and `Opening Hours` and `Booking Session` are distinct columns. The annotation preserves that interpretation and the statutory-holiday closure note. Not a full cell-by-cell booking-hours audit. |
| **122 / 103** | `sec12_F_001` | **PASS (all five catering rows):** each weekday/Saturday/Sunday/public-holiday condition and the corresponding time or `Closed` status matches the visual table. Also checked the separate four-row **Communal Facilities** table on the same page: banking and ATM 24/7, bookshop Mon–Fri 10:00 am–7:00 pm / Sat 10:00 am–5:00 pm / Sun and public holiday closed, convenience store daily including public holidays 7:00 am–11:00 pm; these are already present and associated in the text. |
| **123 / 104** | `sec12_F_002` | **PASS (all 13 catering rows):** each facility's grouped days and its hours/closure status match the PDF; see the row-level ledger below. |

### Catering row-level ledger (PDF 122–123)

`M–F` = Monday–Friday; `PH` = public holiday. Times below use the PDF's 12-hour clock; entries with `closed` are explicit closures in the source, not inferred.

| PDF / printed | Facility | Verified day → hours mapping |
|---|---|---|
| 122 / 103 | Block Y Outlet | M–F 8:00 am–8:00 pm; Sat 9:00 am–6:00 pm; Sun/PH closed |
| 122 / 103 | Communal Student Canteen | M–F 7:30 am–8:30 pm; Sat 7:30 am–7:30 pm; Sun/PH 9:00 am–7:00 pm |
| 122 / 103 | Communal Staff Restaurant | Mon–Sun and PH 11:00 am–10:30 pm |
| 122 / 103 | Communal Student Restaurant | M–F 10:30 am–8:00 pm; Sat 10:30 am–5:00 pm; Sun/PH closed |
| 122 / 103 | Gourmet Shop | M–F 8:00 am–7:30 pm; Sat/Sun/PH closed |
| 123 / 104 | H Cafe | M–F 8:00 am–10:00 pm; Sat 8:00 am–6:00 pm; Sun/PH 10:00 am–6:00 pm |
| 123 / 104 | Staff Club Restaurant | Mon–Sat 11:00 am–9:30 pm; Sun/PH closed |
| 123 / 104 | Theatre Lounge | Mon–Sun and PH 8:00 am–9:30 pm |
| 123 / 104 | U Garden (Staff Canteen) | M–F 7:30 am–8:30 pm; Sat 7:30 am–7:30 pm; Sun/PH closed |
| 123 / 104 | U Garden (Student Canteen) | M–F 7:30 am–8:30 pm; Sat 7:30 am–7:30 pm; Sun 9:00 am–6:00 pm; PH closed |
| 123 / 104 | VA Kiosk | M–F 7:00 am–9:00 pm; Sat/Sun/PH 9:00 am–8:00 pm |
| 123 / 104 | V Cafe | Mon–Sat 8:00 am–8:00 pm; Sun/PH closed |
| 123 / 104 | VA Staff Canteen | M–F and Sat 7:30 am–8:30 pm; Sun/PH closed |
| 123 / 104 | VA Student Canteen | M–F 7:30 am–8:30 pm; Sat 11:00 am–8:30 pm; Sun/PH closed |
| 123 / 104 | W Kiosk | M–F 8:00 am–8:00 pm; Sat 9:00 am–6:00 pm; Sun/PH closed |
| 123 / 104 | X Cafe | M–F 8:00 am–9:00 pm; Sat/Sun 9:00 am–6:00 pm; PH closed |
| 123 / 104 | Z Café (Certified Halal Kitchen Restaurant) | M–F 10:30 am–8:30 pm; Sat 10:30 am–6:30 pm; Sun/PH closed |
| 123 / 104 | Z Canteen | M–F 7:30 am–8:30 pm; Sat 7:30 am–7:30 pm; Sun 9:00 am–6:00 pm; PH closed |

**Correction outcome:** No new incorrect source-layout annotation or numerical pairing was found in these *specified* checks. This does **not** assert correctness of every unrelated table, figure, note, or cell on those pages.

## 3. Tables **missing from the automatic-detector checklist**

The original checklist has **40 distinct PDF pages**. A visual scan identified **six additional PDF pages** containing **seven table/table-like structures**: five small application information boxes and two substantive contact-data tables. The six pages are not listed in `member1_table_checklist.md` and the default PyMuPDF detector found none of their tables. All were independently rendered and checked against their page chunks.

| PDF / printed | Source section and missing structure | Matching chunk(s) | Independent result | Status |
|---|---|---|---|---|
| **20 / 9** | **4.B Student Identity Card:** blue-headed `Application for Replacement of PolyU Student Identity Card (Form AR2)` box | `sec4_B_002` | The source is **eStudent → Application Forms → Applications for Study Related Matters → (AR2) Replacement of PolyU Student Identity Card**. The displayed form name and path appear correctly in the chunk. | **PASS — add to checklist** |
| **27 / 16** | **4.H Deferment of Study:** `Form AR7` application/deadline box | `sec4_H_001` | eStudent AR7, supporting documents (medical certificate for medical grounds), and **deadline before commencement of the examination period of the semester concerned** match. The nearby **HK$5,000 local / HK$20,000 non-local** refund deductions are correctly in the source prose, not box cells. | **PASS — add to checklist** |
| **28 / 17** | **4.I Zero Subject Enrolment:** `Form AR112` application box | `sec4_I_001` | The AR112 eStudent route is correctly represented. The separate prose states **HK$2,350 per semester** for study-place retention; the amount must not be misrepresented as a form-box value. | **PASS — add to checklist** |
| **63 / 49** | **7.A Transcript / 7.B Testimonial:** **two separate** form boxes (`AR3`, `AR4`) | `sec7_A_001`, `sec7_B_001` | AR3 belongs to Transcript of Studies; AR4 belongs to Testimonial. Each separate section and form route is preserved; the prose quotes **HK$100/copy** for each, postage included. | **PASS — add to checklist** |
| **120 / 101** | **12.D University Health Service:** `Enquiries and Arrangement for Consultation` table | `sec12_D_002` | The website and **clinic → telephone → room** pairings are preserved and verified individually below. | **PASS — add to checklist** |
| **137 / 117** | **Appendix 3.H:** `Emergency Contact and Other Useful Telephone Numbers` **four-row, two-column** table | `app3_H_001` | All four service → telephone pairs are present and correctly ordered; verified below. **Caution:** source row boundaries are flattened into one text line, so add a layout annotation or explicit row separators for robustness. | **PASS with hardening action — add to checklist** |

### Newly discovered contact tables: exact checked cells

**PDF 120 / printed 101 — University Health Service (`sec12_D_002`)**

| Service | Telephone | Room |
|---|---|---|
| Website | `https://www.polyu.edu.hk/uhs` | — |
| Medical Clinic | **2766 5433** | **A001** |
| Traditional Chinese Medicine Clinic | **2766 5553** | **A125** |
| Dental Clinic | **2330 9414** | **GH020** |

**PDF 137 / printed 117 — Emergency contacts (`app3_H_001`)**

| Source table label | Telephone |
|---|---|
| 24-Hour Campus Emergency Hotline | **2766 7999** |
| Campus Control Centre | **2766 7666** |
| Health and Safety Office | **3400 8396** |
| University Health Service | **2766 5433** |

The numbers have not been verified against live telephone listings: **the handbook itself is the sole authority** for this review.

### Ready-to-copy additions to `member1_table_checklist.md`

These entries **propose updates** to the existing checklist; they have not been written into the user's repository. The `Detected tables` column intentionally says `missed` rather than inventing a detector output. `[x]` means the specified layout was compared visually, **not** that a complete handbook review or data gate passed.

| PDF | Printed | Detected tables / visual discovery | Section | Checked |
|---:|---:|---|---|---|
| 20 | 9 | **Missed**: AR2 application box | 4.B Student Identity Card | [x] |
| 27 | 16 | **Missed**: AR7 application/deadline box | 4.H Deferment of Study | [x] |
| 28 | 17 | **Missed**: AR112 application box | 4.I Zero Subject Enrolment and Retention of Study Place | [x] |
| 63 | 49 | **Missed**: AR3 and AR4 separate form boxes | 7.A Transcript of Studies / 7.B Testimonial | [x] |
| 120 | 101 | **Missed**: clinic contact/consultation table | 12.D University Health Service | [x] |
| 137 | 117 | **Missed**: 4-row emergency phone table | Appendix 3.H Emergency Contact and Other Useful Telephone Numbers | [x] |

## 4. Unresolved coverage defect and disposition

**`TBL-COVERAGE-001` — The detector's inventory is incomplete.**

- **Evidence:** six unchecked-by-inventory PDF pages identified independently: **20, 27, 28, 63, 120, 137**. The source structures are real and the chunks exist, so this is an **inventory/verification-coverage defect**, not proof of missing text. The especially answer-sensitive cases are **PDF 120, clinic contacts**, and **PDF 137, emergency contacts**.
- **Observed chunk correctness:** the reviewed numbers, units, form paths and row associations agree with their actual source layouts. **No new data-value error** was established in this limited sample.
- **Residual risk:** the reviewed emergency contacts are concatenated into a single paragraph, and the dataset depends on an LLM recognizing the label/number boundaries correctly. That pairing is readable but merits explicit layout annotation and a regression query. Low-resolution sweeping is not an exhaustive full-size inspection for every table.
- **Action:** add the six rows to the authoritative checklist and capture explicit per-table review results there or link this independent report. Consider an **edition-specific source-layout annotation** for `app3_H_001` (and optionally `sec12_D_002`) without changing source passage text; treat any changed `section` or chunk hash as a new artifact requiring a rebuilt index and updated provenance. Add benchmark cases that independently ask for **medical/dental clinic room and phone**, **campus emergency line vs Campus Control Centre**, **AR7 deadline**, and **AR3 vs AR4**. Use source PDF pages as the answer key.
- **Required before gate promotion:** team inspection/sign-off on these newly detected items; confirmation that the coverage search is sufficient (or a defined, documented accepted limitation); run the actual PDF-aware validator and project test suite after any changes; evaluate source citation correctness, and resolve handbook redistribution/provenance questions separately. No conclusion here supersedes the Stage A integration team's gate decision.

**Recommended gate status: `PENDING / NOT PASSED`.** Existing source-layout corrections passed the targeted independent checks, but the newly exposed inventory omissions should be recorded and addressed before declaring that all tables are covered. If the team chooses to accept the remaining risk, that should be an explicit, documented waiver rather than interpreting all checked boxes as a complete table audit.

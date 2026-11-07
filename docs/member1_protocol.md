# Member 1 Protocol — Handbook Processing & Data

| Field | Value |
|---|---|
| Owner | Member 1 — Handbook Processing & Data |
| Branch | `feature/data` |
| Status | Implemented and validated against the supplied PDF |
| Version | 1.0 |
| Source document | `Student Handbook for Taught Programmes 2026/27` (Academic Registry, July 2026), 137 PDF pages |
| Consumers | Member 2 (retrieval/index build), Member 3 (answer composition), Member 4 (UI display) |

This document is the contract for the preprocessing stage. It describes exactly what
Member 1 produces, how page and section metadata are derived, and what downstream
members may rely on. Code that implements it lives in `src/pdf_processor.py`,
`src/chunker.py` and `scripts/build_chunks.py`. It is written **before** the code,
as agreed in the team workflow.

---

## 1. Scope

Member 1 converts the handbook PDF into a list of **chunks** — contiguous, page-bounded
passages of handbook text with stable identifiers and page/section metadata. Member 1
does not embed, index, retrieve, or answer questions.

Out of scope for this stage (handled elsewhere):

- embeddings, ChromaDB, BM25, RRF, retrieval (Member 2)
- prompt design, DeepSeek calls, citation validation (Member 3)
- Streamlit rendering (Member 4)
- programme-specific requirements external to the handbook

---

## 2. Input and output

### Input

The exact supplied PDF file. The pipeline never downloads anything and never reads
the network. The file is identified by its content, not by its filename; the
document title in the PDF metadata is `Student Handbook for Taught Programmes 2026/27`.

### Output

`data/chunks.jsonl` — one JSON object per line, UTF-8, `ensure_ascii=False`, in
reading order. Each object has **exactly five fields**, matching the canonical chunk
in `PROJECT_IMPLEMENTATION_PLAN.md`:

```json
{
  "chunk_id": "sec5_C_001",
  "section": "5.C Retaking of Failed Subjects",
  "printed_page": 33,
  "pdf_page": 45,
  "text": "C. Retaking of Failed Subjects\n\nStudents may only retake a subject ..."
}
```

No other keys are written to this file. Derived statistics and debugging aids go to
separate files (`data/chunks_stats.json`, `data/page_map.csv`,
`data/table_pages.csv`) so that the chunk file stays a stable, strict contract.

---

## 3. Page model

Two page numbers are tracked for every chunk because the handbook's printed
pagination differs from its PDF pagination.

| Field | Meaning | Basis |
|---|---|---|
| `pdf_page` | Position in the PDF file, **1-based** | PDF viewer page counter |
| `printed_page` | Page number printed in the handbook footer | Footer of the page |

### 3.1 Verified facts about the supplied file

| Property | Value |
|---|---|
| Total PDF pages | 137 |
| Printed page range | 1 – 117 |
| Body pages (have a printed page number) | 117 |
| Front matter (paged but unnumbered) | PDF 1 – 7 (cover, motto, Chinese motto, contents ×4) |
| Chapter divider pages | PDF 8, 10, 14, 18, 39, 49, 62, 67, 78, 82, 84, 97, 127 |
| Body pages with a printed page number | exactly the 117 pages 1 … 117, no gaps, no duplicates |

**The PDF→printed offset is not constant.** It increases by one at each chapter
divider, from +8 at the start to +20 at the end:

| Printed page | 1 | 2 | 5 | 8 | 28 | 37 | 49 | 53 | 63 | 66 | 67 | 79 | 108 | 117 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PDF page | 9 | 11 | 15 | 19 | 40 | 50 | 63 | 68 | 79 | 83 | 85 | 98 | 128 | 137 |

Therefore `printed_page` must never be computed as `pdf_page + constant`. It is read
from each page's footer and then validated for continuity.

### 3.2 Divider and front-matter pages

Divider pages carry only a large decorative illustration and chapter display title;
they contain no regulations. They are **excluded** from the chunk output. Front
matter (PDF 1–7) is also excluded, because it contains no regulatory content and
its contents page would otherwise pollute retrieval.

Consequence: **not every `pdf_page` appears in the chunk file.** A consumer must not
assume that `pdf_page` values are contiguous. This is expected, not an error.

### 3.3 Page-map algorithm

1. Check the documented 137-page document length and use the known front-matter
   and divider positions in §3.1.
2. Read each remaining page's bottom-most standalone integer in the bottom 70 pt.
   Require the exact sequence 1–117, including the final page; missing, repeated,
   or out-of-order numbers fail the build.
3. Check the known divider footers, including decorative 8 on PDF page 39 and
   108 on PDF page 127, without treating them as body pages.
4. Reject outline divider entries that point outside the documented divider set.

Different editions require a page-model review before processing.

---

## 4. Section model

### 4.1 Where sections come from

Section headings are detected from the PDF's typography, not by string matching
against the table of contents, because several headings wrap across lines or are
split across spans (e.g. `A. Learning Management System, eStudent and Computing` /
`Facilities`, or `Appendix 3. Health, Safety and Environment` / `Requirements`).

Verified typography of this file:

| Role | Font size | Example |
|---|---|---|
| Chapter heading | 22 pt bold | `5. Subject Registration` |
| Chapter heading (appendix) | 22 pt bold | `Appendix 2. Plagiarism` |
| Subsection heading | 16 pt bold | `C. Retaking of Failed Subjects` |
| Body text | 12 pt regular | — |
| Divider display title | 24 pt | excluded with the divider page |

Consecutive heading lines of the same class are merged, which reconstructs wrapped
headings such as `E. Maximum Period of Registration (Applicable to Students
Admitted in or before 2019/20)`.

### 4.2 Label format

`section` follows the example in `PROJECT_IMPLEMENTATION_PLAN.md`:

| Situation | `section` value | Section key used in `chunk_id` |
|---|---|---|
| Chapter, before any subsection | `5. Subject Registration` | `sec5` |
| Chapter subsection | `5.C Retaking of Failed Subjects` | `sec5_C` |
| Appendix chapter | `Appendix 1. Arrangements during Bad Weather` | `app1` |
| Appendix subsection | `Appendix 1.A Tropical Cyclone Warning and 'Extreme Conditions'` | `app1_A` |

Deeper headings (`i.`, `ii.`, roman-numeral items inside a subsection) are **not**
promoted to the `section` field. They remain inside the chunk text, which keeps the
`section` field at the granularity used by the plan and by Member 2's ranking
metadata.

### 4.3 Continuity

A page can contain the start of a new section after the tail of the previous one.
Paragraphs are labelled with the section that is in force at their position, so the
tail of page N keeps its old label and the rest of page N takes the new one. A
section may therefore continue across pages; its chunks keep the same `section`
value on every page.

---

## 5. Chunk schema

| Field | Type | Required | Semantics | Guarantees |
|---|---|---|---|---|
| `chunk_id` | string | yes | Stable identifier | Unique across the whole file; matches `^(sec\d+(_[A-Z])?|app\d+(_[A-Z])?)_\d{3}$` |
| `section` | string | yes | Section label as in §4.2 | Non-empty; same label for every chunk of one section |
| `printed_page` | integer | yes | Handbook footer page, 1-based | `1 <= printed_page <= 117` |
| `pdf_page` | integer | yes | PDF page, 1-based | `1 <= pdf_page <= 137`; maps to `printed_page` per §3 |
| `text` | string | yes | Complete passage text | Non-empty; contains the full text of the paragraphs in the chunk; never truncated mid-sentence |

`text` is **complete**, not an excerpt. A chunk never contains a truncated word, and
the UI's expandable source view can display it verbatim.

### 5.1 Chunk ID scheme

```
{section_key}_{sequence:03d}
```

- `section_key` is `sec{n}` / `sec{n}_{letter}` for chapters, `app{n}` /
  `app{n}_{letter}` for appendices.
- `sequence` starts at `001` for each section key and increments in reading order.

Example (matches the plan's example):

```
sec5_C_001   →  5.C Retaking of Failed Subjects, printed 33, PDF 45
```

**Uniqueness.** Every chunk belongs to exactly one section key and receives a
distinct sequence number within that key; keys are derived from the document's
chapter/subsection numbering, which is unique. Hence IDs are unique.

**Stability.** The pipeline is deterministic: no randomness, no timestamps, no
filesystem-order dependence, JSONL written in reading order. Re-running on the same
PDF with the same parameters reproduces byte-identical `chunk_id` and `text`.

**What breaks stability.** Changing `--max-words`, `--min-words`, the de-hyphenation
rule, or the source PDF version changes chunk boundaries and therefore sequence
numbers. When that happens, the index must be rebuilt and the benchmark re-run;
record the parameter set in `data/chunks_stats.json` (the build writes it).

---

## 6. Chunking rules

1. **A chunk never crosses a page boundary.** Every chunk resolves to exactly one
   `printed_page` / `pdf_page`, so a citation always points at one page.
2. **A chunk never mixes two sections.** Section change forces a flush.
3. Target size **400–700 tokens**, approximated as **450 words** maximum,
   **100 words** minimum. These are starting parameters, not a hard rule; expose
   them as CLI flags and record the values used.
4. Paragraphs are the atomic unit. A paragraph larger than the maximum is split on
   sentence boundaries, never mid-sentence.
5. A short trailing chunk is merged into the preceding chunk of the same section on
   the same page only when the result still fits the maximum. A short chunk at a
   page or section boundary is left as is.
6. The section heading line is included as the first paragraph of a section's text
   on the page where it appears, so that each chunk carries its own context for
   embedding and for the LLM.

Result on the supplied file: see `data/chunks_stats.json` for the exact counts
produced with the default parameters.

---

## 7. Text normalisation

Applied in this order:

1. Drop the footer page-number line (it is metadata, not content).
2. Replace non-breaking and narrow spaces with a normal space; remove zero-width
   characters.
3. Collapse runs of spaces; strip trailing whitespace per line.
4. Join wrapped lines with a single space; keep a hyphen when a word is broken at a
   line break (`non-` + `refundable` → `non-refundable`).
5. Keep bullet and list markers on their own line (`•`, `a)`, `1)`, `i.`), so lists
   stay readable after joining.
6. Separate paragraphs with a blank line.
7. Do **not** lowercase, stem, translate, or remove punctuation. Form identifiers
   (`AR160`, `AR114`), section references (`Section 6C`), and numeric rules
   (`21 credits`, `HK$47,000`) must survive verbatim.

The handbook is English; Chinese text exists only on the front-matter motto page
(PDF 3), which is excluded.

---

## 8. Tables

The handbook contains 44 pages with detected tables (fee schedules, library
penalties, opening hours, bad-weather arrangements). PyMuPDF extracts table cells
in reading order but **does not preserve column structure** for tables with merged
cells.

Policy:

- Default extraction is plain text (`--tables text`). It is faithful to the content
  and never duplicates or reorders cells, but multi-column relationships can be hard
  to read in the flattened form.
- An experimental `--tables markdown` mode renders simple tables as pipe-delimited
  rows. It is off by default because merged-cell tables (e.g. PDF 115, PDF 128) are
  mis-gridded.
- `data/table_pages.csv` lists every page and table detected, with row/column counts
  and bounding boxes, as the working list for the manual verification required by
  the plan.

Member 1's definition of done includes manual checking of tables and numerical
rules. The checklist is in `docs/member1_table_checklist.md`.

---

## 9. Reproducibility

- Pure function of (PDF bytes, parameters). No network, no clock, no randomness.
- Output order is document order; IDs depend only on content.
- The build writes the parameters and input fingerprint into
  `data/chunks_stats.json` so that a benchmark result can be tied to an exact chunk
  set.
- The generated `data/chunks.jsonl` is committed for convenience so that Member 2
  can start before the PDF is shared. It can be regenerated with
  `python scripts/build_chunks.py --pdf data/handbook.pdf`. The handbook PDF itself
  should only be committed if the course permits redistribution; otherwise each
  member uses the authorised copy.
- To check reproducibility without overwriting committed outputs, run
  `python scripts/build_chunks.py --pdf /path/to/handbook.pdf --out /tmp/chunks_check.jsonl`.
  The companion files default to `/tmp/chunks_check_stats.json`,
  `/tmp/chunks_check_page_map.csv`, and `/tmp/chunks_check_table_pages.csv`.
  `--stats`, `--page-map`, and `--table-report` override those destinations.
  The normal default build retains the original `data/` filenames.

---

## 10. Validation

With a PDF supplied, `scripts/validate_chunks.py` checks:

- every record has exactly the five contract fields, with the right types;
- `chunk_id` is unique and matches the ID pattern;
- `printed_page` ∈ [1, 117] and `pdf_page` ∈ [1, 137];
- each PDF page is a numbered body page and maps to the chunk's printed page;
- `text` is non-empty, has no footer artefact, and is not truncated;
- every body page 1 … 117 is represented by at least one chunk;
- every chunk's text is a verbatim (whitespace-normalised) substring of its own
  PDF page's extracted text — this catches cross-page leakage and accidental
  text loss;
- chunk word counts are within the configured bounds (maximum ×1.2 tolerance for
  an indivisible oversized paragraph).

Without a PDF, the validator reports that page mapping, coverage, and text
integrity were skipped; only schema and chunk-size checks are performed.

`tests/test_member1_pipeline.py` asserts the page-map facts in §3, the ID scheme,
schema conformance, page coverage, and text integrity. It runs with `pytest` or
directly with `python tests/test_member1_pipeline.py`.

---

## 11. Handoff guarantees to Member 2

For **every** chunk in `data/chunks.jsonl`:

| Requested field | Provided | Notes |
|---|---|---|
| `chunk_id` | yes | unique, stable, string |
| `section` | yes | non-empty label per §4.2 |
| `printed_page` | yes | 1-based, 1–117 |
| `pdf_page` | yes | 1-based, 1–137, not necessarily contiguous |
| `text` | yes | complete passage, never truncated |

Additional guarantees Member 2 can rely on:

- chunks are in reading order, so `sort by (pdf_page, chunk_id)` is a valid
  reconstruction of the document;
- the `section` value is stable per section and can be used as a grouping/filter
  key;
- no chunk spans two pages or two sections, so any citation resolves unambiguously.

Member 2 may attach retrieval scores in a separate structure. Scores must not be
written into `chunks.jsonl`.

---

## 12. Change control

Any change to this protocol is a **contract change** and requires a note here plus a
message in the team channel before the index is rebuilt:

| Change | Impact |
|---|---|
| chunk size parameters | chunk IDs change → rebuild index → re-run benchmark |
| new field in `chunks.jsonl` | breaks the strict five-field contract → agree with Member 2 first |
| new source PDF version | page map must be re-verified; IDs may change |
| section granularity (e.g. promoting `i./ii.`) | `section` values change → agree with Members 2–4 |

---

## 13. Known limitations

1. **Merged-cell tables** lose column structure in plain text; see §8 and the
   manual checklist.
2. **Two-column table blocks** in the source may be emitted cell-by-cell rather
   than row-by-row in a few places.
3. **Bullet hierarchy** is flattened to `•` lines; nested list levels are not
   encoded.
4. **Front matter and divider pages are excluded**, so the model cannot answer
   questions about the handbook's own table of contents. This is intended.
5. **No OCR**: the PDF has a selectable text layer, so OCR is unnecessary. A
   scanned replacement copy would require a different pipeline.

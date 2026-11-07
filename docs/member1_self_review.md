# Member 1 — code review record

Per the team rule ("let AI review the code before committing"), this is the review
pass over `src/pdf_processor.py`, `src/chunker.py` and `scripts/`.

It records **real defects found and fixed**, not a checklist of things that look
fine. The review was done against the reference PDF, and every fix is covered by
either a test or a validation check.

---

## 1. Defects found and fixed

| # | Where | Defect | Fix |
|---|---|---|---|
| 1 | `_detect_page_map` | Body-page detection required footer `1` to be followed by footer `2`, but PDF page 10 is a chapter divider with no footer. The build aborted on a correct PDF. | Detect the first page whose footer is `1`, then walk forward skipping unnumbered pages. |
| 2 | `_detect_page_map` | An unnumbered page (`None`) terminated the walk instead of being treated as a divider, so every chapter boundary ended the scan. | Unnumbered pages are recorded as dividers and the walk continues. |
| 3 | `_detect_page_map` | PDF 127 (a divider) carries a decorative "108" in the footer zone, which would have been accepted as printed page 108 and duplicated PDF 128. | A candidate is accepted only if the *next* page does not repeat the same number; PDF 128 repeats 108, so 127 is rejected. |
| 4 | `_extract_page_paragraphs` | The current subsection was reset to `None` at the start of every page, so body text continuing a subsection on the next page was mislabelled with the chapter instead of `5.C`, etc. | Chapter and subsection state are threaded across pages and returned. |
| 5 | `chunker.chunk_document` | A chapter heading immediately followed by a subsection heading produced a 2–7 word chunk (e.g. `6. Assessment`), which is useless for retrieval and violates the minimum size target. | Runs consisting only of heading paragraphs are skipped; the heading text is still carried by `section`. |
| 6 | `find_tables_report` | Table detection produced spurious 2×2 detections on divider pages (PDF 39, 84, 97, 127), polluting the manual checklist. | Front matter and divider pages are excluded from the table scan. |
| 7 | `extract_handbook` | PDF 8 (the chapter-1 divider) was reported as front matter, contradicting the protocol's page sets. | TOC divider pages inside the front-matter range are reclassified as dividers. |
| 8 | `validate_chunks.py` | Chunks below the 100-word target were reported as errors, but short chunks at page/section boundaries are allowed by the protocol. | Downgraded to warnings; only the maximum is an error. |
| 9 | `validate_chunks.py` | Field check compared key order, so a re-serialised file with the same five fields would fail. | Compares the field *set* and count. |

## 2. Properties verified, not just assumed

| Property | How it was verified |
|---|---|
| Printed pages form exactly 1…117 | `test_page_map_dimensions` |
| PDF→printed offset is not constant (8 → 20) | `test_page_map_spot_checks` |
| 13 divider pages excluded; front matter 1–7 | `test_dividers_are_excluded` |
| IDs unique | `test_chunk_ids_are_unique` + `validate_chunks.py` |
| Plan's worked example `sec5_C_001 = printed 33 / PDF 45` | `test_plan_example_chunk` |
| Every body page has at least one chunk | `test_every_body_page_has_a_chunk` |
| Deterministic output | `test_determinism` (two runs, identical IDs and text) |
| Chunk text is verbatim from its own page | `test_text_is_verbatim_from_its_page` |
| No duplicate chunk text | ad-hoc check: 0 duplicates |
| Word accounting | 36,166 words in page paragraphs vs 36,117 in chunks; the 49-word difference is the heading-only runs dropped in defect 5, whose text is retained in `section` |

## 3. Review findings deliberately **not** changed

1. **Page-bounded chunks produce 44 short chunks.** Merging across pages would
   raise the mean size but would make a citation point at only one of the two pages
   it covers. The plan explicitly prefers page-bounded chunks; the trade-off is
   documented rather than hidden.
2. **Tables are not restructured.** `find_tables()` mis-grids merged-cell tables
   (PDF 115, 128), so a markdown conversion would be worse than the flattened text
   in some cases. Kept as a manual-check item.
3. **Deeper headings (`i.`, `ii.`) are not promoted to `section`.** Doing so would
   change the label format the plan and Member 2 expect, for little retrieval gain.

## 4. Residual risks

| Risk | Mitigation |
|---|---|
| A different edition of the handbook breaks the font-size assumptions | The build fails loudly (`HandbookFormatError`) instead of producing wrong chunks; the page map is validated as a contiguous sequence. |
| The team's PDF has a different SHA-256 | `data/chunks_stats.json` records the hash; re-run the build and compare chunk counts before rebuilding the index. |
| Heading text lost when a heading sits alone on a page | Text is preserved in `section`; no regulatory content is lost (headings are labels, not rules). |
| Hard split of an over-long sentence | Only applies to a single sentence > 450 words, which does not occur in this handbook; the fallback exists so the size bound is never violated. |
| Bullet hierarchy flattened | Aesthetic/structural, not factual; the LLM still sees every item. |

## 5. Reproduce the review

```bash
HANDBOOK_PDF=/path/to/Student_Handbook_2026-27_English.pdf \
  python tests/test_member1_pipeline.py

python scripts/validate_chunks.py --pdf /path/to/Student_Handbook_2026-27_English.pdf
```

Expected: 10/10 tests pass and the validator prints `OK`.

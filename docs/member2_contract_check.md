# Reply to Member 2 — Stage 1 chunk contract review

**Re:** `docs/member2_stage1_protocol.md`, Stage 1 chunk contract
**From:** Member 1 (Handbook Processing & Data)
**Status:** Contract requirements satisfied. One caveat about how this was verified — see §0.
**Constraint respected:** Member 1 has not modified any Member 2 file.

---

## 0. Important caveat

Member 1 could not open `docs/member2_stage1_protocol.md` directly (repository
access was not available on the machine used to build the data). This review is
therefore against the contract as quoted in the team message:

> chunk_id, section, printed_page, pdf_page, and text; IDs unique and stable; PDF
> page numbers 1-based; each chunk retains its complete passage text.

If the file specifies anything beyond these five fields, stricter formats, or
different semantics, diff it against §1–§5 below and reply — nothing here is
hard-coded against an unseen file, so an adjustment is cheap.

---

## 1. Field-by-field confirmation

| Member 2 field | Provided by Member 1 | Type | Guarantee |
|---|---|---|---|
| `chunk_id` | yes | string | Unique in the whole file; stable across identical re-runs |
| `section` | yes | string | Non-empty; stable per section |
| `printed_page` | yes | integer | 1-based, range 1–117 |
| `pdf_page` | yes | integer | 1-based, range 1–137 |
| `text` | yes | string | Complete passage; non-empty; never truncated |

`data/chunks.jsonl` contains **exactly these five keys and nothing else**. Scores,
ranks and retrieval metadata are Member 2's to attach at query time; they are not
present in the file.

---

## 2. Uniqueness

**Yes.**

`chunk_id = {section_key}_{sequence:03d}`, where `section_key` is
`sec{n}` / `sec{n}_{letter}` / `app{n}` / `app{n}_{letter}` and `sequence` is a
per-key counter assigned in reading order.

Proof sketch: each chunk has exactly one section key; within a key the counter
strictly increases; keys come from the handbook's own chapter/subsection numbering,
which contains no duplicates. Therefore no two chunks share an ID.

`scripts/validate_chunks.py` enforces this on every build and fails the build on a
duplicate.

---

## 3. Stability

**Yes, under a stated definition.**

- Deterministic pipeline: no randomness, no timestamps, no reliance on filesystem
  ordering. Output is written in document order.
- Identical PDF + identical parameters ⇒ byte-identical `chunk_id` and `text`.
- Parameters that affect boundaries (`--max-words`, `--min-words`, de-hyphenation
  behaviour) are recorded in `data/chunks_stats.json` with the chunk count, so an
  index build can be tied to the exact chunk set it used.

What does **not** survive a parameter change: sequence numbers, because boundaries
move. This is unavoidable for any size-based chunker and is why the stats file
records the parameters. If Member 2's protocol requires IDs to be stable *across
parameter changes*, that requirement cannot be met by any chunker that re-segments
the text; the agreed mitigation is: rebuild the index and re-run the benchmark
whenever the parameters change.

---

## 4. PDF page numbers are 1-based

**Yes.** `pdf_page` is the 1-based position in the PDF file, i.e. the number the
viewer shows for page 1. `printed_page` is the number printed in the handbook
footer. Both are integers.

Note for Member 2: the PDF→printed offset is **not constant** (it grows from +8 to
+20 across the document, because of 13 unnumbered chapter divider pages). Do not
compute one from the other. Always read both fields from the chunk.

Also note: **`pdf_page` values are not contiguous.** Front matter (PDF 1–7) and the
13 divider pages (PDF 8, 10, 14, 18, 39, 49, 62, 67, 78, 82, 84, 97, 127) contain no
regulations and produce no chunks. A consumer that assumes `pdf_page` runs 1..N with
no gaps will break; one that reads the field will not.

---

## 5. Complete passage text

**Yes.** `text` is the full text of the paragraphs assigned to the chunk, joined
with blank lines. The chunker never truncates: an oversized paragraph is split on
sentence boundaries, never mid-sentence, and each resulting piece is itself a
complete passage.

The section heading line is included at the start of a section's text on the page
where the heading appears, so the chunk is self-describing. This means `text`
begins with the heading on the first chunk of a section; it is not duplicated
anywhere else.

`validate_chunks.py` additionally verifies that each chunk's text is a verbatim
(whitespace-normalised) substring of its own PDF page, which catches cross-page
leakage and accidental loss.

---

## 6. Edge cases Member 2 should know about

| Case | Behaviour | Action for Member 2 |
|---|---|---|
| Page contains the end of one section and the start of another | Two chunks on the same page, different `section` | Do not assume page ⇒ unique section |
| Section continues across pages | Same `section`, different pages | Group by `section` for filters |
| Page is a divider or front matter | No chunk | Handle missing `pdf_page` values |
| Table page | One or more chunks of flattened cell text | Do not rely on cell adjacency; see `data/table_pages.csv` |
| Very short section (e.g. `10. Notes for Students under 18 Years Old`, 1 page) | One short chunk below the target minimum | Allowed by design; do not merge across pages |
| Appendix section | `section` starts with `Appendix N` | Regex `^(sec|app)` if you parse the ID prefix |

---

## 7. Proposed additions (optional, not required by Member 2)

These are suggestions only; Member 1 will not add fields to `chunks.jsonl` without
agreement, because that would break the strict five-field contract.

1. **Document order is guaranteed.** Member 2 can sort by `(pdf_page, chunk_id)` and
   reconstruct the handbook, which is useful for neighbour expansion or
   context-window expansion during retrieval.
2. **Stable section grouping.** If Member 2 wants section-level filtering, use
   `section` directly; it is identical for every chunk of a section.
3. **Table awareness.** If Member 2 wants to down-weight or specially handle table
   pages, `data/table_pages.csv` gives the page list offline; it is not in the chunk
   file on purpose.

---

## 8. Open question for Member 2

If `docs/member2_stage1_protocol.md` requires any of the following, reply and we
will settle it before the index is built:

- a different `chunk_id` format (e.g. no section prefix, or a fixed-width hash);
- `section` without the chapter number, or only the letter;
- a `source` / `doc_id` field;
- chunk sizes outside the 400–700-token starting range;
- a requirement that IDs be stable across chunk-size parameter changes.

Otherwise, Member 1's output satisfies the contract as quoted, and the file
`data/chunks.jsonl` can be used as-is for the Stage 1 index.

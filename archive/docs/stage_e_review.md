# Stage E evaluation summary

**Date:** 2026-11-11 (Hong Kong). This summary replaces the earlier Stage E record of 2026-11-07 and reports the most recent full run.

**Status:** The project user confirmed on 2026-11-11 that the current 30-question set is the approved evaluation set. Results below are from one live run on that set. They were graded by Claude Code, not by an independent human reviewer, and they are small-sample observations, not release approval.

## Sources and question set

| Item | SHA-256 |
|---|---|
| `data/handbook.pdf` | `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464` |
| `data/chunks.jsonl` | `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3` |
| `data/stage_e_questions.json` (approved set) | `dc5e84aeece876735819a49d0da2474f9d731d49f1d90ad5eb01175eb0c0768e` |
| `data/stage_e_questions.md` | `d3a98f4c891c10c161ec9587050356d0ef8d9dbccde0ba776f848e4e51df40ea` |

The question file records the PDF and chunk hashes above, and they match the files on disk. Earlier records quoted a different question-file hash (`476790c7…`). The restored file differs from that version, and the user has approved the current file, so the hash above is the one of record. Any later edit to the file changes its hash and should be recorded here.

The set has 30 questions: 8 direct, 8 conditional, 5 multi-section, 4 follow-up and 5 unambiguous unsupported. Each answerable question lists its expected facts, acceptable chunk IDs and page numbers. The four follow-up cases use fixed, source-backed earlier turns. No deliberate ambiguity cases are included. The local, git-ignored files `data/stage_e_questions.md` and `data/stage_e_questions.json` hold the questions.

## Scoring rules

- **Evidence-item Recall@5:** for each answerable question, the fraction of required evidence items represented by an acceptable chunk in the actual top five, averaged over the 25 answerable questions. Unsupported questions have no recall denominator.
- **Correct:** the answer contains all requested facts and material qualifications and no incorrect claims.
- **Claims supported:** each factual claim is found in the cited passages (for answered cases).
- **Appropriate abstention:** an unsupported question returns `insufficient_evidence`, without an invented answer.

## Run conditions

- Real retriever and index: `handbook-index`, generation `1daf62406acf49ea83b4d1333de593a1`, built from the chunks above with `BAAI/bge-small-en-v1.5` at revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Model: `deepseek-flash` through the project's chat-completions client. Python 3.12.13.
- Code: commit `25e3c9b6e2403addbe2af6e0bce8c5e9ef468a96` with a clean working tree at the time of the run (no code was changed for this evaluation).
- Each question was asked once, with a fresh conversation except for the four fixed follow-up histories. Latency is the answer service plus network time, not browser rendering.
- Raw results (retrieved top five, queries, answers, timings) are kept locally and git-ignored in `data/presentation_eval_2026-11-11.jsonl`.

## Results (30 questions, one run)

| Measure | Result |
|---|---|
| Response status matched expectation | 30/30 (25 answered, 5 insufficient evidence) |
| Evidence-item Recall@5 | 25/25 = 100% |
| Correct answerable cases | 24/25 = 96% |
| Answered cases whose factual claims were all supported by the cited text | 25/25 |
| Appropriate abstention on unsupported cases | 5/5 |
| Errors | 0 |

By category: direct 8/8 correct, conditional 7/8, multi-section 5/5, follow-up 4/4.

**Latency:** the first (cold) query took 8.91 s. The median of the other 29 was 2.75 s, the 90th percentile of all 30 was 7.01 s, and the slowest was 10.54 s (M04, a two-topic comparison). These are single-run observations, not guarantees.

**The one incorrect case (C07):** the answer correctly says that failing a compulsory subject after two retakes leads to de-registration, but omits that departments may impose stricter requirements on the retaking of particular types of subjects. By the scoring rule, a missing material qualification means the answer is not fully correct. All statements it did make are supported by the cited passages.

**Repeat stability.** A separate sweep ran 35 candidate questions three times each with fresh conversations (8 direct, 8 conditional, 8 follow-up chains run as real two-turn chats, 11 unsupported), saved in `data/presentation_stability_sweep_2026-11-11.jsonl`. In all three runs, 33 of 35 returned the expected status, contained every required fact and cited an acceptable source; retrieval returned the same top five each time and only the wording changed. The two exceptions were C07, which again omitted the stricter-rules qualification, and a Wi-Fi password question, which was refused once and answered twice because the handbook does cover campus Wi-Fi. One further follow-up chain (leave of absence, then approval) returned a clarification question in one of three runs.

## Limitations

- **One run, graded by Claude Code.** Each answer was compared with the approved expected facts, and each factual claim was checked against the text of the cited passages (and, for neighbouring claims, adjacent passages). This was a text comparison. It did not re-check table layout or the PDF visually and is not an independent human review.
- **Not an independent estimate.** The retrieval and prompting code was tuned against this same 30-question set in earlier stages (the withdrawal-keyword handling in the retriever, and answer-prompt refinements), so these figures do not show how the system generalises to new questions.
- **Small and narrow.** The set covers a limited number of handbook sections, has only fixed follow-up histories, and has no deliberate ambiguity cases. The unsupported questions are clearly external or future facts.
- **Answers vary in wording** between runs and sometimes add extra supported detail. A valid citation ID and an evidence-only prompt do not guarantee that every claim is supported or complete.
- **Extraction limits.** The accepted limitation on possible undiscovered or imperfectly extracted tables remains. Check cited numbers and table relationships against the PDF.

## Open items carried forward

- **Answer service:** completeness of qualifications (C07) remains the known weak point. Stronger mitigation and retesting would be needed before any release claim.
- **Retrieval:** the withdrawal-keyword normalisation was validated only on this set and a few probes, not against ranking regressions in general.
- **Data:** keep checking cited numerical and table relationships against the PDF whenever evaluation cases are added.
- **Interface:** the interface cannot compensate for unsupported or incomplete model claims.
- Do not include `.env`, the PDF, virtual environments, indexes or these ignored evaluation files in commits. The user has confirmed that redistribution of the handbook and handbook-derived project files is acceptable. That is the user's confirmation, not an independent licence determination.

## Demo cases

The demo questions were chosen from the three-run stability sweep (see `presentation/PRESENTATION_PLAN.md`). Re-verify the live responses immediately before presenting.

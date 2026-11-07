# Integration protocol — PolyU regulations assistant

**Status:** Stages A–D have passed their integration gates with recorded limitations; Stage E evaluation is complete with grounding limitations accepted by the project user; the project user reports that independent teammate review is complete. See [Stage E review](stage_e_review.md).

**Working branch:** `codex/integration`, in the `GP-integration` worktree.
**Baseline:** merge commit `6d3ec6a`, incorporating the four member branches and retrieval commit `ae5892f`. This branch was local at the time of writing. Keep `main` stable and record subsequent integration commits and reviews.

## 1. Baseline and contracts

| Owner | Existing work | Boundary to integrate |
| --- | --- | --- |
| Member 1 — data | Extracts the handbook into page-bounded chunks and accompanying statistics, page map and table report. | `data/chunks.jsonl`: exactly `chunk_id`, `section`, `printed_page`, `pdf_page`, `text`. Both page numbers are 1-based. |
| Member 2 — retrieval | Hybrid sentence embeddings, ChromaDB, BM25 and reciprocal rank fusion. | `retrieve(query: str, top_k: int = 5)` returns ranked chunks with those five fields. Blank query returns `[]`; invalid `top_k` raises `ValueError`; index/model/search failures raise `RetrievalError`. |
| Member 3 — answer service | model provider client, history-aware search query, evidence prompting and citation ID validation. | `answer_question(question, history)` returns `answer`, `citation_chunk_ids`, `cited_chunks`, `clarification_question`, `status` and `evidence_source`. Status is `answered`, `needs_clarification`, `insufficient_evidence` or `error`. |
| Member 4 — interface | Streamlit chat, examples, session history and expandable citations. | The UI consumes `src.conversation.answer_question`; Stage D removed the language selector and mock backend import. |

The answer service already selects `src.retriever` by default. `RETRIEVAL_BACKEND=mock` explicitly selects the fictional mock retriever; setting an index path selects an index, not a retriever. `src/mock_backend.py`, `src/mock_retriever.py` and `data/sample_chunks.json` are development fixtures. Their contents are fictional and must never be presented as handbook rules. Retaining them for isolated tests is acceptable; they must not be on the normal user-facing path.

The integration project's code and interface should use English. During integration, translate Chinese comments, docstrings, developer messages and other code text into English, or remove them when obsolete. Remove the Chinese interface options and text as specified in Stage D. Preserve program behavior, public contracts and the meaning of useful explanations; do not alter handbook source data, quoted evidence, proper names or intentional test inputs merely to remove Chinese. Review any necessary exceptions explicitly.

The integration worktree tracks Member 1's `data/chunks.jsonl`, `data/chunks_stats.json`, `data/page_map.csv` and `data/table_pages.csv`, even though the general `data/*` ignore rule applies to untracked files. These contain handbook-derived material; confirm redistribution permission rather than assuming the ignore rule protects tracked files. The supplied PDF is now at the default path `data/handbook.pdf` and is ignored by Git; each developer must use an authorized copy. At this baseline the chunk file SHA-256 is `2729978a200ca6738a4a50e44d0f5778069400a339a4f6dcc8dd50644c73665c`; the local PDF SHA-256 is `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464`, matching the value recorded in the supplied statistics. A matching hash establishes identity, not correctness of every extracted table.

On 2026-11-07, running `../GP/.venv/bin/python -m pytest -q -rs` from the integration worktree produced **55 passed, 4 skipped, 8 subtests passed**, with five dependency deprecation warnings. The four PDF-dependent checks were skipped because `data/handbook.pdf` was absent at the time. After the PDF and dedicated environment were added, the Stage A Member 1 test command below was rerun with the PDF and produced **20 passed**, with five SWIG deprecation warnings. These component-test results are not evidence that the integrated application works or that Stage A's manual review is complete.

**Current approved data and Stage B (2026-11-07):** Stage A passed with an accepted table-coverage limitation. The approved PDF SHA-256 remains `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464`; the approved 186-chunk file now has SHA-256 `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`, superseding the historical baseline hash above. A fresh handbook index was built and the Stage B integration gate passed with a documented paraphrase miss; the benchmark and quality assessment remain pending. See [Stage A review](stage_a_review.md) and [Stage B review](stage_b_review.md) for provenance, results, and limitations.

**Stage C (2026-11-07):** The answer-service gate passed the recorded live and deterministic checks, with retrieval and table-coverage limitations carried forward. At the Stage C gate the Streamlit UI still used the mock backend; Stage D subsequently integrated the real service. See the [Stage C review](stage_c_review.md) for results and fixture-warning requirements.

**Stage D (2026-11-07):** The Streamlit interface is connected to the answer service and passed the recorded deterministic and live checks, with the existing limitations carried forward. A repeat live-browser check confirmed reset, which also passed in a real-service Streamlit test session and deterministic tests. See the [Stage D review](stage_d_review.md).

On 2026-11-07, a dedicated Python 3.12.13 environment was created at `GP-integration/.venv`, separate from `../GP/.venv`. The pinned requirements, including Streamlit 1.67.0, PyMuPDF 2.1 and pytest 9.2.0, were installed there, and `pip check` found no broken requirements. Activate it from the integration root with `source .venv/bin/activate`. During integration, test the runtime and test dependencies together and document a clean setup; a successful `pip check` alone does not establish reproducibility or integrated application behavior.

## 2. Stage A — validate the handbook data

**Prerequisites:** An authorized 2026/27 PDF; Member 1's tracked chunks and companion files; a Python environment with PyMuPDF and pytest. Check the working tree and preserve the current PDF and all existing data before any rebuild.

1. Record the PDF and chunk hashes and compare the PDF hash with `source_sha256` in `data/chunks_stats.json`. A mismatch requires identifying the intended edition and reviewing page mapping before proceeding.
2. Set `HANDBOOK_PDF` to the absolute path of the authorized PDF (the current default is `data/handbook.pdf`). From the integration root, with the required dependencies installed, run:

   ```sh
   shasum -a 256 "$HANDBOOK_PDF" data/chunks.jsonl
   python scripts/validate_chunks.py --chunks data/chunks.jsonl --pdf "$HANDBOOK_PDF"
   HANDBOOK_PDF="$HANDBOOK_PDF" python -m pytest -q -rs tests/test_member1_pipeline.py tests/test_member1_review_regressions.py
   ```

   Record actual results and warnings. Without `--pdf`, the validator explicitly skips page mapping, coverage and PDF text-integrity checks; this does not satisfy the gate.
3. Compare printed and PDF pages against the source, including divider boundaries. The offset is not constant. Review the still-unchecked entries in [Member 1's table checklist](member1_table_checklist.md), including numerical rules and tables where flattened text can lose relationships. Record each checked item, reviewer, source page, outcome and any defect; do not assume the checklist is complete.
4. If regeneration is needed, write to a new, separate temporary directory, not the tracked files. For example, with `CHECK_DIR` set to a newly created directory outside the worktree:

   ```sh
   python scripts/build_chunks.py --pdf "$HANDBOOK_PDF" --out "$CHECK_DIR/chunks.jsonl"
   python scripts/validate_chunks.py --chunks "$CHECK_DIR/chunks.jsonl" --pdf "$HANDBOOK_PDF"
   ```

   Companion files use the `chunks_` prefix in that directory. Compare hashes and differences with the supplied artifacts; review any intentional replacement as a separate change. Chunk boundaries or source changes can invalidate IDs, indexes and benchmark mappings.

**Expected / gate:** Schema, unique IDs, page mapping, coverage and text checks pass; manual table and numeric checks relevant to the evaluation are recorded, and unresolved items are visible. Stop before using affected evidence if the PDF identity, mapping, extraction or a critical table is wrong. Escalate unresolved broader table coverage rather than claiming it has been fully checked.

## 3. Stage B — connect validated data to retrieval

**Prerequisites:** Stage A's data gate; compatible retrieval dependencies; access to the candidate embedding model `BAAI/bge-small-en-v1.5`. First model download requires network access. Do not reuse or overwrite an existing index whose provenance is unknown.

1. Choose a new index directory outside the worktree, for example a fresh `$INDEX_DIR` created with `mktemp -d`; keep it for the duration of testing. Build and select the handbook index:

   ```sh
   python scripts/build_index.py --chunks data/chunks.jsonl --index-dir "$INDEX_DIR"
   export RETRIEVAL_INDEX_DIR="$INDEX_DIR"
   unset RETRIEVAL_BACKEND
   ```

   Record the index manifest's source path and SHA-256, model and immutable revision, generation, count, configuration and build date. The source path is absolute and must remain available and unchanged; moving or changing it requires a rebuild. If a nondefault model is chosen, set `RETRIEVAL_MODEL` consistently.
2. Test `src.retriever.retrieve` with manually verified direct questions, paraphrases and exact identifiers from the handbook. Record top-five IDs and ranks, sections, printed and PDF pages, and latency; inspect the returned full text against the PDF. Check blank input and limits. Verify missing, stale and incompatible index/model failures using disposable test paths or copies, not the active index.
3. Use a different directory for any sample index. Never promote it to the handbook index. Before running the real app, check `RETRIEVAL_INDEX_DIR` and `RETRIEVAL_BACKEND` in the process environment. Clear or replace any sample configuration explicitly.
4. Before reporting retrieval quality, agree the benchmark and scoring with the team. For each answerable question, predefine required evidence items and acceptable chunk IDs; for multi-section questions count each required item. A possible Recall@5 is the fraction of required items represented in the top five, averaged across answerable questions. Score unsupported cases separately. Record misses and limitations; synthetic smoke checks and ranking scores are not evidence of answer correctness.

**Expected / gate:** Manifest points to the validated handbook chunks; real retrieval returns contract-compliant, correctly paginated passages, and error cases fail explicitly without fictional fallback. Stop on stale or unverified sources, sample contamination, broken page mappings or unexplained index errors. Record retrieval evaluation as pending until completed and agreed.

## 4. Stage C — connect retrieval to answer generation

**Prerequisites:** Stage B handbook index and environment selected; an authorized model provider key in an ignored local `.env` or process environment, never in the protocol, repository or logs. The default model is `deepseek-flash`; configure alternatives explicitly and record the model used. Live calls can incur cost. The answer service's default is already real retrieval, so do not describe an import swap as a completed or necessary change here.

1. Run automated answer-service and retrieval tests using injected test doubles. Then exercise `src.conversation.answer_question` with the real selected index and live service, recording inputs, model, source/index identifiers and outcomes without recording credentials.
2. Check a straightforward answer and a conditional answer against the exact passages; confirm returned cited IDs belong to the retrieved set and `cited_chunks` retain complete text and both page numbers. A valid citation ID does **not** prove the passage supports every claim: manually check claim support.
3. Test a contextual follow-up, a clarification, unsupported or insufficient evidence, empty retrieval, malformed/unknown citations, and missing or stale index and API failure. Verify errors are distinct from insufficient evidence and that no answer falls back to fictional data or invented regulations.
4. Exercise fixture detection in isolated tests, including mixed fixture/handbook chunks. If a fixture is ever enabled in a development UI, ensure its warning is visible for every applicable status; the pre-Stage-D UI replaced the backend text for insufficient-evidence and error responses, so this could not be assumed. Inspect configuration explicitly: the retriever is selected before the model provider client loads `.env` on a first call, so process environment configuration must be established before startup.

**Expected / gate:** Answer-service outcomes and errors match the contract; real answers are grounded in verified handbook passages and fictional evidence cannot be mistaken for handbook evidence. Stop on unsupported claims, hidden fixture warnings, unhandled errors, or inability to reproduce the configured retrieval source.

## 5. Stage D — connect the Streamlit interface

**Prerequisites:** Stages B and C pass and Streamlit is installed in the selected environment. The agreed scope is English only. The pre-Stage-D UI had English, Simplified Chinese and Traditional Chinese labels and examples; remove the language selector and Chinese interface text during integration. Multilingual retrieval and answers are outside the current scope.

1. Replace the `src.mock_backend.answer_question` import in `app.py` with `src.conversation.answer_question`, retaining the agreed interface. Ensure normal startup selects the intended real handbook index and no mock backend. The UI must not independently call the retriever or model.
2. Render all four statuses appropriately. Preserve safe, actionable backend error information, distinguish insufficient evidence from infrastructure failure, and show fixture warnings where relevant without exposing credentials or sensitive details. Show complete cited chunk text with section, printed page and 1-based PDF page.
3. Verify the interface, example questions and normal service responses use English, and that the language selector is absent. Verify user and assistant history sent to the service matches what was displayed, including clarification turns; check reruns, multiple questions, example buttons, citations, and New Conversation clearing the session. Run the app locally with `streamlit run app.py` from the integration root, with environment variables set before startup. Check the real interaction as well as deterministic tests with injected responses.
4. Update the setup and usage documentation, including the English-only scope, dependency installation, index and `.env` setup, startup command, and troubleshooting. Remove stale claims that the project is only an initial structure or that a mock import is still required.
5. Review project source code, including embedded CSS, fixtures and tests, for Chinese comments, docstrings and messages. Translate useful text into English or remove obsolete text, and remove the Chinese UI content. Search for remaining Chinese characters and inspect matches individually, preserving only justified source material, proper names or intentional test inputs. Run affected tests after changes and record any exceptions.

**Expected / gate:** A local user can submit a question and see a real, grounded answer and complete citations; follow-ups, reset, status messages, errors and fixture warnings behave correctly. The interface and project code use English except for reviewed, justified exceptions. Stop if the UI masks a critical error, shows mock content as real, loses relevant history or silently misrepresents language support.

## 6. Stage E — integrated evaluation and handoff

**Prerequisites:** Stages A–D completed, a reviewed test set and a repeatable environment. Keep handbook-derived evaluation material local until redistribution permission is confirmed. All members participate in verification; module owners investigate failures in their areas.

1. Assemble and manually check 30 clearly worded questions: 8 direct factual, 8 conditional, 5 multi-section, 4 follow-up and 5 unsupported. This replaces the project plan’s unsupported-or-ambiguous category at the user’s request; do not use questions whose intended meaning is ambiguous. For each answerable case, record expected evidence and both page numbers; include context for follow-ups.
2. Record per-question retrieved IDs/ranks, evidence-item Recall@5 under the agreed definition, answer correctness, claim-by-claim citation support, correct abstention or clarification, latency and notes. Inspect numerical conditions and tables against the PDF. Report category results, failures, denominator and limitations; distinguish the plan's targets (≥90% Recall@5, ≥90% answer correctness, and an aim of 100% grounded citations and appropriate abstention) from observed results.
3. Fix and retest failures, rerunning affected automated and manual cases. Record the code commit, data and PDF hashes, embedding model/revision, index manifest, LLM model, dependency versions, environment, date and reviewer with results. Do not treat a successful API call or citation ID validation as proof of correctness.
4. From a clean environment, follow the updated setup instructions and rerun the full tests, the handbook-dependent checks, and representative end-to-end UI scenarios. Record skipped tests and reasons. Verify no keys, local indexes, environments or unauthorized PDF are included in changes; separately review redistribution permission for the already tracked handbook-derived data.
5. Record teammate review of interfaces and results, open issues and ownership, and select 2–3 demo cases only after evaluation. The project user reported the independent review complete on 2026-11-07; see the Stage E review. Follow the team's review and merge process; do not claim release readiness while critical gates remain unresolved.

**Completion gate:** The team can reproduce the validated data-to-retrieval-to-answer-to-UI flow; benchmark results and known limitations are documented; mock data is absent from the normal user-facing path; dependency setup and failure handling are verified; and outstanding permissions and review decisions are recorded.

## Reference documents

- [Project implementation plan](../PROJECT_IMPLEMENTATION_PLAN.md)
- [Member 1 preprocessing protocol](member1_protocol.md), [review](member1_self_review.md) and [table checklist](member1_table_checklist.md)
- [Member 2 retrieval protocol](member2_stage2_protocol.md), [evaluation protocol](member2_stage3_protocol.md) and [findings](member2_stage3_findings.md)
- [Stage A review](stage_a_review.md) and [Stage B review](stage_b_review.md)
- [Stage C review](stage_c_review.md) and [Stage D review](stage_d_review.md)
- [Member 3 answer-service contract](member3_stage1_protocol.md)

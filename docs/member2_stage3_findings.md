# Member 2 Stage 3: Verification and Review Findings

**Date:** 2026-11-07  
**Branch:** `feature/retrieval`  
**Scope:** Synthetic retrieval verification and handbook evaluation preparation; teammate confirmations and the handbook benchmark remain pending.

## Synthetic verification

In the project virtual environment, Python 3.12.13 successfully built the default index with `python scripts/build_index.py`. The input was `data/sample_chunks.json`, containing three fictional passages. `python -m unittest discover -s tests` passed all 8 tests. Integration tests use controlled embeddings; the following separate smoke test used the actual local model.

Model: `BAAI/bge-small-en-v1.5`  
Immutable model revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`

| Query | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| How can a student take a break from their studies? | `sample_leave_002` | `sample_retake_001` | `sample_leave_001` |
| ZX101 | `sample_leave_001` | `sample_leave_002` | `sample_retake_001` |

The exact identifier returned the target passage first. The temporary-leave application passage was third for the paraphrase, below an unrelated retake passage; the return-from-leave passage was first. This is a useful issue to revisit with real handbook questions, but three synthetic passages cannot establish retrieval quality, select the final model, or support real regulatory answers. No smoke-test error was observed.

## Synthetic latency spot check

On 2026-11-07, a fresh Python 3.12.13 process on an Apple M3 Mac (macOS 26.5.2) queried the existing local three-chunk fictional index using the model and revision above. The index and model were already available locally; no download or index build was included. Timing used `time.perf_counter()` around each `retrieve(..., top_k=5)` call, after importing the retriever. The first query was the temporary-leave paraphrase above; five subsequent calls alternated `ZX101` and that paraphrase.

| Call | Elapsed seconds |
|---|---:|
| First call in process (cold retriever) | 11.6396 |
| Subsequent calls (warm retriever) | 0.0166, 0.0104, 0.0113, 0.0092, 0.0111 |

All calls returned three fictional chunks. Cache statistics showed one load followed by five cache hits, so one successful warm-up call reused the loaded retriever for these subsequent queries in the same process with the same index configuration. A changed manifest, process restart, or cache eviction can require a reload. These are a single local spot check, not a benchmark or a prediction of latency for a larger handbook index or a different machine.

## Evaluation and handoff

Eight handbook-based candidate questions and an empty results template are in the local, Git-ignored `data/stage3_evaluation.md`. Their evidence and page mappings were checked against the local PDF. The proposed evidence-item Recall@5 rule is in the Stage 3 protocol and awaits team agreement. No handbook index, handbook retrieval score, or final model selection has been made.

The handoff to Members 1 and 3 has been completed, as reported by Member 2. Their confirmations are pending. Real-data evaluation requires Member 1's validated chunks; answer-service integration requires Member 3's readiness.

## Branch review

The tracked file list contains the synthetic fixture and code, not the handbook PDF, virtual environment, local Chroma index, or `.env` file. Git ignore checks cover the local handbook, default index, virtual environment, and local evaluation file. Other custom index paths must also be kept out of Git. The Stage 3 protocol and these findings are ready for teammate review; a teammate review and pull request remain to be completed under the project plan.

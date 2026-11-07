# Stage D Streamlit integration review

**Date:** 2026-11-07 (Hong Kong)  
**Reviewer:** Codex  
**Decision:** The Stage D gate passes for the checks recorded below. A repeat live-browser check confirmed that New Conversation clears messages and citations and restores the welcome screen. Reset also passed in deterministic tests and a separate real-service Streamlit test session. The Stage A table-coverage limitation and Stage B retrieval misses remain; the Stage E benchmark and integrated evaluation are pending.

## Configuration and provenance

The Stage C baseline was commit `2033eee`. The app was started from the integration root with Python 3.12.13, the project `.venv`, `RETRIEVAL_BACKEND=real`, `HF_HUB_OFFLINE=1` and `RETRIEVAL_INDEX_DIR=/private/tmp/gp-stage-b-index.pTotFHEc`; the model override was unset. The local `.env` contained the API key setting, and the default `deepseek-flash` model was used. No key or raw service error was recorded. The temporary index may be removed by the operating system.

The index manifest identified 186 chunks, generation `5d8469f9af98404396d5153ac7578419`, model `BAAI/bge-small-en-v1.5` at revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, and the approved absolute chunk source. The chunk SHA-256 was `4c9ba414555b6fd35a184088f8768cdd2d98fb296fbe7f4522f37704e4683bc3`; the PDF SHA-256 was `4fb771304c1d1ae17f2e2d1187b8878d2e0942966959eda1b3bfbbc48cf9a464`.

## Interface checks

- The live browser showed an English interface with no language selector. The failed-subject retake question returned an answer supported by the expanded full passage in Section 5.C, printed page 33 / PDF page 45. The answer's two-retake limit, conditions, procedure and final-attempt GPA statement matched the passage. A contextual follow-up correctly stated the maximum of two retakes and cited the same section.
- In a repeat live-browser session, a Medical Clinic question returned a real answer and citations, and New Conversation cleared the messages and citations and restored the welcome screen. An earlier browser automation attempt did not observe the reset; the repeat resolved that uncertainty without a code change. In a separate real-service Streamlit test session, the Medical Clinic question returned the telephone number and room with a citation to Section 12.D, printed page 101 / PDF page 120; New Conversation cleared the session. With a deliberately missing index, the same test session showed fixed handbook-search troubleshooting guidance and no unhandled exception. The active index was not modified.
- Injected Streamlit tests covered all four statuses, fixture warnings for each status, mixed fixture/handbook evidence and an API failure, sanitized error messages, complete citations, clarification and follow-up history, reruns, example submission, and reset. Stage C tests separately exercise service-level failures and mixed-evidence detection.
- The UI uses backend evidence-source metadata to display the fictional-data warning on every applicable status. The underlying fixture detector relies on the `sample_` chunk-ID convention and is not a general provenance classifier. UI error messages are fixed guidance rather than raw exception text.
- A search of project text files, including Python, fixtures, tests, embedded CSS and documentation, found no remaining Chinese characters; binary files, the local environment, caches and Git metadata were excluded. Handbook source data and quoted evidence were not changed for translation.

## Automated verification

The focused Streamlit suite passed: **9 passed**. With `HANDBOOK_PDF` set to the authorized local PDF, the full suite passed: **84 passed, 16 subtests passed**, with five SWIG deprecation warnings and no skips. These checks and the limited live examples do not establish benchmark quality or support for every generated claim.

# Testing

From the project root, activate the environment and run:

```sh
python -m pip check
HANDBOOK_PDF="$PWD/data/handbook.pdf" python -m pytest -q -rs
```

Tests requiring the handbook may be skipped when it is unavailable; check the reported skips. The suite covers extraction and reviewed table transformations, retrieval and index consistency, conversation responses, citations, and the Streamlit interface. Tests use test doubles and temporary files, so they do not require live DeepSeek requests.

For manual review, run the app with the real handbook index and ask representative questions, including follow-ups and questions with insufficient evidence. Compare every claim and cited passage with the relevant PDF page, including table layout, conditions, and printed/PDF page numbers. A valid citation ID alone does not establish that the answer is correct or complete. Live model calls may incur charges.

See [Data and indexing](data-and-indexing.md) for candidate extraction and validation without replacing active artifacts.

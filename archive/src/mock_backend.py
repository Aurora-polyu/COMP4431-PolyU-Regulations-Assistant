# src/mock_backend.py

_MOCK_CHUNKS = [
    {
        "chunk_id": "sec5_C_001",
        "section": "5.C Retaking of Failed Subjects",
        "printed_page": 33,
        "pdf_page": 45,
        "text": (
            "MOCK TEXT: A student who fails a subject in an assessment may, "
            "subject to the conditions in this section, retake the subject in a "
            "subsequent semester. The grade obtained shall be recorded in the "
            "student's academic record."
        ),
    },
    {
        "chunk_id": "sec3_A_007",
        "section": "3.A Add/Drop Period",
        "printed_page": 12,
        "pdf_page": 20,
        "text": (
            "MOCK TEXT: Students may add or drop subjects during the first two "
            "weeks of each semester, as specified in the Academic Calendar."
        ),
    },
]


def answer_question(question, history):
    """Return fictional responses for isolated interface development tests."""
    q = question.lower()

    if "error" in q:
        return {
            "answer": "",
            "citation_chunk_ids": [],
            "cited_chunks": [],
            "clarification_question": None,
            "status": "error",
        }

    if "clarify" in q:
        return {
            "answer": "",
            "citation_chunk_ids": [],
            "cited_chunks": [],
            "clarification_question": (
                "Could you clarify whether you are asking about undergraduate "
                "or taught postgraduate programmes?"
            ),
            "status": "needs_clarification",
        }

    if "xyz" in q or "nonsense" in q:
        return {
            "answer": "",
            "citation_chunk_ids": [],
            "cited_chunks": [],
            "clarification_question": None,
            "status": "insufficient_evidence",
        }

    return {
        "answer": (
            "MOCK ANSWER: Based on the Student Handbook, you may retake a failed "
            "subject in a subsequent semester, and the grade is recorded in your "
            "academic record. Please confirm the exact conditions with the cited "
            "sections below."
        ),
        "citation_chunk_ids": ["sec5_C_001", "sec3_A_007"],
        "cited_chunks": _MOCK_CHUNKS,
        "clarification_question": None,
        "status": "answered",
    }

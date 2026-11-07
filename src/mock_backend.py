# src/mock_backend.py
# Member 4 专用:Member 3 的 answer_question() 没做完之前,先用这个假后端开发 UI。
# 字段名必须和 PROJECT_IMPLEMENTATION_PLAN.md 第 3 节约定的 ChatResponse 完全一致,
# 这样以后把 import 换成真函数时,UI 代码一行都不用改。

# 假引用原文(expandable 展开时显示)
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
    """假回答:根据问题关键词返回四种不同状态,方便你把 UI 每个分支都测一遍。

    真函数由 Member 3 提供,签名相同:
        answer_question(question: str, history: list[dict]) -> ChatResponse
    """
    q = question.lower()

    # 测试"错误"分支:问题里带 error
    if "error" in q:
        return {
            "answer": "",
            "citation_chunk_ids": [],
            "cited_chunks": [],
            "clarification_question": None,
            "status": "error",
        }

    # 测试"需要澄清"分支:问题里带 clarify
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

    # 测试"证据不足"分支:问题里带 xyz 或 nonsense
    if "xyz" in q or "nonsense" in q:
        return {
            "answer": "",
            "citation_chunk_ids": [],
            "cited_chunks": [],
            "clarification_question": None,
            "status": "insufficient_evidence",
        }

    # 默认:正常回答,带两条假引用
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

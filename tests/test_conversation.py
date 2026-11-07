import json
import unittest

from src.conversation import NO_EVIDENCE_ANSWER, answer_question
from src.llm_client import LlmError

CHUNKS = [
    {
        "chunk_id": "sec5_C_001",
        "section": "5.C Retaking of Failed Subjects",
        "printed_page": 33,
        "pdf_page": 45,
        "text": "A student who fails a subject may retake it subject to programme requirements.",
    },
    {
        "chunk_id": "sec5_D_002",
        "section": "5.D Withdrawal from Study",
        "printed_page": 34,
        "pdf_page": 46,
        "text": "Withdrawal applications are considered by the programme leader.",
    },
]

FIXTURE = [
    {
        "chunk_id": "sample_leave_001",
        "section": "Fictional A.1 Temporary Leave",
        "printed_page": 10,
        "pdf_page": 15,
        "text": "Fictional passage that must never be presented as a regulation.",
    }
]


def model_answer(ids=("sec5_C_001",), answer="You may retake the subject.", clarification=None):
    return json.dumps(
        {
            "answer": answer,
            "status": "needs_clarification" if clarification else "answered",
            "citation_ids": list(ids),
            "clarification_question": clarification,
        }
    )


class FakeLlm:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, messages, **_kwargs):
        self.calls.append(messages)
        if not self.replies:
            raise AssertionError("model called more times than scripted")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def fake_retriever(chunks=None, error=None):
    calls = []

    def retrieve(query, top_k=5):
        calls.append((query, top_k))
        if error is not None:
            raise error
        return list(chunks or [])[:top_k]

    retrieve.calls = calls
    return retrieve


class AnswerServiceTests(unittest.TestCase):
    def test_formatted_answer_survives_json_parsing(self):
        answer = (
            "Here are the relevant rules. [sec5_C_001]\n\n"
            "- A failed subject may be retaken. [sec5_C_001]\n"
            "- Programme requirements apply. [sec5_C_001]\n\n"
            "Check your programme requirements. [sec5_C_001]"
        )
        llm = FakeLlm(model_answer(answer=answer))
        result = answer_question("What are the retake rules?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["answer"], answer)
        self.assertEqual(result["citation_chunk_ids"], ["sec5_C_001"])

    def test_answered_with_validated_citations(self):
        llm = FakeLlm(model_answer())
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["citation_chunk_ids"], ["sec5_C_001"])
        self.assertEqual(result["cited_chunks"][0]["text"], CHUNKS[0]["text"])
        self.assertIsNone(result["clarification_question"])
        self.assertEqual(result["evidence_source"], "handbook")

    def test_unknown_citation_is_dropped(self):
        llm = FakeLlm(model_answer(ids=["sec5_C_001", "invented_999"]))
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["citation_chunk_ids"], ["sec5_C_001"])

    def test_answer_without_valid_citation_is_not_answered(self):
        llm = FakeLlm(model_answer(ids=["invented_999"]))
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["answer"], NO_EVIDENCE_ANSWER)
        self.assertEqual(result["citation_chunk_ids"], [])

    def test_model_declared_insufficient_evidence_strips_citations(self):
        reply = json.dumps(
            {
                "answer": "The provided handbook does not cover tuition fees.",
                "status": "insufficient_evidence",
                "citation_ids": ["sec5_C_001"],
                "clarification_question": None,
            }
        )
        result = answer_question("What is the tuition fee?", retrieve=fake_retriever(CHUNKS), llm=FakeLlm(reply))
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["citation_chunk_ids"], [])
        self.assertEqual(result["cited_chunks"], [])
        self.assertEqual(result["answer"], NO_EVIDENCE_ANSWER)

    def test_insufficient_evidence_does_not_leak_model_claims(self):
        reply = json.dumps({"status": "insufficient_evidence", "answer": "Uncited fee: $500."})
        result = answer_question("What is the fee?", retrieve=fake_retriever(CHUNKS), llm=FakeLlm(reply))
        self.assertEqual(result["answer"], NO_EVIDENCE_ANSWER)
        self.assertEqual(result["citation_chunk_ids"], [])

    def test_empty_retrieval_skips_model(self):
        llm = FakeLlm()
        result = answer_question("Anything?", retrieve=fake_retriever([]), llm=llm)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(llm.calls, [])

    def test_retrieval_failure_is_an_error_not_an_answer(self):
        llm = FakeLlm()
        result = answer_question(
            "Can I retake a failed subject?",
            retrieve=fake_retriever(error=RuntimeError("index missing")),
            llm=llm,
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Retrieval failed", result["answer"])
        self.assertIn("build_index.py", result["answer"])
        self.assertEqual(result["citation_chunk_ids"], [])
        self.assertEqual(llm.calls, [])

    def test_fixture_evidence_is_flagged(self):
        llm = FakeLlm(model_answer(ids=["sample_leave_001"], answer="Submit form ZX101."))
        result = answer_question("How do I take leave?", retrieve=fake_retriever(FIXTURE), llm=llm)
        self.assertEqual(result["evidence_source"], "fixture")
        self.assertIn("Development data", result["answer"])
        self.assertIn("Submit form ZX101.", result["answer"])

    def test_clarification_status(self):
        llm = FakeLlm(model_answer(ids=[], answer="", clarification="Which programme are you in?"))
        result = answer_question("What are the rules?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["clarification_question"], "Which programme are you in?")

    def test_clarification_does_not_leak_uncited_answer(self):
        llm = FakeLlm(
            model_answer(
                ids=[],
                answer="The deadline is 31 March and the fee is 500 dollars.",
                clarification="Which programme are you in?",
            )
        )
        result = answer_question("What are the rules?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["answer"], "")
        self.assertEqual(result["citation_chunk_ids"], [])

    def test_mixed_fixture_evidence_is_flagged(self):
        llm = FakeLlm(model_answer(ids=["sec5_C_001"], answer="Submit form ZX101."))
        result = answer_question(
            "How do I take leave?", retrieve=fake_retriever([*CHUNKS, *FIXTURE]), llm=llm
        )
        self.assertEqual(result["evidence_source"], "fixture")
        self.assertIn("Development data", result["answer"])

    def test_fixture_warning_on_every_post_retrieval_status(self):
        scenarios = [
            ("needs_clarification", FakeLlm(model_answer(ids=[], answer="", clarification="Which case?"))),
            ("insufficient_evidence", FakeLlm(model_answer(ids=["unknown"]))),
            ("insufficient_evidence", FakeLlm(json.dumps({"status": "insufficient_evidence"}))),
            ("error", FakeLlm(LlmError("API failure"))),
            ("error", FakeLlm("invalid", "still invalid")),
        ]
        for expected_status, llm in scenarios:
            with self.subTest(status=expected_status, llm=llm):
                result = answer_question("Question?", retrieve=fake_retriever([*CHUNKS, *FIXTURE]), llm=llm)
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["evidence_source"], "fixture")
                self.assertIn("Development data", result["answer"])

    def test_retrieval_value_error_returns_error_status(self):
        result = answer_question(
            "Can I retake a failed subject?",
            retrieve=fake_retriever(error=ValueError("top_k must be positive")),
            llm=FakeLlm(),
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Retrieval failed", result["answer"])

    def test_malformed_json_is_retried_once(self):
        llm = FakeLlm("not json at all", model_answer())
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(llm.calls), 2)

    def test_malformed_json_twice_is_reported_as_error(self):
        llm = FakeLlm("nope", "still nope")
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "error")
        self.assertNotIn("does not appear to cover", result["answer"])

    def test_invalid_model_status_is_an_error(self):
        for reply in ('{}', '{"status": "needs_clarification"}', '{"status": []}'):
            with self.subTest(reply=reply):
                result = answer_question("Question?", retrieve=fake_retriever(CHUNKS), llm=FakeLlm(reply))
                self.assertEqual(result["status"], "error")

    def test_model_error_returns_error_status(self):
        llm = FakeLlm(LlmError("Model provider returned HTTP 401"))
        result = answer_question("Can I retake a failed subject?", retrieve=fake_retriever(CHUNKS), llm=llm)
        self.assertEqual(result["status"], "error")
        self.assertIn("401", result["answer"])

    def test_follow_up_rewrites_retrieval_query(self):
        history = [
            {"role": "user", "content": "I failed a subject last semester."},
            {"role": "assistant", "content": "You may be able to retake it."},
        ]
        llm = FakeLlm("can a student retake a failed subject", model_answer())
        retriever = fake_retriever(CHUNKS)
        result = answer_question("Can I do that?", history=history, retrieve=retriever, llm=llm)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(retriever.calls[0][0], "can a student retake a failed subject")
        self.assertEqual(retriever.calls[0][1], 5)

    def test_rewrite_failure_falls_back_to_history(self):
        history = [{"role": "user", "content": "I failed a subject last semester."}]
        llm = FakeLlm(LlmError("network down"), model_answer())
        retriever = fake_retriever(CHUNKS)
        answer_question("Can I retake it?", history=history, retrieve=retriever, llm=llm)
        self.assertIn("I failed a subject last semester.", retriever.calls[0][0])
        self.assertIn("Can I retake it?", retriever.calls[0][0])

    def test_blank_question_is_rejected(self):
        with self.assertRaises(ValueError):
            answer_question("   ", retrieve=fake_retriever(CHUNKS), llm=FakeLlm())

    def test_top_k_is_passed_to_retriever(self):
        llm = FakeLlm(model_answer())
        retriever = fake_retriever(CHUNKS)
        answer_question("Can I retake a failed subject?", retrieve=retriever, llm=llm, top_k=3)
        self.assertEqual(retriever.calls[0][1], 3)


if __name__ == "__main__":
    unittest.main()

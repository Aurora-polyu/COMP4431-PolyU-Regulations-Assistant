import unittest

from src.citations import format_evidence, is_fixture, validate_citations

CHUNK_A = {
    "chunk_id": "sec5_C_001",
    "section": "5.C Retaking of Failed Subjects",
    "printed_page": 33,
    "pdf_page": 45,
    "text": "A student who fails a subject may retake it subject to programme requirements.",
}
CHUNK_B = {
    "chunk_id": "sec5_D_002",
    "section": "5.D Withdrawal from Study",
    "printed_page": 34,
    "pdf_page": 46,
    "text": "Withdrawal applications are considered by the programme leader.",
}


class CitationTests(unittest.TestCase):
    def test_keeps_only_retrieved_ids_in_order(self):
        ids, chunks = validate_citations(["sec5_D_002", "sec5_C_001"], [CHUNK_A, CHUNK_B])
        self.assertEqual(ids, ["sec5_D_002", "sec5_C_001"])
        self.assertEqual([chunk["chunk_id"] for chunk in chunks], ids)

    def test_drops_unknown_duplicate_and_malformed_ids(self):
        ids, chunks = validate_citations(
            ["[sec5_C_001]", "sec5_C_001", "invented_001", 42, None, " 'sec5_D_002' "],
            [CHUNK_A, CHUNK_B],
        )
        self.assertEqual(ids, ["sec5_C_001", "sec5_D_002"])
        self.assertEqual(len(chunks), 2)

    def test_returns_full_chunk_text(self):
        _, chunks = validate_citations(["sec5_C_001"], [CHUNK_A, CHUNK_B])
        self.assertEqual(chunks[0]["text"], CHUNK_A["text"])
        self.assertEqual(chunks[0]["printed_page"], 33)

    def test_rejects_non_list(self):
        self.assertEqual(validate_citations(None, [CHUNK_A]), ([], []))
        self.assertEqual(validate_citations("sec5_C_001", [CHUNK_A]), ([], []))

    def test_evidence_block_has_id_section_and_page(self):
        block = format_evidence([CHUNK_A])
        self.assertIn("sec5_C_001", block)
        self.assertIn("5.C Retaking of Failed Subjects", block)
        self.assertIn("printed page 33", block)
        self.assertIn(CHUNK_A["text"], block)

    def test_fixture_detection(self):
        fixture = [{"chunk_id": "sample_leave_001"}]
        self.assertTrue(is_fixture(fixture))
        self.assertFalse(is_fixture([CHUNK_A]))
        self.assertFalse(is_fixture([]))
        self.assertFalse(is_fixture([CHUNK_A, {"chunk_id": "sample_leave_001"}]))


if __name__ == "__main__":
    unittest.main()

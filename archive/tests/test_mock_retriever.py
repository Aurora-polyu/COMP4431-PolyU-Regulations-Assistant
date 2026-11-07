import unittest

from src.mock_retriever import retrieve


class MockRetrieverTests(unittest.TestCase):
    def test_fixture_contract(self):
        chunks = retrieve("example", top_k=100)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(len({chunk["chunk_id"] for chunk in chunks}), len(chunks))
        for chunk in chunks:
            self.assertEqual(set(chunk), {"chunk_id", "section", "printed_page", "pdf_page", "text"})
            for field in ("chunk_id", "section", "text"):
                self.assertIsInstance(chunk[field], str)
                self.assertTrue(chunk[field].strip())
            for field in ("printed_page", "pdf_page"):
                self.assertIs(type(chunk[field]), int)
                self.assertGreater(chunk[field], 0)

    def test_fixed_order_and_limit(self):
        self.assertEqual(retrieve("first", 2), retrieve("different", 2))
        self.assertEqual(len(retrieve("example", 2)), 2)
        self.assertEqual(retrieve("example", 1), retrieve("example", 2)[:1])

    def test_blank_and_invalid_limit(self):
        self.assertEqual(retrieve(" \n "), [])
        for top_k in (0, -1):
            with self.subTest(top_k=top_k), self.assertRaises(ValueError):
                retrieve("", top_k)


if __name__ == "__main__":
    unittest.main()

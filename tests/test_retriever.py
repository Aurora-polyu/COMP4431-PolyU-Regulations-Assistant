import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from scripts.build_index import build_index
from src.retriever import RetrievalError, _load, retrieve, rrf, tokenize, validate_chunks

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "sample_chunks.json"


class FakeModel:
    def __init__(self, revision="a" * 40):
        self.revision = revision

    def _first_module(self):
        return SimpleNamespace(auto_model=SimpleNamespace(config=SimpleNamespace(_commit_hash=self.revision)))

    def encode(self, texts, normalize_embeddings=True):
        return np.array([[1.0, 0.1] if "leave" in t.lower() or "zx101" in t.lower() else [0.1, 1.0] for t in texts])


class UnitTests(unittest.TestCase):
    def test_validation(self):
        chunks = json.loads(FIXTURE.read_text())
        self.assertEqual(validate_chunks(chunks), chunks)
        for invalid in ([], [chunks[0], chunks[0]], [dict(chunks[0], printed_page=True)],
                        [dict(chunks[0], text=" ")], [dict(chunks[0], pdf_page=0)], [{}]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_chunks(invalid)

    def test_tokenize_and_fusion(self):
        self.assertEqual(tokenize("Use ZX101, or AR160!"), ["use", "zx101", "or", "ar160"])
        self.assertEqual(rrf([["b", "a", "a"], ["a", "b"]], 3), ["a", "b"])
        self.assertEqual(rrf([["b"], ["a"]], 2), ["a", "b"])

    def test_early_contract(self):
        self.assertEqual(retrieve(" \n"), [])
        with self.assertRaises(ValueError):
            retrieve("", 0)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"RETRIEVAL_INDEX_DIR": directory}):
            with self.assertRaisesRegex(RetrievalError, "Rebuild"):
                retrieve("question")


class IntegrationTests(unittest.TestCase):
    def test_build_reload_search_stale_and_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "chunks.json", root / "index"
            chunks = json.loads(FIXTURE.read_text())
            source.write_text(json.dumps(chunks))
            with patch("scripts.build_index.load_model", return_value=FakeModel()), \
                 patch("src.retriever.load_model", return_value=FakeModel()) as loader, \
                 patch.dict(os.environ, {"RETRIEVAL_INDEX_DIR": str(index), "RETRIEVAL_MODEL": "test-model"}):
                build_index(source, index, "test-model")
                _load.cache_clear()
                manifest = json.loads((index / "manifest.json").read_text())
                self.assertEqual(manifest["model_revision"], "a" * 40)
                results = retrieve("ZX101", 10)
                loader.assert_called_once_with("test-model", local_only=True, revision="a" * 40)
                self.assertEqual(len(results), 3)
                self.assertEqual(results[0], chunks[0])
                self.assertEqual(len({c["chunk_id"] for c in results}), 3)
                self.assertEqual(len(retrieve("leave", 1)), 1)
                _load.cache_clear()
                loader.return_value = FakeModel("b" * 40)
                with self.assertRaisesRegex(RetrievalError, "revision differs"):
                    retrieve("leave")
                loader.return_value = FakeModel()
                with patch.dict(os.environ, {"RETRIEVAL_MODEL": "wrong"}):
                    with self.assertRaisesRegex(RetrievalError, "incompatible"):
                        retrieve("leave")
                source.write_text(json.dumps(chunks[1:]))
                with self.assertRaisesRegex(RetrievalError, "changed"):
                    retrieve("leave")
                build_index(source, index, "test-model")
                self.assertEqual({c["chunk_id"] for c in retrieve("leave", 10)}, {c["chunk_id"] for c in chunks[1:]})
                _load.cache_clear()

    def test_bm25_common_identifier_prefers_more_occurrences(self):
        from src.retriever import HybridRetriever
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "chunks.json", root / "index"
            chunks = [dict(chunk_id=str(i), section="Example", printed_page=1, pdf_page=1,
                           text=" ".join(["ZX101"] * n)) for i, n in enumerate((5, 1, 1))]
            source.write_text(json.dumps(chunks))
            with patch("scripts.build_index.load_model", return_value=FakeModel()), \
                 patch("src.retriever.load_model", return_value=FakeModel()):
                build_index(source, index, "test-model")
                retriever = HybridRetriever(index, json.loads((index / "manifest.json").read_text()))
                scores = retriever.bm25.get_scores(["zx101"])
                self.assertGreater(scores[0], scores[1])


if __name__ == "__main__":
    unittest.main()

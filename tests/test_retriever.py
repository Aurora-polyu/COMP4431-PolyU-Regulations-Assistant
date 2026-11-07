import json
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from scripts.build_index import build_index, parse_chunks
from src.retriever import DEFAULT_INDEX, RetrievalError, _load, _manifest, file_hash, retrieve, rrf, tokenize, validate_chunks

FIXTURE = None
_fixture_directory = None
_fixture_hash_patch = None


def setUpModule():
    global FIXTURE, _fixture_directory, _fixture_hash_patch
    _fixture_directory = tempfile.TemporaryDirectory()
    FIXTURE = Path(_fixture_directory.name) / "retrieval_test.json"
    chunks = [
        {"chunk_id": "sample_001", "section": "Example", "printed_page": 1, "pdf_page": 1, "text": "ZX101 leave example."},
        {"chunk_id": "sample_002", "section": "Example", "printed_page": 2, "pdf_page": 2, "text": "A different test passage."},
        {"chunk_id": "sample_003", "section": "Example", "printed_page": 3, "pdf_page": 3, "text": "Another test passage."},
    ]
    FIXTURE.write_text(json.dumps(chunks))
    _fixture_hash_patch = patch("src.retriever.FICTIONAL_SAMPLE_SHA256", file_hash(FIXTURE))
    _fixture_hash_patch.start()


def tearDownModule():
    _fixture_hash_patch.stop()
    _fixture_directory.cleanup()


class FakeModel:
    def __init__(self, revision="a" * 40):
        self.revision = revision

    def _first_module(self):
        return SimpleNamespace(auto_model=SimpleNamespace(config=SimpleNamespace(_commit_hash=self.revision)))

    def encode(self, texts, normalize_embeddings=True):
        return np.array([[1.0, 0.1] if "leave" in t.lower() or "zx101" in t.lower() else [0.1, 1.0] for t in texts])


class UnitTests(unittest.TestCase):
    def test_jsonl_validation_and_errors(self):
        chunks = json.loads(FIXTURE.read_text())
        source = Path("chunks.jsonl")
        raw = ("\n" + "\n".join(json.dumps(c) for c in chunks) + "\n").encode()
        self.assertEqual(parse_chunks(raw, source), chunks)
        with self.assertRaisesRegex(ValueError, "line 3"):
            parse_chunks(b'{}\n\ninvalid\n', source)
        with self.assertRaisesRegex(ValueError, "Duplicate chunk_id"):
            parse_chunks((json.dumps(chunks[0]) + "\n" + json.dumps(chunks[0])).encode(), source)

    def test_cli_rejects_missing_source(self):
        script = Path(__file__).resolve().parents[1] / "scripts/build_index.py"
        env = dict(os.environ)
        env.pop("RETRIEVAL_INDEX_DIR", None)
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.jsonl"
            index = Path(directory) / "index"
            result = subprocess.run([sys.executable, str(script), "--chunks", str(missing), "--index-dir", str(index)], capture_output=True, text=True, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Prepare the handbook chunks", result.stderr)
            self.assertFalse(index.exists())

    def test_missing_default_does_not_publish_an_index(self):
        from scripts.build_index import main
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "index"
            stderr = io.StringIO()
            with patch("scripts.build_index.ROOT", root), \
                 patch.object(sys, "argv", ["build_index.py"]), \
                 patch.dict(os.environ, {"RETRIEVAL_INDEX_DIR": str(index)}), \
                 redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
                main()
            self.assertNotEqual(exc.exception.code, 0)
            self.assertIn("Prepare the handbook chunks", stderr.getvalue())
            self.assertFalse(index.exists())

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
    def test_jsonl_build_search_and_stale_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "chunks.jsonl", root / "index"
            chunks = json.loads(FIXTURE.read_text())
            source.write_text("\n".join(json.dumps(c) for c in chunks) + "\n", encoding="utf-8")
            with patch("scripts.build_index.load_model", return_value=FakeModel()), \
                 patch("src.retriever.load_model", return_value=FakeModel()), \
                 patch.dict(os.environ, {"RETRIEVAL_INDEX_DIR": str(index), "RETRIEVAL_MODEL": "test-model"}):
                build_index(source, index, "test-model")
                self.assertEqual(retrieve("ZX101", 3)[0], chunks[0])
                source.write_text(source.read_text() + "\n", encoding="utf-8")
                with self.assertRaisesRegex(RetrievalError, "changed"):
                    retrieve("ZX101")
                _load.cache_clear()

    def test_existing_sample_default_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory)
            other_checkout = index / "other-checkout-sample.json"
            other_checkout.write_bytes(FIXTURE.read_bytes())
            manifest = {"format_version": 2, "model": "test-model", "query_prefix": "Represent this sentence for searching relevant passages: ", "source_path": str(other_checkout), "source_sha256": file_hash(other_checkout)}
            (index / "manifest.json").write_text(json.dumps(manifest))
            with patch("src.retriever.DEFAULT_INDEX", index):
                with self.assertRaisesRegex(RetrievalError, "fictional sample"):
                    _manifest(index, "test-model")

    def test_sample_cannot_replace_custom_handbook_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "other-checkout-sample.json", root / "custom-index"
            source.write_bytes(FIXTURE.read_bytes())
            index.mkdir()
            manifest_path = index / "manifest.json"
            original = json.dumps({"source_sha256": "a" * 64})
            manifest_path.write_text(original)
            with patch("scripts.build_index.load_model") as load:
                with self.assertRaisesRegex(ValueError, "cannot replace"):
                    build_index(source, index, "test-model")
                load.assert_not_called()
            self.assertEqual(manifest_path.read_text(), original)

    def test_sample_can_rebuild_its_own_index(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "sample-index"
            with patch("scripts.build_index.load_model", return_value=FakeModel()):
                build_index(FIXTURE, index, "test-model")
                first = json.loads((index / "manifest.json").read_text())
                build_index(FIXTURE, index, "test-model")
                second = json.loads((index / "manifest.json").read_text())
            self.assertNotEqual(first["generation"], second["generation"])

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
                loader.assert_called_once()
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

    def test_withdraw_query_matches_withdrawal_passage(self):
        from src.retriever import HybridRetriever
        from rank_bm25 import BM25Plus
        retriever = HybridRetriever.__new__(HybridRetriever)
        retriever.ids = ["programme", "unrelated"]
        retriever.chunks = {
            "programme": {"chunk_id": "programme", "section": "Example", "printed_page": 1,
                          "pdf_page": 1, "text": "Official withdrawal from a programme"},
            "unrelated": {"chunk_id": "unrelated", "section": "Example", "printed_page": 1,
                          "pdf_page": 1, "text": "Information about the campus"},
        }
        retriever.tokens = [tokenize(retriever.chunks[i]["text"]) for i in retriever.ids]
        retriever.bm25 = BM25Plus(retriever.tokens)
        retriever.model = FakeModel()
        retriever.collection = SimpleNamespace(query=lambda **kw: {"ids": [["unrelated", "programme"]]})
        self.assertEqual(retriever.search("How do I withdraw from my programme?", 2)[0]["chunk_id"], "programme")


if __name__ == "__main__":
    unittest.main()

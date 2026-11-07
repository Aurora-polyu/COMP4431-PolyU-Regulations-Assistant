import subprocess
import os
from unittest.mock import patch
import sys
import unittest

from src import contracts, retriever


class ContractTests(unittest.TestCase):
    def test_shared_types_and_compatible_imports(self):
        self.assertIs(retriever.RetrievedChunk, contracts.RetrievedChunk)
        self.assertIs(retriever.RetrievalError, contracts.RetrievalError)

    def test_contracts_import_without_site_packages(self):
        result = subprocess.run(
            [sys.executable, "-S", "-c",
             "from src.contracts import RetrievedChunk, RetrievalError"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_retriever_ignores_old_mock_setting(self):
        from src.conversation import _default_retriever
        with patch.dict(os.environ, {"RETRIEVAL_BACKEND": "mock"}):
            self.assertIs(_default_retriever(), retriever.retrieve)

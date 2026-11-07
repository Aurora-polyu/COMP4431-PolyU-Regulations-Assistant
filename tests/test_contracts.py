import subprocess
import sys
import unittest

from src import contracts, mock_retriever, retriever


class ContractTests(unittest.TestCase):
    def test_shared_types_and_compatible_imports(self):
        self.assertIs(mock_retriever.RetrievedChunk, contracts.RetrievedChunk)
        self.assertIs(retriever.RetrievedChunk, contracts.RetrievedChunk)
        self.assertIs(retriever.RetrievalError, contracts.RetrievalError)

    def test_contracts_import_without_site_packages(self):
        result = subprocess.run(
            [sys.executable, "-S", "-c",
             "from src.contracts import RetrievedChunk, RetrievalError"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

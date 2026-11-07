import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from src.llm_client import ModelClient, LlmError, load_env_file


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def http_error(code: int, message: str) -> urllib.error.HTTPError:
    body = f'{{"error": {{"message": "{message}"}}}}'.encode()
    return urllib.error.HTTPError(
        "https://example.com/chat/completions", code, message, {}, io.BytesIO(body)
    )


OK_BODY = b'{"choices": [{"message": {"content": "hello"}}]}'


class ClientTests(unittest.TestCase):
    def test_model_configuration_uses_generic_environment_variables(self):
        settings = {"MODEL_API_KEY": "test-key", "MODEL_BASE_URL": "https://example.com/", "MODEL_NAME": "test-model"}
        with patch.dict(os.environ, settings, clear=True), patch("src.llm_client.load_env_file"):
            client = ModelClient()
        self.assertEqual((client.api_key, client.base_url, client.model), ("test-key", "https://example.com", "test-model"))

    def test_missing_key_is_reported(self):
        with patch.dict(os.environ, {}, clear=True), patch("src.llm_client.load_env_file"):
            with self.assertRaises(LlmError) as ctx:
                ModelClient()
        self.assertIn("MODEL_API_KEY", str(ctx.exception))

    def test_successful_completion(self):
        with patch("src.llm_client.urllib.request.urlopen", return_value=FakeResponse(OK_BODY)) as call:
            client = ModelClient(api_key="test-key")
            self.assertEqual(client.complete([{"role": "user", "content": "hi"}]), "hello")
        self.assertEqual(call.call_count, 1)

    def test_auth_error_does_not_retry(self):
        error = http_error(401, "invalid key")
        with patch("src.llm_client.urllib.request.urlopen", side_effect=error) as call, patch(
            "src.llm_client.time.sleep"
        ):
            client = ModelClient(api_key="bad-key")
            with self.assertRaises(LlmError) as ctx:
                client.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(call.call_count, 1)
        self.assertIn("401", str(ctx.exception))

    def test_server_error_retries_once_then_fails(self):
        with patch(
            "src.llm_client.urllib.request.urlopen", side_effect=[http_error(500, "boom"), http_error(500, "boom")]
        ) as call, patch("src.llm_client.time.sleep"):
            client = ModelClient(api_key="test-key")
            with self.assertRaises(LlmError):
                client.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(call.call_count, 2)

    def test_connection_reset_is_wrapped(self):
        with patch("src.llm_client.urllib.request.urlopen", side_effect=ConnectionResetError("reset")) as call, patch(
            "src.llm_client.time.sleep"
        ):
            client = ModelClient(api_key="test-key")
            with self.assertRaises(LlmError):
                client.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(call.call_count, 2)

    def test_empty_content_is_rejected(self):
        body = b'{"choices": [{"message": {"content": "   "}}]}'
        with patch("src.llm_client.urllib.request.urlopen", return_value=FakeResponse(body)):
            client = ModelClient(api_key="test-key")
            with self.assertRaises(LlmError):
                client.complete([{"role": "user", "content": "hi"}])

    def test_env_file_is_loaded_without_overriding(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text('MODEL_API_KEY="from-file"\n# comment\nBADLINE\n', encoding="utf-8")
            with patch.dict(os.environ, {"MODEL_KEEP": "existing"}, clear=True):
                load_env_file(env_file)
                self.assertEqual(os.environ["MODEL_API_KEY"], "from-file")
                self.assertEqual(os.environ["MODEL_KEEP"], "existing")


if __name__ == "__main__":
    unittest.main()

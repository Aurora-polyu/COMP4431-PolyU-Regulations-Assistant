"""Minimal DeepSeek chat client used by the answer service.

The key is read from the local .env file or the environment. It is never
written to code, logs or the repository.
"""

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_TIMEOUT = 60


class LlmError(RuntimeError):
    """The language model is unavailable, misconfigured, or returned an error."""


def load_env_file(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from .env without overriding existing variables."""
    env_path = path or ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip("\"'"))


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        load_env_file()
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = (
            base_url or os.environ.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = model or os.environ.get("DEEPSEEK_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        if not self.api_key:
            raise LlmError(
                "DEEPSEEK_API_KEY is not set. Create a local .env file with "
                "DEEPSEEK_API_KEY=<your key> and restart the app."
            )

    def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 1500,
        temperature: float = 0.0,
    ) -> str:
        """Return the assistant message content for the given chat messages.

        The budget covers reasoning tokens as well, because deepseek-v4-pro
        thinks before it writes; too small a value returns empty content.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        last_error: Exception | None = None
        for attempt in range(2):
            if attempt:
                time.sleep(1.5)
            try:
                body = self._post(payload)
                return self._content(body)
            except LlmError as exc:
                last_error = exc
                if not getattr(exc, "retryable", False):
                    raise
        raise LlmError(str(last_error))

    def _post(self, payload: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = self._error_detail(exc)
            error = LlmError(f"DeepSeek returned HTTP {exc.code}: {detail}")
            error.retryable = exc.code >= 500 or exc.code == 429
            raise error from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise LlmError("DeepSeek returned a response that is not valid JSON") from exc
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
            error = LlmError(f"Could not reach DeepSeek at {self.base_url}: {exc}")
            error.retryable = True
            raise error from exc

    @staticmethod
    def _error_detail(exc: urllib.error.HTTPError) -> str:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            return str(body.get("error", {}).get("message") or body)
        except Exception:
            return exc.reason or "no details"

    @staticmethod
    def _content(body: dict) -> str:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("DeepSeek response did not contain an assistant message") from exc
        if not isinstance(content, str) or not content.strip():
            raise LlmError("DeepSeek returned an empty answer")
        return content

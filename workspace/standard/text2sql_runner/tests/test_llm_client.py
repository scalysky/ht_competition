from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import unittest
from unittest.mock import patch

from workspace.standard.text2sql_runner.llm_client import (
    LlmConfig,
    LlmRequestError,
    OpenAICompatibleClient,
)


class _ResponseServer(ThreadingHTTPServer):
    def __init__(self, responses: list[tuple[int, dict[str, object]]]):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []


class _Handler(BaseHTTPRequestHandler):
    server: _ResponseServer

    def do_POST(self) -> None:  # noqa: N802 - HTTP handler API
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.requests.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "payload": payload,
            }
        )
        status, body = self.server.responses.pop(0)
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def response_server(responses: list[tuple[int, dict[str, object]]]):
    server = _ResponseServer(responses)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def config_for(server: _ResponseServer) -> LlmConfig:
    return LlmConfig(
        base_url=f"http://127.0.0.1:{server.server_port}/v1/",
        api_key="test-key",
        model="test-model",
        timeout_seconds=5.0,
    )


class LlmConfigTests(unittest.TestCase):
    def test_from_env_requires_all_model_settings(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "LLM_BASE_URL"):
                LlmConfig.from_env()

    def test_config_repr_does_not_expose_api_key(self) -> None:
        config = LlmConfig("https://example.test/v1", "very-secret", "model", 10)
        self.assertNotIn("very-secret", repr(config))


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_complete_posts_openai_compatible_request(self) -> None:
        response = {"choices": [{"message": {"content": "SELECT 1"}}]}
        with response_server([(200, response)]) as server:
            client = OpenAICompatibleClient(config_for(server))

            content = client.complete([{"role": "user", "content": "question"}])

        self.assertEqual(content, "SELECT 1")
        self.assertEqual(
            server.requests,
            [
                {
                    "path": "/v1/chat/completions",
                    "authorization": "Bearer test-key",
                    "payload": {
                        "model": "test-model",
                        "messages": [{"role": "user", "content": "question"}],
                        "temperature": 0,
                        "stream": False,
                    },
                }
            ],
        )

    def test_http_429_retries_then_returns_content(self) -> None:
        success = {"choices": [{"message": {"content": "SELECT 2"}}]}
        with response_server([(429, {"error": "busy"}), (200, success)]) as server:
            client = OpenAICompatibleClient(config_for(server))
            with patch("time.sleep", return_value=None):
                content = client.complete([{"role": "user", "content": "q"}])

        self.assertEqual(content, "SELECT 2")
        self.assertEqual(len(server.requests), 2)

    def test_http_400_is_not_retried_or_leak_key(self) -> None:
        with response_server([(400, {"error": "bad request"})]) as server:
            client = OpenAICompatibleClient(config_for(server))
            with self.assertRaises(LlmRequestError) as raised:
                client.complete([{"role": "user", "content": "q"}])

        self.assertEqual(len(server.requests), 1)
        self.assertNotIn("test-key", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

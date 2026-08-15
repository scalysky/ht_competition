from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LlmRequestError(RuntimeError):
    """模型接口请求失败或返回了无法解析的响应。"""


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str = field(repr=False)
    model: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "LlmConfig":
        required = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f".env 缺少必填项: {', '.join(missing)}")
        try:
            timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        except ValueError as exc:
            raise RuntimeError("LLM_TIMEOUT_SECONDS 必须是数字") from exc
        if timeout <= 0:
            raise RuntimeError("LLM_TIMEOUT_SECONDS 必须大于 0")
        return cls(
            base_url=os.environ["LLM_BASE_URL"].strip(),
            api_key=os.environ["LLM_API_KEY"],
            model=os.environ["LLM_MODEL"].strip(),
            timeout_seconds=timeout,
        )


class OpenAICompatibleClient:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config
        base = config.base_url.rstrip("/")
        self.endpoint = (
            base if base.endswith("/chat/completions") else base + "/chat/completions"
        )

    def _safe_message(self, message: str) -> str:
        return message.replace(self.config.api_key, "***")

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps(
            {
                "model": self.config.model,
                "messages": messages,
                "temperature": 0,
                "stream": False,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        response_body: bytes | None = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.config.timeout_seconds) as response:
                    response_body = response.read()
                break
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if retryable and attempt < 2:
                    time.sleep(attempt + 1)
                    continue
                detail = self._safe_message(body[:500])
                raise LlmRequestError(
                    f"模型接口返回 HTTP {exc.code}: {detail}"
                ) from exc
            except (URLError, TimeoutError, socket.timeout) as exc:
                if attempt < 2:
                    time.sleep(attempt + 1)
                    continue
                detail = self._safe_message(str(exc))
                raise LlmRequestError(f"模型接口请求失败: {detail}") from exc

        if response_body is None:
            raise LlmRequestError("模型接口未返回响应")
        try:
            decoded: Any = json.loads(response_body.decode("utf-8"))
            content = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LlmRequestError("模型接口响应格式无效") from exc
        if not isinstance(content, str):
            raise LlmRequestError("模型接口响应缺少文本内容")
        return content

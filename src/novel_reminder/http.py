from __future__ import annotations

import json
import ssl
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class HttpClient:
    def __init__(
        self,
        timeout: int = 20,
        retry_count: int = 3,
        retry_backoff_seconds: float = 1.5,
    ) -> None:
        self.timeout = timeout
        self.retry_count = max(1, retry_count)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self._ssl_context = ssl.create_default_context()

    def get_text(self, url: str) -> str:
        def send() -> str:
            request = Request(url, headers=DEFAULT_HEADERS)
            with urlopen(
                request, timeout=self.timeout, context=self._ssl_context
            ) as response:
                return response.read().decode("utf-8", errors="ignore")

        return self._with_retries(send, url)

    def post_json(self, url: str, payload: dict[str, Any]) -> str:
        def send() -> str:
            body = json.dumps(payload).encode("utf-8")
            headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}
            request = Request(url, data=body, headers=headers, method="POST")
            with urlopen(
                request, timeout=self.timeout, context=self._ssl_context
            ) as response:
                return response.read().decode("utf-8", errors="ignore")

        return self._with_retries(send, url)

    def _with_retries(self, operation: Any, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                return operation()
            except HTTPError as exc:
                last_error = RuntimeError(f"HTTP {exc.code} for {url}")
                if 400 <= exc.code < 500 and exc.code not in {408, 429}:
                    raise last_error from exc
            except (URLError, TimeoutError) as exc:
                reason = exc.reason if isinstance(exc, URLError) else str(exc)
                last_error = RuntimeError(f"Request failed for {url}: {reason}")

            if attempt < self.retry_count and self.retry_backoff_seconds > 0:
                time.sleep(self.retry_backoff_seconds * attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Request failed for {url}: unknown error")

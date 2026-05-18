from __future__ import annotations

import json
import ssl
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
    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self._ssl_context = ssl.create_default_context()

    def get_text(self, url: str) -> str:
        request = Request(url, headers=DEFAULT_HEADERS)
        try:
            with urlopen(
                request, timeout=self.timeout, context=self._ssl_context
            ) as response:
                return response.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except URLError as exc:
            raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc

    def post_json(self, url: str, payload: dict[str, Any]) -> str:
        body = json.dumps(payload).encode("utf-8")
        headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(
                request, timeout=self.timeout, context=self._ssl_context
            ) as response:
                return response.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except URLError as exc:
            raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc

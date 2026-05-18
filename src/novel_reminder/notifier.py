from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any
from urllib.parse import quote_plus

from .http import HttpClient
from .models import LatestChapter


class DingTalkNotifier:
    def __init__(
        self,
        http_client: HttpClient,
        webhook: str,
        secret: str | None = None,
    ) -> None:
        self.http_client = http_client
        self.webhook = webhook
        self.secret = secret

    def send_update(self, chapter: LatestChapter) -> dict[str, Any]:
        payload = {
            "msgtype": "text",
            "text": {
                "content": self._build_message(chapter),
            },
        }
        response = self.http_client.post_json(self._signed_webhook(), payload)
        return json.loads(response)

    def _build_message(self, chapter: LatestChapter) -> str:
        return (
            f"小说更新提醒\n"
            f"来源：{chapter.site}\n"
            f"小说：{chapter.novel_name}\n"
            f"章节：{chapter.chapter_title}\n"
            f"更新时间：{chapter.update_time_text}\n"
            f"章节链接：{chapter.chapter_url}\n"
            f"检测时间：{chapter.fetched_at}"
        )

    def _signed_webhook(self) -> str:
        if not self.secret:
            return self.webhook
        import time

        timestamp = str(round(time.time() * 1000))
        sign_value = f"{timestamp}\n{self.secret}".encode("utf-8")
        signature = hmac.new(
            self.secret.encode("utf-8"),
            sign_value,
            digestmod=hashlib.sha256,
        ).digest()
        encoded = quote_plus(base64.b64encode(signature))
        separator = "&" if "?" in self.webhook else "?"
        return f"{self.webhook}{separator}timestamp={timestamp}&sign={encoded}"

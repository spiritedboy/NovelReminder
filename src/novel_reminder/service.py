from __future__ import annotations

import logging
from datetime import datetime, timezone

from .config import Settings, load_novels_config
from .crawlers import build_crawler
from .http import HttpClient
from .models import LatestChapter, StoredState
from .notifier import DingTalkNotifier
from .storage import StateStore


LOGGER = logging.getLogger(__name__)


class NovelReminderService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.novels = load_novels_config(settings.novels_path)
        self.novels_by_id = {novel.novel_id: novel for novel in self.novels}
        self.http_client = HttpClient(
            timeout=settings.http_timeout_seconds,
            retry_count=settings.http_retry_count,
            retry_backoff_seconds=settings.http_retry_backoff_seconds,
        )
        self.store = StateStore(settings.database_path)
        self.notifier = DingTalkNotifier(
            self.http_client,
            settings.dingtalk_webhook,
            settings.dingtalk_secret,
        )

    def run_once(self) -> None:
        for novel in self.novels:
            self._process_novel(novel.novel_id)

    def list_states(self) -> list[dict[str, str | None]]:
        return self.store.list_states()

    def _process_novel(self, novel_id: str) -> None:
        novel = self.novels_by_id[novel_id]
        crawler = build_crawler(novel, self.http_client)
        state = self.store.get_state(novel_id)

        try:
            latest = crawler.fetch_latest()
            should_notify = self._should_notify(state, latest)
            notified_at = None
            if should_notify:
                self._ensure_webhook_configured()
                response = self.notifier.send_update(latest)
                if response.get("errcode") != 0:
                    raise RuntimeError(f"DingTalk returned error: {response}")
                notified_at = _now_iso()
                LOGGER.info(
                    "Notified update for %s: %s",
                    latest.novel_name,
                    latest.chapter_title,
                )
            self.store.upsert_state(
                novel_id=latest.novel_id,
                chapter_title=latest.chapter_title,
                chapter_url=latest.chapter_url,
                update_time_text=latest.update_time_text,
                last_checked_at=latest.fetched_at,
                last_notified_at=notified_at,
                last_status="ok",
                last_error=None,
            )
            if not should_notify:
                LOGGER.info(
                    "No new chapter for %s, latest=%s",
                    latest.novel_name,
                    latest.chapter_title,
                )
        except Exception as exc:
            checked_at = _now_iso()
            self.store.upsert_state(
                novel_id=novel.novel_id,
                chapter_title=state.chapter_title if state else "",
                chapter_url=state.chapter_url if state else novel.detail_url,
                update_time_text=state.update_time_text if state else "",
                last_checked_at=checked_at,
                last_notified_at=None,
                last_status="error",
                last_error=str(exc),
            )
            LOGGER.exception("Failed to process %s: %s", novel.novel_name, exc)

    def _should_notify(
        self, state: StoredState | None, latest: LatestChapter
    ) -> bool:
        if state is None:
            return self.settings.notify_on_first_seen
        if latest.chapter_url != state.chapter_url:
            return True
        if latest.chapter_title != state.chapter_title:
            return True
        if latest.update_time_text != state.update_time_text:
            return True
        return False

    def _ensure_webhook_configured(self) -> None:
        if self.settings.dingtalk_webhook:
            return
        raise RuntimeError("NOVEL_REMINDER_DINGTALK_WEBHOOK is not configured")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

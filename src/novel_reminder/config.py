from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class NovelConfig:
    novel_id: str
    novel_name: str
    site: str
    detail_url: str


@dataclass(frozen=True)
class Settings:
    dingtalk_webhook: str
    dingtalk_secret: str | None
    database_path: Path
    novels_path: Path
    http_timeout_seconds: int
    http_retry_count: int
    http_retry_backoff_seconds: float
    interval_seconds: int
    notify_on_first_seen: bool
    log_level: int


DEFAULT_NOVELS = [
    NovelConfig(
        novel_id="zongheng_408586",
        novel_name="逆天邪神",
        site="zongheng",
        detail_url="https://www.zongheng.com/detail/408586",
    ),
    NovelConfig(
        novel_id="fanqie_7503984033022364734",
        novel_name="公主太恶劣？抱紧她大腿后真香！",
        site="fanqie",
        detail_url="https://fanqienovel.com/page/7503984033022364734",
    ),
]


def load_novels_config(path: Path) -> list[NovelConfig]:
    if not path.exists():
        return list(DEFAULT_NOVELS)
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, list):
        raise ValueError("Novels config must be a JSON array")

    novels: list[NovelConfig] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Novel entry #{index} must be an object")
        novel = NovelConfig(
            novel_id=_required_text(item, "novel_id", index),
            novel_name=_required_text(item, "novel_name", index),
            site=_required_text(item, "site", index),
            detail_url=_required_text(item, "detail_url", index),
        )
        if novel.novel_id in seen_ids:
            raise ValueError(f"Duplicate novel_id in config: {novel.novel_id}")
        seen_ids.add(novel.novel_id)
        novels.append(novel)

    if not novels:
        raise ValueError("Novels config must contain at least one novel")
    return novels


def _required_text(item: dict[str, object], field_name: str, index: int) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Novel entry #{index} field '{field_name}' must be a non-empty string"
        )
    return value.strip()


def load_settings() -> Settings:
    load_env_file()
    level_name = os.getenv("NOVEL_REMINDER_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, level_name, logging.INFO)
    webhook = os.getenv("NOVEL_REMINDER_DINGTALK_WEBHOOK", "").strip()
    database_path = Path(
        os.getenv("NOVEL_REMINDER_DATABASE_PATH", "data/state.db").strip()
    )
    novels_path = Path(
        os.getenv("NOVEL_REMINDER_NOVELS_PATH", "config/novels.json").strip()
    )
    return Settings(
        dingtalk_webhook=webhook,
        dingtalk_secret=os.getenv("NOVEL_REMINDER_DINGTALK_SECRET") or None,
        database_path=database_path,
        novels_path=novels_path,
        http_timeout_seconds=_read_int("NOVEL_REMINDER_HTTP_TIMEOUT_SECONDS", 20),
        http_retry_count=_read_int("NOVEL_REMINDER_HTTP_RETRY_COUNT", 3),
        http_retry_backoff_seconds=float(
            os.getenv("NOVEL_REMINDER_HTTP_RETRY_BACKOFF_SECONDS", "1.5")
        ),
        interval_seconds=_read_int("NOVEL_REMINDER_INTERVAL_SECONDS", 300),
        notify_on_first_seen=_read_bool(
            "NOVEL_REMINDER_NOTIFY_ON_FIRST_SEEN", False
        ),
        log_level=log_level,
    )

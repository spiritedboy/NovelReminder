from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatestChapter:
    novel_id: str
    novel_name: str
    site: str
    source_url: str
    chapter_title: str
    chapter_url: str
    update_time_text: str
    fetched_at: str


@dataclass(frozen=True)
class StoredState:
    chapter_title: str
    chapter_url: str
    update_time_text: str

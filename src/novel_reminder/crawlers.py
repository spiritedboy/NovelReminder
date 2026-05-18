from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from urllib.parse import urljoin

from .config import NovelConfig
from .http import HttpClient
from .models import LatestChapter


class BaseCrawler(ABC):
    def __init__(self, novel: NovelConfig, http_client: HttpClient) -> None:
        self.novel = novel
        self.http_client = http_client

    @abstractmethod
    def fetch_latest(self) -> LatestChapter:
        raise NotImplementedError

    def _fetched_at(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class ZonghengCrawler(BaseCrawler):
    _pattern = re.compile(
        r"最新章节：\s*<a[^>]+href=\"(?P<href>//read\.zongheng\.com/chapter/[^\"]+)\"[^>]*>"
        r"(?P<title>[^<]+)</a>.*?(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
        re.S,
    )

    def fetch_latest(self) -> LatestChapter:
        html = _prepare_html(self.http_client.get_text(self.novel.detail_url))
        match = self._pattern.search(html)
        if match is None:
            raise RuntimeError(f"Could not parse latest chapter from {self.novel.detail_url}")
        href = match.group("href").strip()
        chapter_url = urljoin("https://www.zongheng.com/", href)
        return LatestChapter(
            novel_id=self.novel.novel_id,
            novel_name=self.novel.novel_name,
            site=self.novel.site,
            source_url=self.novel.detail_url,
            chapter_title=_clean_text(match.group("title")),
            chapter_url=chapter_url,
            update_time_text=match.group("time").strip(),
            fetched_at=self._fetched_at(),
        )


class FanqieCrawler(BaseCrawler):
    _section_pattern = re.compile(
        r"<div class=\"info-last\">(?P<section>.*?)</div>",
        re.S,
    )
    _href_pattern = re.compile(
        r"<a[^>]+href=\"(?P<href>/reader/[^\"]+)\"",
    )
    _title_pattern = re.compile(
        r"<span class=\"info-last-title\">最近更新：(?P<title>.*?)</span>",
        re.S,
    )
    _time_pattern = re.compile(
        r"<span class=\"info-last-time\">(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})</span>"
    )

    def fetch_latest(self) -> LatestChapter:
        html = _prepare_html(self.http_client.get_text(self.novel.detail_url))
        section_match = self._section_pattern.search(html)
        if section_match is None:
            raise RuntimeError(f"Could not parse latest chapter from {self.novel.detail_url}")
        section = section_match.group("section")
        href_match = self._href_pattern.search(section)
        title_match = self._title_pattern.search(section)
        time_match = self._time_pattern.search(section)
        if href_match is None or title_match is None or time_match is None:
            raise RuntimeError(f"Could not parse latest chapter from {self.novel.detail_url}")
        chapter_url = urljoin("https://fanqienovel.com", href_match.group("href").strip())
        return LatestChapter(
            novel_id=self.novel.novel_id,
            novel_name=self.novel.novel_name,
            site=self.novel.site,
            source_url=self.novel.detail_url,
            chapter_title=_strip_tags(title_match.group("title")),
            chapter_url=chapter_url,
            update_time_text=time_match.group("time").strip(),
            fetched_at=self._fetched_at(),
        )


def build_crawler(novel: NovelConfig, http_client: HttpClient) -> BaseCrawler:
    if novel.site == "zongheng":
        return ZonghengCrawler(novel, http_client)
    if novel.site == "fanqie":
        return FanqieCrawler(novel, http_client)
    raise ValueError(f"Unsupported site: {novel.site}")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _prepare_html(html: str) -> str:
    without_comments = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return without_comments.replace("\n", " ")


def _strip_tags(value: str) -> str:
    return _clean_text(re.sub(r"<[^>]+>", "", value))

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import StoredState


class StateStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS novel_state (
                    novel_id TEXT PRIMARY KEY,
                    chapter_title TEXT NOT NULL,
                    chapter_url TEXT NOT NULL,
                    update_time_text TEXT NOT NULL,
                    last_checked_at TEXT NOT NULL,
                    last_notified_at TEXT,
                    last_status TEXT NOT NULL,
                    last_error TEXT
                )
                """
            )

    def get_state(self, novel_id: str) -> StoredState | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT chapter_title, chapter_url, update_time_text
                FROM novel_state
                WHERE novel_id = ?
                """,
                (novel_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredState(
            chapter_title=row[0],
            chapter_url=row[1],
            update_time_text=row[2],
        )

    def upsert_state(
        self,
        novel_id: str,
        chapter_title: str,
        chapter_url: str,
        update_time_text: str,
        last_checked_at: str,
        last_notified_at: str | None,
        last_status: str,
        last_error: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO novel_state (
                    novel_id,
                    chapter_title,
                    chapter_url,
                    update_time_text,
                    last_checked_at,
                    last_notified_at,
                    last_status,
                    last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(novel_id) DO UPDATE SET
                    chapter_title = excluded.chapter_title,
                    chapter_url = excluded.chapter_url,
                    update_time_text = excluded.update_time_text,
                    last_checked_at = excluded.last_checked_at,
                    last_notified_at = excluded.last_notified_at,
                    last_status = excluded.last_status,
                    last_error = excluded.last_error
                """,
                (
                    novel_id,
                    chapter_title,
                    chapter_url,
                    update_time_text,
                    last_checked_at,
                    last_notified_at,
                    last_status,
                    last_error,
                ),
            )

    def list_states(self) -> list[dict[str, str | None]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    novel_id,
                    chapter_title,
                    chapter_url,
                    update_time_text,
                    last_checked_at,
                    last_notified_at,
                    last_status,
                    last_error
                FROM novel_state
                ORDER BY novel_id
                """
            ).fetchall()
        return [
            {
                "novel_id": row[0],
                "chapter_title": row[1],
                "chapter_url": row[2],
                "update_time_text": row[3],
                "last_checked_at": row[4],
                "last_notified_at": row[5],
                "last_status": row[6],
                "last_error": row[7],
            }
            for row in rows
        ]

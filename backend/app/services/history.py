"""
Phase 10: SQLite Download History
"""
from __future__ import annotations
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import json

from app.core.config import settings

logger = logging.getLogger("areebfetch.history")

DB_PATH = settings.DATA_DIR / "history.db"


class HistoryService:
    def __init__(self):
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self):
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail TEXT,
                    format TEXT,
                    quality TEXT,
                    status TEXT NOT NULL,
                    filename TEXT,
                    filesize INTEGER,
                    type TEXT DEFAULT 'video',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_title ON history(title)")
            conn.commit()

    def add(
        self,
        title: str,
        url: str,
        status: str = "completed",
        thumbnail: Optional[str] = None,
        format: Optional[str] = None,
        quality: Optional[str] = None,
        filename: Optional[str] = None,
        filesize: Optional[int] = None,
        type: str = "video",
        job_id: Optional[str] = None,
    ) -> str:
        entry_id = job_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO history
                   (id, title, url, thumbnail, format, quality, status, filename, filesize, type, created_at, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (entry_id, title, url, thumbnail, format, quality, status, filename, filesize, type, now, now if status == "completed" else None),
            )
            conn.commit()
        return entry_id

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM history WHERE 1=1"
        params: list = []
        if search:
            query += " AND (title LIKE ? OR url LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM history WHERE id = ?", (entry_id,)).fetchone()
            return dict(row) if row else None

    def delete(self, entry_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM history")
            conn.commit()
            return cur.rowcount

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]


history_service = HistoryService()
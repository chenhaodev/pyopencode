import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".pyopencode" / "sessions.db"


class SessionStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH))
        self._init_db()

    def _init_db(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_path TEXT,
                created_at TEXT,
                updated_at TEXT,
                messages TEXT,
                summary TEXT
            )
            """
        )
        self.conn.commit()

    def save(
        self,
        session_id: str,
        project_path: str,
        messages: list[dict],
        summary: str = "",
    ):
        now = datetime.now().isoformat()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO sessions
                (id, project_path, created_at, updated_at, messages, summary)
            VALUES (
                ?,
                ?,
                COALESCE((SELECT created_at FROM sessions WHERE id = ?), ?),
                ?,
                ?,
                ?
            )
            """,
            (
                session_id,
                project_path,
                session_id,
                now,
                now,
                json.dumps(messages, ensure_ascii=False),
                summary,
            ),
        )
        self.conn.commit()

    def load_latest(self, project_path: str) -> list[dict] | None:
        cursor = self.conn.execute(
            "SELECT messages FROM sessions WHERE project_path = ? ORDER BY updated_at DESC LIMIT 1",
            (project_path,),
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def list_sessions(
        self, project_path: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        if project_path:
            cursor = self.conn.execute(
                "SELECT id, project_path, updated_at, summary FROM sessions "
                "WHERE project_path = ? ORDER BY updated_at DESC LIMIT ?",
                (project_path, limit),
            )
        else:
            cursor = self.conn.execute(
                "SELECT id, project_path, updated_at, summary FROM sessions "
                "ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
        return [
            {"id": r[0], "path": r[1], "updated": r[2], "summary": r[3]}
            for r in cursor.fetchall()
        ]

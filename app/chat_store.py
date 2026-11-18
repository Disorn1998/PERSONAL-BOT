"""SQLite chat store — source of truth for threads and messages (incl. partials)."""

from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Role = Literal["user", "assistant", "system"]


@dataclass(slots=True)
class Thread:
    id: str
    persona_id: str
    title: str
    created_at: float
    updated_at: float


@dataclass(slots=True)
class Message:
    id: str
    thread_id: str
    role: Role
    content: str
    created_at: float
    partial: bool = False
    meta: dict[str, Any] | None = None


class ChatStore:
    """Windows-safe UTF-8 sqlite store under ``data/``."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    def _migrate(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                partial INTEGER NOT NULL DEFAULT 0,
                meta_json TEXT,
                FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_thread
                ON messages(thread_id, created_at);
            """
        )
        self._conn.commit()

    def create_thread(self, *, persona_id: str, title: str = "") -> Thread:
        now = time.time()
        thread = Thread(
            id=str(uuid.uuid4()),
            persona_id=persona_id,
            title=title or "new-chat",
            created_at=now,
            updated_at=now,
        )
        self._conn.execute(
            """
            INSERT INTO threads (id, persona_id, title, created_at, updated_at)
            VALUES (?,?,?,?,?)
            """,
            (
                thread.id,
                thread.persona_id,
                thread.title,
                thread.created_at,
                thread.updated_at,
            ),
        )
        self._conn.commit()
        return thread

    def list_threads(self, *, persona_id: str | None = None) -> list[Thread]:
        if persona_id:
            rows = self._conn.execute(
                "SELECT * FROM threads WHERE persona_id=? ORDER BY updated_at DESC",
                (persona_id,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM threads ORDER BY updated_at DESC").fetchall()
        return [self._row_thread(r) for r in rows]

    def get_thread(self, thread_id: str) -> Thread | None:
        row = self._conn.execute("SELECT * FROM threads WHERE id=?", (thread_id,)).fetchone()
        return self._row_thread(row) if row else None

    def touch_thread(self, thread_id: str, *, title: str | None = None) -> None:
        if title is None:
            self._conn.execute(
                "UPDATE threads SET updated_at=? WHERE id=?",
                (time.time(), thread_id),
            )
        else:
            self._conn.execute(
                "UPDATE threads SET updated_at=?, title=? WHERE id=?",
                (time.time(), title, thread_id),
            )
        self._conn.commit()

    def clear_thread_messages(self, thread_id: str) -> None:
        self._conn.execute("DELETE FROM messages WHERE thread_id=?", (thread_id,))
        self.touch_thread(thread_id)
        self._conn.commit()

    def delete_thread(self, thread_id: str) -> None:
        self._conn.execute("DELETE FROM threads WHERE id=?", (thread_id,))
        self._conn.commit()

    def add_message(
        self,
        *,
        thread_id: str,
        role: Role,
        content: str,
        partial: bool = False,
        message_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Message:
        import json

        msg = Message(
            id=message_id or str(uuid.uuid4()),
            thread_id=thread_id,
            role=role,
            content=content,
            created_at=time.time(),
            partial=partial,
            meta=meta,
        )
        self._conn.execute(
            """
            INSERT INTO messages (id, thread_id, role, content, created_at, partial, meta_json)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                msg.id,
                msg.thread_id,
                msg.role,
                msg.content,
                msg.created_at,
                1 if msg.partial else 0,
                json.dumps(meta, ensure_ascii=False) if meta else None,
            ),
        )
        self.touch_thread(thread_id)
        self._conn.commit()
        return msg

    def update_message(
        self,
        message_id: str,
        *,
        content: str,
        partial: bool | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        import json

        if partial is None and meta is None:
            self._conn.execute(
                "UPDATE messages SET content=? WHERE id=?",
                (content, message_id),
            )
        elif meta is None:
            self._conn.execute(
                "UPDATE messages SET content=?, partial=? WHERE id=?",
                (content, 1 if partial else 0, message_id),
            )
        else:
            self._conn.execute(
                "UPDATE messages SET content=?, partial=?, meta_json=? WHERE id=?",
                (
                    content,
                    1 if (partial or False) else 0,
                    json.dumps(meta, ensure_ascii=False),
                    message_id,
                ),
            )
        row = self._conn.execute(
            "SELECT thread_id FROM messages WHERE id=?", (message_id,)
        ).fetchone()
        if row:
            self.touch_thread(str(row["thread_id"]))
        self._conn.commit()

    def list_messages(self, thread_id: str) -> list[Message]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE thread_id=? ORDER BY created_at ASC",
            (thread_id,),
        ).fetchall()
        return [self._row_message(r) for r in rows]

    def history_for_prompt(self, thread_id: str) -> list[dict[str, str]]:
        """Return user/assistant messages suitable for ``build_messages``."""
        out: list[dict[str, str]] = []
        for msg in self.list_messages(thread_id):
            if msg.role not in {"user", "assistant"}:
                continue
            if not msg.content.strip():
                continue
            out.append({"role": msg.role, "content": msg.content})
        return out

    @staticmethod
    def _row_thread(row: sqlite3.Row) -> Thread:
        return Thread(
            id=str(row["id"]),
            persona_id=str(row["persona_id"]),
            title=str(row["title"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    @staticmethod
    def _row_message(row: sqlite3.Row) -> Message:
        import json

        meta_raw = row["meta_json"]
        meta = json.loads(meta_raw) if meta_raw else None
        return Message(
            id=str(row["id"]),
            thread_id=str(row["thread_id"]),
            role=str(row["role"]),  # type: ignore[arg-type]
            content=str(row["content"]),
            created_at=float(row["created_at"]),
            partial=bool(row["partial"]),
            meta=meta,
        )

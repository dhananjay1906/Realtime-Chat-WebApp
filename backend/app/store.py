"""SQLite message store. Small and synchronous on purpose: one lock, short queries."""

from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Message:
    id: int
    room: str
    username: str
    text: str
    ts: float

    def to_dict(self) -> dict:
        return {"type": "message", **asdict(self)}


class MessageStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                room     TEXT NOT NULL,
                username TEXT NOT NULL,
                text     TEXT NOT NULL,
                ts       REAL NOT NULL
            )
            """
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_room_id ON messages (room, id)")
        self._db.commit()

    def add(self, room: str, username: str, text: str) -> Message:
        ts = time.time()
        with self._lock:
            cur = self._db.execute(
                "INSERT INTO messages (room, username, text, ts) VALUES (?, ?, ?, ?)",
                (room, username, text, ts),
            )
            self._db.commit()
            return Message(cur.lastrowid, room, username, text, ts)

    def recent(self, room: str, limit: int = 50) -> list[Message]:
        with self._lock:
            rows = self._db.execute(
                "SELECT id, room, username, text, ts FROM messages "
                "WHERE room = ? ORDER BY id DESC LIMIT ?",
                (room, limit),
            ).fetchall()
        return [Message(*row) for row in reversed(rows)]

    def count(self, room: str) -> int:
        with self._lock:
            return self._db.execute(
                "SELECT COUNT(*) FROM messages WHERE room = ?", (room,)
            ).fetchone()[0]

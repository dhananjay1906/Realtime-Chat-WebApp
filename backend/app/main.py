"""Realtime chat server: FastAPI + WebSockets, with SQLite message history."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .manager import RoomManager
from .store import MessageStore

DEFAULT_ROOMS = ["general", "random", "dev-talk"]
ROOM_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")
NAME_RE = re.compile(r"^[\w .-]{1,24}$")
MAX_MESSAGE_LEN = 1000
RATE_LIMIT = 5  # messages per second, per connection

# WebSocket close codes (4000-4999 are free for apps)
CLOSE_BAD_INPUT = 4400
CLOSE_NAME_TAKEN = 4409


def create_app(db_path: str | None = None, static_dir: str | None = None) -> FastAPI:
    app = FastAPI(title="Realtime Chat", version="1.0.0")
    store = MessageStore(db_path or os.getenv("CHAT_DB", "chat.db"))
    rooms = RoomManager()
    app.state.store = store
    app.state.rooms = rooms

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/rooms")
    def list_rooms() -> list[dict]:
        online = rooms.online_counts()
        names = DEFAULT_ROOMS + sorted(r for r in online if r not in DEFAULT_ROOMS)
        return [{"name": n, "online": online.get(n, 0)} for n in names]

    @app.get("/api/rooms/{room}/messages")
    def room_messages(room: str, limit: int = Query(50, ge=1, le=200)) -> list[dict]:
        if not ROOM_RE.match(room):
            raise HTTPException(400, "Invalid room name")
        return [m.to_dict() for m in store.recent(room, limit)]

    @app.websocket("/ws/{room}")
    async def chat(ws: WebSocket, room: str, username: str = "") -> None:
        username = username.strip()
        await ws.accept()

        if not ROOM_RE.match(room) or not NAME_RE.match(username):
            await ws.close(code=CLOSE_BAD_INPUT, reason="Invalid room or username")
            return
        if not await rooms.join(room, ws, username):
            await ws.close(code=CLOSE_NAME_TAKEN, reason="That name is already in this room")
            return

        try:
            await ws.send_json(
                {"type": "history", "messages": [m.to_dict() for m in store.recent(room)]}
            )
            await rooms.broadcast_presence(room)
            await rooms.broadcast(room, {"type": "system", "text": f"{username} joined", "ts": time.time()}, exclude=ws)

            window_start, sent_in_window = time.monotonic(), 0
            while True:
                data = await ws.receive_json()
                kind = data.get("type")

                if kind == "message":
                    text = str(data.get("text", "")).strip()
                    if not text:
                        continue
                    now = time.monotonic()
                    if now - window_start >= 1:
                        window_start, sent_in_window = now, 0
                    sent_in_window += 1
                    if sent_in_window > RATE_LIMIT:
                        await ws.send_json({"type": "error", "text": "Slow down a little."})
                        continue
                    message = store.add(room, username, text[:MAX_MESSAGE_LEN])
                    await rooms.broadcast(room, message.to_dict())

                elif kind == "typing":
                    await rooms.broadcast(
                        room,
                        {"type": "typing", "username": username, "is_typing": bool(data.get("is_typing"))},
                        exclude=ws,
                    )
        except (WebSocketDisconnect, ValueError, KeyError):
            pass
        finally:
            if await rooms.leave(room, ws):
                await rooms.broadcast_presence(room)
                await rooms.broadcast(room, {"type": "system", "text": f"{username} left", "ts": time.time()})

    # Serve the built React app (frontend/dist) from the same origin in production.
    dist = Path(static_dir or os.getenv("STATIC_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            file = dist / path
            if path and file.is_file() and dist in file.resolve().parents:
                return FileResponse(file)
            return FileResponse(dist / "index.html")

    return app


app = create_app()

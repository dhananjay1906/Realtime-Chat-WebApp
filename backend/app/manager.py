"""Tracks who is connected to which room and fans messages out to them."""

from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket


class RoomManager:
    def __init__(self) -> None:
        # room -> {websocket: username}
        self._rooms: dict[str, dict[WebSocket, str]] = {}
        self._lock = asyncio.Lock()

    async def join(self, room: str, ws: WebSocket, username: str) -> bool:
        """Register a socket. Returns False if the name is already taken in this room."""
        async with self._lock:
            members = self._rooms.setdefault(room, {})
            if username.lower() in (u.lower() for u in members.values()):
                return False
            members[ws] = username
            return True

    async def leave(self, room: str, ws: WebSocket) -> str | None:
        async with self._lock:
            members = self._rooms.get(room, {})
            username = members.pop(ws, None)
            if not members:
                self._rooms.pop(room, None)
            return username

    def users(self, room: str) -> list[str]:
        return sorted(self._rooms.get(room, {}).values(), key=str.lower)

    def online_counts(self) -> dict[str, int]:
        return {room: len(members) for room, members in self._rooms.items()}

    async def broadcast(self, room: str, payload: dict, exclude: WebSocket | None = None) -> None:
        data = json.dumps(payload)
        targets = [ws for ws in list(self._rooms.get(room, {})) if ws is not exclude]
        results = await asyncio.gather(
            *(ws.send_text(data) for ws in targets), return_exceptions=True
        )
        # Sockets that failed to send are dead; drop them quietly.
        for ws, result in zip(targets, results):
            if isinstance(result, Exception):
                await self.leave(room, ws)

    async def broadcast_presence(self, room: str) -> None:
        await self.broadcast(room, {"type": "presence", "users": self.users(room)})

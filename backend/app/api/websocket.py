"""WebSocket endpoint for real-time analysis updates.

Provides a :class:`ConnectionManager` that tracks active client connections
and a WebSocket route handler that pushes incremental analysis progress to
connected frontends.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import get_logger

logger: logging.Logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage active WebSocket connections keyed by *client_id*."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    @property
    def active_connections(self) -> dict[str, WebSocket]:
        """Return the current connection map (read-only view)."""
        return self._connections

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a WebSocket handshake and store the connection.

        If *client_id* already has an open connection it is replaced.
        """
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info("WebSocket connected: client_id=%s (total=%d)", client_id, len(self._connections))

    def disconnect(self, client_id: str) -> None:
        """Remove a client from the active connections."""
        self._connections.pop(client_id, None)
        logger.info("WebSocket disconnected: client_id=%s (total=%d)", client_id, len(self._connections))

    async def send_message(self, client_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to a specific client.

        Silently disconnects the client if the socket has closed.
        """
        ws = self._connections.get(client_id)
        if ws is None:
            logger.warning("send_message: client_id=%s not found", client_id)
            return
        try:
            await ws.send_json(message)
        except Exception:
            logger.exception("Failed to send to client_id=%s – removing", client_id)
            self.disconnect(client_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client.

        Clients whose sockets have closed are automatically removed.
        """
        stale: list[str] = []
        for client_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning("Broadcast failed for client_id=%s – marking stale", client_id)
                stale.append(client_id)

        for client_id in stale:
            self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """Handle a WebSocket connection for *client_id*.

    The handler listens for incoming JSON messages, logs them, and can push
    analysis-progress updates back to the client via the global
    :data:`manager`.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_message(client_id, {"error": "Invalid JSON"})
                continue

            logger.info("WS message from %s: %s", client_id, str(data)[:200])

            msg_type = data.get("type", "unknown")

            if msg_type == "ping":
                await manager.send_message(client_id, {"type": "pong"})
            elif msg_type == "analyze":
                await manager.send_message(
                    client_id,
                    {"type": "status", "message": "Analysis request received", "progress": 0},
                )
            else:
                await manager.send_message(
                    client_id,
                    {"type": "ack", "original_type": msg_type},
                )
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        logger.exception("WebSocket error for client_id=%s", client_id)
        manager.disconnect(client_id)

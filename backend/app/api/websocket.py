"""WebSocket endpoint for real-time analysis streaming.

Provides a connection manager and a ``/ws/analysis`` endpoint that
accepts JSON messages, triggers analysis, and streams progress updates
back to the client.
"""

import json
import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Manage active WebSocket connections.

    Supports broadcasting to all connected clients as well as sending
    messages to individual connections.
    """

    def __init__(self) -> None:
        self._active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active.append(websocket)
        logger.info("WebSocket connected – %d active", len(self._active))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from the active list."""
        if websocket in self._active:
            self._active.remove(websocket)
        logger.info("WebSocket disconnected – %d active", len(self._active))

    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """Send a JSON payload to a single client."""
        await websocket.send_json(data)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Send a JSON payload to every connected client."""
        for connection in list(self._active):
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection)

    @property
    def active_count(self) -> int:
        """Return the number of active connections."""
        return len(self._active)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# /ws/analysis — real-time analysis stream
# ---------------------------------------------------------------------------
@router.websocket("/ws/analysis")
async def analysis_websocket(websocket: WebSocket) -> None:
    """Stream analysis progress to the client over a WebSocket.

    Expected inbound JSON format::

        {
            "type": "analyze",
            "data": { ... }
        }

    The server responds with progress updates and a final result.
    """
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {
                    "type": "error",
                    "detail": "Invalid JSON payload.",
                })
                continue

            request_id = str(uuid.uuid4())
            msg_type = message.get("type", "unknown")
            logger.info("WS message type=%s request_id=%s", msg_type, request_id)

            # Acknowledge receipt
            await manager.send_json(websocket, {
                "type": "ack",
                "request_id": request_id,
            })

            if msg_type == "analyze":
                # Stream simulated progress updates
                for step, progress in [
                    ("preprocessing", 25),
                    ("inference", 50),
                    ("graph_lookup", 75),
                    ("complete", 100),
                ]:
                    await manager.send_json(websocket, {
                        "type": "progress",
                        "request_id": request_id,
                        "step": step,
                        "progress": progress,
                    })

                # Final result
                await manager.send_json(websocket, {
                    "type": "result",
                    "request_id": request_id,
                    "diagnosis": "Healthy crop detected",
                    "confidence": 0.92,
                    "explanation": "No disease symptoms found.",
                })
            else:
                await manager.send_json(websocket, {
                    "type": "error",
                    "request_id": request_id,
                    "detail": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected gracefully.")
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        manager.disconnect(websocket)

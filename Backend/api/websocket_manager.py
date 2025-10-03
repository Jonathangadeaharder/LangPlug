"""
WebSocket connection manager for real-time updates
"""

import asyncio
import contextlib
import logging
from datetime import datetime

from fastapi import WebSocket
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with proper cleanup and error handling"""

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.connection_info: dict[WebSocket, dict] = {}
        self.health_check_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_ping": datetime.now(),
        }

        logger.info(f"WebSocket connected for user {user_id}")

        await self.send_personal_message(
            websocket, {"type": "connection", "status": "connected", "timestamp": datetime.now().isoformat()}
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection and clean up resources"""
        info = self.connection_info.get(websocket)

        if info:
            user_id = info["user_id"]

            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            del self.connection_info[websocket]

            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def send_user_message(self, user_id: str, message: dict):
        """Send a message to all connections for a specific user"""
        if user_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)

            for conn in disconnected:
                self.disconnect(conn)

    async def broadcast(self, message: dict, exclude_user: str | None = None):
        """Broadcast a message to all connected clients"""
        all_connections = []

        for user_id, connections in self.active_connections.items():
            if user_id != exclude_user:
                all_connections.extend(connections)

        disconnected = []

        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_progress_update(self, user_id: str, task_id: str, progress: int, status: str):
        """Send task progress update to user"""
        message = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        await self.send_user_message(user_id, message)

    async def send_error(self, user_id: str, error: str, task_id: str | None = None):
        """Send error message to user"""
        message = {"type": "error", "error": error, "task_id": task_id, "timestamp": datetime.now().isoformat()}
        await self.send_user_message(user_id, message)

    async def handle_message(self, websocket: WebSocket, data: dict):
        """Handle incoming WebSocket messages"""
        info = self.connection_info.get(websocket)
        if not info:
            return

        message_type = data.get("type")

        if message_type == "ping":
            info["last_ping"] = datetime.now()
            await self.send_personal_message(websocket, {"type": "pong", "timestamp": datetime.now().isoformat()})

        elif message_type == "subscribe":
            event_type = data.get("event_type")
            logger.info(f"User {info['user_id']} subscribed to {event_type}")

        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def start_health_checks(self):
        """Start background task to check connection health"""

        async def check_connections():
            while True:
                try:
                    await asyncio.sleep(30)  # Check every 30 seconds

                    current_time = datetime.now()
                    disconnected = []

                    for websocket, info in self.connection_info.items():
                        last_ping = info.get("last_ping")

                        if (current_time - last_ping).seconds > 60:
                            logger.warning(f"Connection timeout for user {info['user_id']}")
                            disconnected.append(websocket)
                        else:
                            try:
                                await websocket.send_json({"type": "heartbeat", "timestamp": current_time.isoformat()})
                            except (ConnectionClosed, RuntimeError, Exception) as e:
                                logger.warning(f"Failed to send heartbeat to websocket: {e}")
                                disconnected.append(websocket)

                    for conn in disconnected:
                        self.disconnect(conn)

                except Exception as e:
                    logger.error(f"Error in health check: {e}")

        self.health_check_task = asyncio.create_task(check_connections())

    async def stop_health_checks(self):
        """Stop the health check background task"""
        if self.health_check_task:
            self.health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.health_check_task

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        return len(self.active_connections.get(user_id, set()))

    def get_connected_users(self) -> set[str]:
        """Get set of all connected user IDs"""
        return set(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()

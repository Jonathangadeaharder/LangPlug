"""
WebSocket routes for real-time communication
"""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None)
):
    """
    WebSocket endpoint for real-time updates
    
    Connect with: ws://localhost:8000/ws/connect?token=YOUR_JWT_TOKEN
    """
    # Validate token and get user
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        # Validate token and get user info
        from core.auth import jwt_authentication
        from core.database import AsyncSessionLocal

        # Get database session
        async with AsyncSessionLocal() as db:
            user = await jwt_authentication.authenticate(token, db)
            if not user:
                await websocket.close(code=1008, reason="Invalid authentication token")
                return

        user_id = str(user.id)

        # Connect the WebSocket
        await manager.connect(websocket, user_id)

        try:
            # Keep connection alive and handle messages
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                # Handle the message
                await manager.handle_message(websocket, data)

        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info(f"WebSocket disconnected for user {user_id}")

        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Server error")


@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    """
    Simple status WebSocket for monitoring (no auth required)
    """
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "status",
            "connections": manager.get_connection_count(),
            "users": len(manager.get_connected_users())
        })

        # Keep connection alive for status updates
        while True:
            data = await websocket.receive_text()

            if data == "status":
                await websocket.send_json({
                    "type": "status",
                    "connections": manager.get_connection_count(),
                    "users": len(manager.get_connected_users())
                })

    except WebSocketDisconnect:
        logger.info("Status WebSocket disconnected")
    except Exception as e:
        logger.error(f"Status WebSocket error: {e}")

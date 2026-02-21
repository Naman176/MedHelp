from fastapi import WebSocket
from typing import Dict
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        # Maps a user's UUID to their active WebSocket connection
        self.active_connections: Dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: UUID):
        # Only send if the user is currently online
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

# Create a single global instance to use across app
manager = ConnectionManager()
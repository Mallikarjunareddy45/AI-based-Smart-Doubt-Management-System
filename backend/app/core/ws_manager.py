from fastapi import WebSocket
from typing import Dict, List, Set, Any
import json
import logging

logger = logging.getLogger("uvicorn.error")

class ConnectionManager:
    def __init__(self):
        # Maps user_id (str) to their active WebSocket connection objects
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps cluster_id (str) to a set of active user_ids listening in that thread
        self.cluster_rooms: Dict[str, Set[str]] = {}
        # Keep track of active tutors/admins for broadcasting dashboards
        self.active_tutors: Set[str] = set()
        self.active_admins: Set[str] = set()

    async def connect(self, websocket: WebSocket, user_id: str, roles: List[str]):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Track role classifications for workspace dashboards
        if "tutor" in roles:
            self.active_tutors.add(user_id)
        if "admin" in roles:
            self.active_admins.add(user_id)
            
        logger.info(f"WebSocket connected for user {user_id} with roles {roles}. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        # Clean up role tracking lists
        self.active_tutors.discard(user_id)
        self.active_admins.discard(user_id)
        
        # Remove user from any cluster rooms
        for room_users in self.cluster_rooms.values():
            room_users.discard(user_id)
            
        logger.info(f"WebSocket disconnected for user {user_id}")

    def join_cluster_room(self, user_id: str, cluster_id: str):
        cluster_str = str(cluster_id)
        if cluster_str not in self.cluster_rooms:
            self.cluster_rooms[cluster_str] = set()
        self.cluster_rooms[cluster_str].add(user_id)
        logger.info(f"User {user_id} joined cluster room {cluster_id}")

    def leave_cluster_room(self, user_id: str, cluster_id: str):
        cluster_str = str(cluster_id)
        if cluster_str in self.cluster_rooms:
            self.cluster_rooms[cluster_str].discard(user_id)
            if not self.cluster_rooms[cluster_str]:
                del self.cluster_rooms[cluster_str]
        logger.info(f"User {user_id} left cluster room {cluster_id}")

    async def send_personal_message(self, message: Any, user_id: str):
        user_str = str(user_id)
        if user_str in self.active_connections:
            payload = json.dumps(message) if isinstance(message, (dict, list)) else str(message)
            dead_sockets = set()
            for ws in self.active_connections[user_str]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.add(ws)
            # Remove any closed/dead sockets discovered during write
            for ws in dead_sockets:
                self.active_connections[user_str].discard(ws)

    async def broadcast_to_cluster(self, message: Dict[str, Any], cluster_id: str):
        cluster_str = str(cluster_id)
        if cluster_str in self.cluster_rooms:
            for user_id in list(self.cluster_rooms[cluster_str]):
                await self.send_personal_message(message, user_id)

    async def broadcast_to_tutors(self, message: Dict[str, Any]):
        for tutor_id in list(self.active_tutors):
            await self.send_personal_message(message, tutor_id)

    async def broadcast_to_admins(self, message: Dict[str, Any]):
        for admin_id in list(self.active_admins):
            await self.send_personal_message(message, admin_id)

    async def broadcast_all(self, message: Dict[str, Any]):
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

# Singleton manager instance
manager = ConnectionManager()

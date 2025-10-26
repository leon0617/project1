import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class StreamingService:
    """Manages WebSocket connections for streaming debug events"""
    
    def __init__(self):
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        
    async def connect(self, session_id: int, websocket: WebSocket):
        """Register a new WebSocket connection for a session"""
        await websocket.accept()
        
        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = set()
            self._connections[session_id].add(websocket)
            
        logger.info(f"WebSocket connected for session {session_id}")
        
    async def disconnect(self, session_id: int, websocket: WebSocket):
        """Remove a WebSocket connection"""
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)
                if not self._connections[session_id]:
                    del self._connections[session_id]
                    
        logger.info(f"WebSocket disconnected for session {session_id}")
        
    async def broadcast(self, session_id: int, message: dict):
        """Broadcast a message to all connected clients for a session"""
        async with self._lock:
            connections = self._connections.get(session_id, set()).copy()
            
        if not connections:
            return
            
        # Send to all connections, remove failed ones
        failed_connections = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                failed_connections.add(websocket)
                
        # Clean up failed connections
        if failed_connections:
            async with self._lock:
                if session_id in self._connections:
                    self._connections[session_id] -= failed_connections
                    if not self._connections[session_id]:
                        del self._connections[session_id]
                        
    def has_listeners(self, session_id: int) -> bool:
        """Check if there are any active listeners for a session"""
        return session_id in self._connections and len(self._connections[session_id]) > 0


# Global instance
streaming_service = StreamingService()

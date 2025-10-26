import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    DebugSessionCreate,
    DebugSessionResponse,
    DebugSessionDetailResponse,
    NetworkEventResponse,
)
from app.services import debug_session_service, streaming_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/sessions", response_model=DebugSessionResponse)
async def create_debug_session(
    session_create: DebugSessionCreate,
    db: Session = Depends(get_db),
):
    """Create a new debug session"""
    try:
        session = await debug_session_service.create_session(
            target_url=session_create.target_url,
            duration_limit=session_create.duration_limit,
            db=db,
        )
        return session
    except Exception as e:
        logger.error(f"Error creating debug session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/start", response_model=DebugSessionResponse)
async def start_debug_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Start a debug session and begin capturing network events"""
    try:
        await debug_session_service.start_session(session_id, db)
        session = debug_session_service.get_session(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting debug session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop", response_model=DebugSessionResponse)
async def stop_debug_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Stop a debug session"""
    try:
        await debug_session_service.stop_session(session_id, db)
        session = debug_session_service.get_session(session_id, db)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping debug session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=DebugSessionDetailResponse)
async def get_debug_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Get debug session details with all captured events"""
    session = debug_session_service.get_session(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/events", response_model=List[NetworkEventResponse])
async def get_session_events(
    session_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get network events for a debug session (paginated)"""
    session = debug_session_service.get_session(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    events = debug_session_service.get_session_events(
        session_id=session_id,
        db=db,
        limit=limit,
        offset=offset,
    )
    return events


@router.websocket("/sessions/{session_id}/stream")
async def stream_session_events(
    websocket: WebSocket,
    session_id: int,
):
    """WebSocket endpoint for streaming live debug events"""
    # Note: We can't easily inject db dependency in WebSocket
    # So we'll keep this simple for now
    await streaming_service.connect(session_id, websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for any message (client keep-alive pings)
            data = await websocket.receive_text()
            # Echo back to confirm connection is alive
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await streaming_service.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await streaming_service.disconnect(session_id, websocket)

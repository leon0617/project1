from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.debug import DebugSessionCreate, DebugSessionResponse, NetworkEventResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.debug_service import DebugService
from app.api.dependencies import get_pagination_params

router = APIRouter()


@router.post(
    "/sessions",
    response_model=DebugSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a debug session",
    description="Start a new debug session for a website. Only one active session per website is allowed.",
)
async def start_debug_session(
    session_create: DebugSessionCreate,
    db: Session = Depends(get_db),
):
    try:
        debug_session = DebugService.start_debug_session(db, session_create.website_id)
        return debug_session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/{session_id}/stop",
    response_model=DebugSessionResponse,
    summary="Stop a debug session",
    description="Stop an active debug session.",
)
async def stop_debug_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    debug_session = DebugService.stop_debug_session(db, session_id)
    if not debug_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found")
    return debug_session


@router.get(
    "/sessions/{session_id}",
    response_model=DebugSessionResponse,
    summary="Get a debug session",
    description="Retrieve details of a specific debug session.",
)
async def get_debug_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    debug_session = DebugService.get_debug_session(db, session_id)
    if not debug_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found")
    return debug_session


@router.get(
    "/sessions",
    response_model=PaginatedResponse[DebugSessionResponse],
    summary="List debug sessions",
    description="Retrieve a paginated list of debug sessions with optional filtering by website.",
)
async def list_debug_sessions(
    website_id: Optional[int] = Query(None, description="Filter by website ID"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    sessions, total = DebugService.get_debug_sessions(
        db,
        website_id=website_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return PaginatedResponse(
        items=sessions,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/events",
    response_model=PaginatedResponse[NetworkEventResponse],
    summary="List network events",
    description="Retrieve paginated network events with filtering by debug session, time range, and HTTP method.",
)
async def list_network_events(
    debug_session_id: Optional[int] = Query(None, description="Filter by debug session ID"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    events, total = DebugService.get_network_events(
        db,
        debug_session_id=debug_session_id,
        start_time=start_time,
        end_time=end_time,
        method=method,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return PaginatedResponse(
        items=events,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/sessions/{session_id}/stream",
    summary="Stream network events",
    description="Stream live network events from an active debug session using Server-Sent Events (SSE).",
)
async def stream_network_events(
    session_id: int,
    db: Session = Depends(get_db),
):
    debug_session = DebugService.get_debug_session(db, session_id)
    if not debug_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found")
    
    if debug_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debug session is not active"
        )
    
    return StreamingResponse(
        DebugService.stream_network_events(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

from typing import List, Optional, AsyncGenerator
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import asyncio
import json

from app.models.debug_session import DebugSession
from app.models.network_event import NetworkEvent
from app.models.website import Website


class DebugService:
    active_sessions = {}

    @staticmethod
    def start_debug_session(db: Session, website_id: int) -> DebugSession:
        website = db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise ValueError(f"Website with ID {website_id} not found")
        
        active_session = db.query(DebugSession).filter(
            DebugSession.website_id == website_id,
            DebugSession.status == "active"
        ).first()
        
        if active_session:
            raise ValueError(f"Debug session already active for website {website_id}")
        
        debug_session = DebugSession(
            website_id=website_id,
            status="active",
        )
        db.add(debug_session)
        db.commit()
        db.refresh(debug_session)
        
        DebugService.active_sessions[debug_session.id] = asyncio.Queue()
        
        return debug_session

    @staticmethod
    def stop_debug_session(db: Session, session_id: int) -> Optional[DebugSession]:
        debug_session = db.query(DebugSession).filter(DebugSession.id == session_id).first()
        if not debug_session:
            return None
        
        debug_session.end_time = datetime.now(timezone.utc)
        debug_session.status = "completed"
        db.commit()
        db.refresh(debug_session)
        
        if session_id in DebugService.active_sessions:
            del DebugService.active_sessions[session_id]
        
        return debug_session

    @staticmethod
    def get_debug_session(db: Session, session_id: int) -> Optional[DebugSession]:
        return db.query(DebugSession).filter(DebugSession.id == session_id).first()

    @staticmethod
    def get_debug_sessions(
        db: Session,
        website_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[DebugSession], int]:
        query = db.query(DebugSession)
        
        if website_id:
            query = query.filter(DebugSession.website_id == website_id)
        
        total = query.count()
        sessions = query.order_by(DebugSession.start_time.desc()).offset(skip).limit(limit).all()
        return sessions, total

    @staticmethod
    def get_network_events(
        db: Session,
        debug_session_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        method: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[NetworkEvent], int]:
        query = db.query(NetworkEvent)
        
        if debug_session_id:
            query = query.filter(NetworkEvent.debug_session_id == debug_session_id)
        if start_time:
            query = query.filter(NetworkEvent.timestamp >= start_time)
        if end_time:
            query = query.filter(NetworkEvent.timestamp <= end_time)
        if method:
            query = query.filter(NetworkEvent.method == method.upper())
        
        total = query.count()
        events = query.order_by(NetworkEvent.timestamp.desc()).offset(skip).limit(limit).all()
        return events, total

    @staticmethod
    async def stream_network_events(session_id: int) -> AsyncGenerator[str, None]:
        if session_id not in DebugService.active_sessions:
            return
        
        queue = DebugService.active_sessions[session_id]
        
        while session_id in DebugService.active_sessions:
            try:
                event_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(event_data)}\n\n"
            except asyncio.TimeoutError:
                yield f": keepalive\n\n"
            except Exception:
                break

    @staticmethod
    async def add_network_event(db: Session, session_id: int, event_data: dict):
        network_event = NetworkEvent(
            debug_session_id=session_id,
            method=event_data.get('method', 'GET'),
            url=event_data.get('url', ''),
            status_code=event_data.get('status_code'),
            headers=event_data.get('headers'),
            request_body=event_data.get('request_body'),
            response_body=event_data.get('response_body'),
            duration=event_data.get('duration'),
        )
        db.add(network_event)
        db.commit()
        db.refresh(network_event)
        
        if session_id in DebugService.active_sessions:
            queue = DebugService.active_sessions[session_id]
            await queue.put({
                'id': network_event.id,
                'timestamp': network_event.timestamp.isoformat(),
                'method': network_event.method,
                'url': network_event.url,
                'status_code': network_event.status_code,
                'duration': network_event.duration,
            })
        
        return network_event

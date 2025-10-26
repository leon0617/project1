import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from playwright.async_api import BrowserContext, Page, Route, Request, Response

from app.core.config import settings
from app.models import DebugSession, NetworkEvent, ConsoleError
from app.services.playwright_service import playwright_service
from app.services.streaming_service import streaming_service
from app.schemas import NetworkEventResponse, ConsoleErrorResponse

logger = logging.getLogger(__name__)


def utc_now():
    """Get current UTC time with timezone info"""
    return datetime.now(timezone.utc)


class ActiveDebugSession:
    """Represents an active debug session with its browser context"""
    
    def __init__(self, session_id: int, context: BrowserContext, page: Page, db: Session):
        self.session_id = session_id
        self.context = context
        self.page = page
        self.db = db
        self._stop_event = asyncio.Event()
        self._flush_task: Optional[asyncio.Task] = None
        self._timeout_task: Optional[asyncio.Task] = None
        self._pending_events: list = []
        self._pending_errors: list = []
        
    async def start_monitoring(self, duration_limit: Optional[int] = None):
        """Start monitoring network events and console messages"""
        # Set up network event handlers
        self.page.on("request", self._handle_request)
        self.page.on("response", self._handle_response)
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_page_error)
        
        # Start periodic flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
        # Start timeout task if duration limit is set
        if duration_limit:
            self._timeout_task = asyncio.create_task(self._timeout_handler(duration_limit))
            
    async def stop(self):
        """Stop monitoring and cleanup"""
        self._stop_event.set()
        
        # Cancel tasks
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
                
        if self._timeout_task:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
                
        # Final flush
        await self._flush_events()
        
        # Close context
        try:
            await self.context.close()
        except Exception as e:
            logger.error(f"Error closing context: {e}")
            
    async def _handle_request(self, request: Request):
        """Handle network request"""
        try:
            event_data = {
                "session_id": self.session_id,
                "event_type": "request",
                "url": request.url,
                "method": request.method,
                "request_headers": json.dumps(request.headers),
                "resource_type": request.resource_type,
                "timestamp": utc_now(),
            }
            
            # Try to get request body (may fail for some requests)
            try:
                post_data = request.post_data
                if post_data:
                    event_data["request_body"] = post_data[:10000]  # Limit body size
            except Exception:
                pass
                
            self._pending_events.append(event_data)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            
    async def _handle_response(self, response: Response):
        """Handle network response"""
        try:
            request = response.request
            timing = None
            
            # Calculate timing
            try:
                timing_data = await response.all_headers()
                # Timing calculation would need more sophisticated approach
                # For now, we'll skip precise timing
            except Exception:
                pass
            
            event_data = {
                "session_id": self.session_id,
                "event_type": "response",
                "url": response.url,
                "method": request.method,
                "status_code": response.status,
                "response_headers": json.dumps(response.headers),
                "resource_type": request.resource_type,
                "timestamp": utc_now(),
            }
            
            # Try to get response body (only for specific content types)
            try:
                content_type = response.headers.get("content-type", "")
                if any(ct in content_type.lower() for ct in ["json", "text", "xml", "html"]):
                    body = await response.text()
                    event_data["response_body"] = body[:10000]  # Limit body size
            except Exception:
                pass
                
            self._pending_events.append(event_data)
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            
    async def _handle_console(self, msg):
        """Handle console messages"""
        try:
            if msg.type in ["error", "warning"]:
                error_data = {
                    "session_id": self.session_id,
                    "level": msg.type,
                    "message": msg.text,
                    "timestamp": utc_now(),
                }
                self._pending_errors.append(error_data)
        except Exception as e:
            logger.error(f"Error handling console message: {e}")
            
    async def _handle_page_error(self, error):
        """Handle page errors"""
        try:
            error_data = {
                "session_id": self.session_id,
                "level": "error",
                "message": str(error),
                "timestamp": utc_now(),
            }
            self._pending_errors.append(error_data)
        except Exception as e:
            logger.error(f"Error handling page error: {e}")
            
    async def _periodic_flush(self):
        """Periodically flush captured events to database"""
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(settings.debug_session_flush_interval)
                await self._flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
                
    async def _flush_events(self):
        """Flush pending events to database and stream to clients"""
        if not self._pending_events and not self._pending_errors:
            return
            
        # Get events to flush
        events_to_flush = self._pending_events[:]
        errors_to_flush = self._pending_errors[:]
        self._pending_events.clear()
        self._pending_errors.clear()
        
        # Persist to database
        try:
            # Add network events and collect DB objects
            db_events = []
            for event_data in events_to_flush:
                db_event = NetworkEvent(**event_data)
                self.db.add(db_event)
                db_events.append(db_event)
                
            # Add console errors and collect DB objects
            db_errors = []
            for error_data in errors_to_flush:
                db_error = ConsoleError(**error_data)
                self.db.add(db_error)
                db_errors.append(db_error)
                
            self.db.commit()
            
            # Refresh objects to get IDs
            for db_event in db_events:
                self.db.refresh(db_event)
                
            for db_error in db_errors:
                self.db.refresh(db_error)
            
            # Stream to connected clients
            for db_event in db_events:
                await streaming_service.broadcast(
                    self.session_id,
                    {
                        "type": "network_event",
                        "event": NetworkEventResponse.model_validate(db_event).model_dump()
                    }
                )
                
            for db_error in db_errors:
                await streaming_service.broadcast(
                    self.session_id,
                    {
                        "type": "console_error",
                        "error": ConsoleErrorResponse.model_validate(db_error).model_dump()
                    }
                )
                
            logger.info(f"Flushed {len(events_to_flush)} events and {len(errors_to_flush)} errors for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error flushing events: {e}")
            self.db.rollback()
            
    async def _timeout_handler(self, duration_limit: int):
        """Handle session timeout"""
        try:
            await asyncio.sleep(duration_limit)
            logger.info(f"Session {self.session_id} reached duration limit")
            await streaming_service.broadcast(
                self.session_id,
                {
                    "type": "status",
                    "status": "timeout",
                    "message": "Session duration limit reached"
                }
            )
            self._stop_event.set()
        except asyncio.CancelledError:
            pass


class DebugSessionService:
    """Service for managing debug sessions"""
    
    def __init__(self):
        self._active_sessions: Dict[int, ActiveDebugSession] = {}
        
    async def create_session(self, target_url: str, duration_limit: Optional[int], db: Session) -> DebugSession:
        """Create a new debug session"""
        # Validate duration limit
        if duration_limit and duration_limit > settings.debug_session_max_duration:
            duration_limit = settings.debug_session_max_duration
            
        # Create session record
        session = DebugSession(
            target_url=target_url,
            status="pending",
            duration_limit=duration_limit,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created debug session {session.id} for {target_url}")
        return session
        
    async def start_session(self, session_id: int, db: Session):
        """Start a debug session"""
        session = db.query(DebugSession).filter_by(id=session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        if session.status != "pending":
            raise ValueError(f"Session {session_id} is not in pending state")
            
        try:
            # Create browser context
            context = await playwright_service.create_context()
            page = await context.new_page()
            
            # Create active session
            active_session = ActiveDebugSession(session_id, context, page, db)
            self._active_sessions[session_id] = active_session
            
            # Update session status
            session.status = "active"
            session.started_at = utc_now()
            db.commit()
            
            # Start monitoring
            await active_session.start_monitoring(session.duration_limit)
            
            # Navigate to target URL
            logger.info(f"Navigating to {session.target_url}")
            await page.goto(session.target_url, wait_until="networkidle", timeout=30000)
            
            # Broadcast status
            await streaming_service.broadcast(
                session_id,
                {
                    "type": "status",
                    "status": "active",
                    "message": "Session started successfully"
                }
            )
            
            logger.info(f"Started debug session {session_id}")
        except Exception as e:
            logger.error(f"Error starting session {session_id}: {e}")
            session.status = "failed"
            session.error_message = str(e)
            db.commit()
            
            # Cleanup
            if session_id in self._active_sessions:
                await self._active_sessions[session_id].stop()
                del self._active_sessions[session_id]
                
            raise
            
    async def stop_session(self, session_id: int, db: Session):
        """Stop a debug session"""
        session = db.query(DebugSession).filter_by(id=session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} is not active")
            
        try:
            # Stop active session
            active_session = self._active_sessions[session_id]
            await active_session.stop()
            del self._active_sessions[session_id]
            
            # Update session status
            session.status = "stopped"
            session.stopped_at = utc_now()
            db.commit()
            
            # Broadcast status
            await streaming_service.broadcast(
                session_id,
                {
                    "type": "status",
                    "status": "stopped",
                    "message": "Session stopped"
                }
            )
            
            logger.info(f"Stopped debug session {session_id}")
        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")
            raise
            
    def get_session(self, session_id: int, db: Session) -> Optional[DebugSession]:
        """Get a debug session by ID"""
        return db.query(DebugSession).filter_by(id=session_id).first()
        
    def get_session_events(self, session_id: int, db: Session, limit: int = 100, offset: int = 0):
        """Get network events for a session"""
        return db.query(NetworkEvent).filter_by(
            session_id=session_id
        ).order_by(NetworkEvent.timestamp.desc()).limit(limit).offset(offset).all()
        
    def is_session_active(self, session_id: int) -> bool:
        """Check if a session is active"""
        return session_id in self._active_sessions


# Global instance
debug_session_service = DebugSessionService()

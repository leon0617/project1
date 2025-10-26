import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set testing mode
os.environ["TESTING"] = "1"

from app.models import DebugSession, NetworkEvent
from app.core.database import Base
from app.services.debug_session_service import debug_session_service, ActiveDebugSession


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_active_debug_session_request_handling(db_session):
    """Test that ActiveDebugSession properly handles network requests"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Mock context and page
    mock_context = MagicMock()
    mock_context.close = AsyncMock()
    mock_page = MagicMock()
    
    # Create active session
    active_session = ActiveDebugSession(session.id, mock_context, mock_page, db_session)
    
    # Mock request
    mock_request = MagicMock()
    mock_request.url = "https://example.com/api/test"
    mock_request.method = "GET"
    mock_request.headers = {"User-Agent": "Test"}
    mock_request.resource_type = "xhr"
    mock_request.post_data = None
    
    # Handle request
    await active_session._handle_request(mock_request)
    
    # Verify event was captured
    assert len(active_session._pending_events) == 1
    event = active_session._pending_events[0]
    assert event["url"] == "https://example.com/api/test"
    assert event["method"] == "GET"
    assert event["event_type"] == "request"
    
    # Cleanup
    await active_session.stop()


@pytest.mark.asyncio
async def test_active_debug_session_response_handling(db_session):
    """Test that ActiveDebugSession properly handles network responses"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Mock context and page
    mock_context = MagicMock()
    mock_context.close = AsyncMock()
    mock_page = MagicMock()
    
    # Create active session
    active_session = ActiveDebugSession(session.id, mock_context, mock_page, db_session)
    
    # Mock response
    mock_request = MagicMock()
    mock_request.url = "https://example.com/api/test"
    mock_request.method = "GET"
    mock_request.resource_type = "xhr"
    
    mock_response = MagicMock()
    mock_response.url = "https://example.com/api/test"
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.request = mock_request
    mock_response.all_headers = AsyncMock(return_value={"Content-Type": "application/json"})
    mock_response.text = AsyncMock(return_value='{"success": true}')
    
    # Handle response
    await active_session._handle_response(mock_response)
    
    # Verify event was captured
    assert len(active_session._pending_events) == 1
    event = active_session._pending_events[0]
    assert event["url"] == "https://example.com/api/test"
    assert event["status_code"] == 200
    assert event["event_type"] == "response"
    
    # Cleanup
    await active_session.stop()


@pytest.mark.asyncio
async def test_active_debug_session_console_error_handling(db_session):
    """Test that ActiveDebugSession properly handles console errors"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Mock context and page
    mock_context = MagicMock()
    mock_context.close = AsyncMock()
    mock_page = MagicMock()
    
    # Create active session
    active_session = ActiveDebugSession(session.id, mock_context, mock_page, db_session)
    
    # Mock console message
    mock_console_msg = MagicMock()
    mock_console_msg.type = "error"
    mock_console_msg.text = "Uncaught ReferenceError: foo is not defined"
    
    # Handle console message
    await active_session._handle_console(mock_console_msg)
    
    # Verify error was captured
    assert len(active_session._pending_errors) == 1
    error = active_session._pending_errors[0]
    assert error["level"] == "error"
    assert "ReferenceError" in error["message"]
    
    # Cleanup
    await active_session.stop()


@pytest.mark.asyncio
async def test_event_flushing(db_session):
    """Test that events are properly flushed to database"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Mock context and page
    mock_context = MagicMock()
    mock_context.close = AsyncMock()
    mock_page = MagicMock()
    
    # Create active session
    active_session = ActiveDebugSession(session.id, mock_context, mock_page, db_session)
    
    # Add some pending events
    active_session._pending_events.append({
        "session_id": session.id,
        "event_type": "request",
        "url": "https://example.com/test",
        "method": "GET",
        "request_headers": "{}",
        "resource_type": "document",
        "timestamp": datetime.now(timezone.utc),
    })
    
    # Flush events
    await active_session._flush_events()
    
    # Verify events were persisted
    events = db_session.query(NetworkEvent).filter_by(session_id=session.id).all()
    assert len(events) == 1
    assert events[0].url == "https://example.com/test"
    
    # Verify pending events were cleared
    assert len(active_session._pending_events) == 0
    
    # Cleanup
    await active_session.stop()


@pytest.mark.asyncio
async def test_session_timeout(db_session):
    """Test that sessions respect duration limits"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active",
        duration_limit=1  # 1 second
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Mock context and page
    mock_context = MagicMock()
    mock_context.close = AsyncMock()
    mock_page = MagicMock()
    
    # Create active session
    active_session = ActiveDebugSession(session.id, mock_context, mock_page, db_session)
    
    # Start timeout handler
    timeout_task = asyncio.create_task(active_session._timeout_handler(1))
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Verify stop event was set
    assert active_session._stop_event.is_set()
    
    # Cleanup
    timeout_task.cancel()
    try:
        await timeout_task
    except asyncio.CancelledError:
        pass
    await active_session.stop()


@pytest.mark.asyncio
async def test_debug_session_service_create(db_session):
    """Test creating a debug session via service"""
    session = await debug_session_service.create_session(
        target_url="https://example.com",
        duration_limit=60,
        db=db_session
    )
    
    assert session.id is not None
    assert session.target_url == "https://example.com"
    assert session.status == "pending"
    assert session.duration_limit == 60


@pytest.mark.asyncio
async def test_debug_session_service_max_duration_limit(db_session):
    """Test that service enforces max duration limit"""
    from app.core.config import settings
    
    # Try to create session with excessive duration
    session = await debug_session_service.create_session(
        target_url="https://example.com",
        duration_limit=99999,  # Way over limit
        db=db_session
    )
    
    # Should be capped at max
    assert session.duration_limit == settings.debug_session_max_duration


@pytest.mark.asyncio
async def test_debug_session_service_get_events(db_session):
    """Test retrieving session events via service"""
    # Create session
    session = DebugSession(
        target_url="https://example.com",
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Add events
    for i in range(10):
        event = NetworkEvent(
            session_id=session.id,
            event_type="request",
            url=f"https://example.com/page{i}",
            method="GET"
        )
        db_session.add(event)
    db_session.commit()
    
    # Retrieve events
    events = debug_session_service.get_session_events(
        session_id=session.id,
        db=db_session,
        limit=5,
        offset=0
    )
    
    assert len(events) == 5
    
    # Test pagination
    events_page2 = debug_session_service.get_session_events(
        session_id=session.id,
        db=db_session,
        limit=5,
        offset=5
    )
    
    assert len(events_page2) == 5
    assert events[0].id != events_page2[0].id  # Different results

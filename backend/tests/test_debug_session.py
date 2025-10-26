import pytest
import asyncio
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch

# Set testing mode to avoid Playwright initialization
os.environ["TESTING"] = "1"

from app.main import app
from app.core.database import Base, get_db
from app.models import DebugSession, NetworkEvent, ConsoleError


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestDebugSessionAPI:
    """Tests for debug session API endpoints"""
    
    def test_create_debug_session(self, client):
        """Test creating a new debug session"""
        response = client.post(
            "/api/debug/sessions",
            json={
                "target_url": "https://example.com",
                "duration_limit": 60
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_url"] == "https://example.com"
        assert data["status"] == "pending"
        assert data["duration_limit"] == 60
        assert "id" in data
        assert "created_at" in data
        
    def test_create_debug_session_without_duration(self, client):
        """Test creating a session without duration limit"""
        response = client.post(
            "/api/debug/sessions",
            json={"target_url": "https://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_url"] == "https://example.com"
        assert data["duration_limit"] is None
        
    def test_get_debug_session(self, client, db_session):
        """Test retrieving a debug session"""
        # Create a session in database
        session = DebugSession(
            target_url="https://example.com",
            status="pending"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Retrieve it
        response = client.get(f"/api/debug/sessions/{session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session.id
        assert data["target_url"] == "https://example.com"
        assert "network_events" in data
        assert "console_errors" in data
        
    def test_get_nonexistent_session(self, client):
        """Test retrieving a non-existent session"""
        response = client.get("/api/debug/sessions/99999")
        assert response.status_code == 404
        
    def test_get_session_events(self, client, db_session):
        """Test retrieving network events for a session"""
        # Create session and events
        session = DebugSession(
            target_url="https://example.com",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Add network events
        for i in range(5):
            event = NetworkEvent(
                session_id=session.id,
                event_type="request",
                url=f"https://example.com/resource{i}",
                method="GET"
            )
            db_session.add(event)
        db_session.commit()
        
        # Retrieve events
        response = client.get(f"/api/debug/sessions/{session.id}/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all(e["session_id"] == session.id for e in data)
        
    def test_get_session_events_pagination(self, client, db_session):
        """Test pagination of network events"""
        # Create session and events
        session = DebugSession(
            target_url="https://example.com",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Add many network events
        for i in range(25):
            event = NetworkEvent(
                session_id=session.id,
                event_type="request",
                url=f"https://example.com/resource{i}",
                method="GET"
            )
            db_session.add(event)
        db_session.commit()
        
        # Test pagination
        response = client.get(f"/api/debug/sessions/{session.id}/events?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        response = client.get(f"/api/debug/sessions/{session.id}/events?limit=10&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10


class TestDebugSessionWithMockedPlaywright:
    """Tests for debug session with mocked Playwright"""
    
    @pytest.mark.asyncio
    async def test_start_session_with_mock(self, client, db_session):
        """Test starting a debug session with mocked Playwright"""
        # Create session
        session = DebugSession(
            target_url="https://example.com",
            status="pending"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Mock Playwright components
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.on = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()
        
        with patch('app.services.playwright_service.playwright_service.create_context', 
                   return_value=mock_context):
            response = client.post(f"/api/debug/sessions/{session.id}/start")
            
            # Give it a moment to process
            await asyncio.sleep(0.1)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            assert data["started_at"] is not None
            
            # Verify Playwright was called
            mock_context.new_page.assert_called_once()
            mock_page.goto.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_stop_session_with_mock(self, client, db_session):
        """Test stopping a debug session"""
        # Create active session
        session = DebugSession(
            target_url="https://example.com",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Mock active session
        mock_active_session = MagicMock()
        mock_active_session.stop = AsyncMock()
        
        with patch.dict('app.services.debug_session_service.debug_session_service._active_sessions',
                        {session.id: mock_active_session}):
            response = client.post(f"/api/debug/sessions/{session.id}/stop")
            
            # Give it a moment to process
            await asyncio.sleep(0.1)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"
            assert data["stopped_at"] is not None
            
            # Verify cleanup was called
            mock_active_session.stop.assert_called_once()


class TestNetworkEventCapture:
    """Tests for network event capture functionality"""
    
    def test_network_event_persistence(self, db_session):
        """Test that network events are properly persisted"""
        # Create session
        session = DebugSession(
            target_url="https://example.com",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Create network event
        event = NetworkEvent(
            session_id=session.id,
            event_type="request",
            url="https://example.com/api/data",
            method="POST",
            request_headers='{"Content-Type": "application/json"}',
            request_body='{"test": "data"}',
            resource_type="xhr"
        )
        db_session.add(event)
        db_session.commit()
        
        # Verify persistence
        retrieved_event = db_session.query(NetworkEvent).filter_by(
            session_id=session.id
        ).first()
        assert retrieved_event is not None
        assert retrieved_event.url == "https://example.com/api/data"
        assert retrieved_event.method == "POST"
        assert retrieved_event.event_type == "request"
        
    def test_console_error_persistence(self, db_session):
        """Test that console errors are properly persisted"""
        # Create session
        session = DebugSession(
            target_url="https://example.com",
            status="active"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Create console error
        error = ConsoleError(
            session_id=session.id,
            level="error",
            message="Uncaught TypeError: Cannot read property 'foo' of undefined"
        )
        db_session.add(error)
        db_session.commit()
        
        # Verify persistence
        retrieved_error = db_session.query(ConsoleError).filter_by(
            session_id=session.id
        ).first()
        assert retrieved_error is not None
        assert retrieved_error.level == "error"
        assert "TypeError" in retrieved_error.message
        
    def test_session_cascade_delete(self, db_session):
        """Test that deleting a session cascades to events and errors"""
        # Create session with events and errors
        session = DebugSession(
            target_url="https://example.com",
            status="stopped"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Add events and errors
        event = NetworkEvent(
            session_id=session.id,
            event_type="request",
            url="https://example.com",
            method="GET"
        )
        error = ConsoleError(
            session_id=session.id,
            level="error",
            message="Test error"
        )
        db_session.add(event)
        db_session.add(error)
        db_session.commit()
        
        # Delete session
        db_session.delete(session)
        db_session.commit()
        
        # Verify cascade delete
        assert db_session.query(NetworkEvent).filter_by(session_id=session.id).count() == 0
        assert db_session.query(ConsoleError).filter_by(session_id=session.id).count() == 0


class TestStreamingService:
    """Tests for streaming service"""
    
    def test_streaming_connection_management(self):
        """Test WebSocket connection management"""
        from app.services.streaming_service import StreamingService
        
        service = StreamingService()
        
        # Initially no connections
        assert not service.has_listeners(1)
        
        # Note: Full WebSocket testing requires more complex setup
        # This is a basic structure test
        assert service._connections == {}


@pytest.mark.asyncio
async def test_playwright_service_lifecycle():
    """Test Playwright service start/stop"""
    from app.services.playwright_service import PlaywrightService
    
    service = PlaywrightService()
    
    # Initially not running
    assert not service.is_running
    
    # Note: Actually starting Playwright in tests requires browser binaries
    # In CI, we would mock this or use --headed flag with proper setup

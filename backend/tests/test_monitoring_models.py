import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.monitoring import (
    Website,
    MonitorCheck,
    DowntimeWindow,
    DebugSession,
    NetworkEvent,
    MonitorStatus,
    HTTPMethod,
    NetworkEventType,
)
from app.schemas.monitoring import (
    WebsiteCreate,
    WebsiteUpdate,
    MonitorCheckCreate,
    DowntimeWindowCreate,
    DowntimeWindowUpdate,
    DebugSessionCreate,
    DebugSessionUpdate,
    NetworkEventCreate,
)
from app.services.monitoring_crud import (
    WebsiteCRUD,
    MonitorCheckCRUD,
    DowntimeWindowCRUD,
    DebugSessionCRUD,
    NetworkEventCRUD,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_website(db_session):
    """Create a sample website for testing"""
    website = WebsiteCreate(
        url="https://example.com",
        name="Example Website",
        description="A test website",
        check_interval=300,
        timeout=30,
        is_active=True,
    )
    return WebsiteCRUD.create(db_session, website)


class TestWebsiteModel:
    """Test Website ORM model"""

    def test_create_website(self, db_session):
        website = Website(
            url="https://test.com",
            name="Test Site",
            check_interval=60,
            timeout=10,
        )
        db_session.add(website)
        db_session.commit()
        db_session.refresh(website)

        assert website.id is not None
        assert website.url == "https://test.com"
        assert website.name == "Test Site"
        assert website.is_active is True
        assert website.created_at is not None
        assert website.updated_at is not None

    def test_website_url_unique_constraint(self, db_session):
        website1 = Website(url="https://duplicate.com", name="Site 1", check_interval=60, timeout=10)
        db_session.add(website1)
        db_session.commit()

        website2 = Website(url="https://duplicate.com", name="Site 2", check_interval=60, timeout=10)
        db_session.add(website2)

        with pytest.raises(Exception):
            db_session.commit()

    def test_website_relationships(self, db_session, sample_website):
        assert sample_website.monitor_checks == []
        assert sample_website.downtime_windows == []
        assert sample_website.debug_sessions == []


class TestMonitorCheckModel:
    """Test MonitorCheck ORM model"""

    def test_create_monitor_check(self, db_session, sample_website):
        check = MonitorCheck(
            website_id=sample_website.id,
            status=MonitorStatus.UP,
            http_status_code=200,
            http_method=HTTPMethod.GET,
            response_time_ms=150.5,
            dns_time_ms=10.2,
            connect_time_ms=20.3,
            tls_time_ms=15.4,
            ttfb_ms=100.1,
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.id is not None
        assert check.website_id == sample_website.id
        assert check.status == MonitorStatus.UP
        assert check.http_status_code == 200
        assert check.response_time_ms == 150.5
        assert check.checked_at is not None

    def test_monitor_check_with_error(self, db_session, sample_website):
        check = MonitorCheck(
            website_id=sample_website.id,
            status=MonitorStatus.DOWN,
            error_message="Connection timeout",
        )
        db_session.add(check)
        db_session.commit()
        db_session.refresh(check)

        assert check.status == MonitorStatus.DOWN
        assert check.error_message == "Connection timeout"
        assert check.http_status_code is None

    def test_monitor_check_cascade_delete(self, db_session, sample_website):
        check = MonitorCheck(website_id=sample_website.id, status=MonitorStatus.UP)
        db_session.add(check)
        db_session.commit()

        check_id = check.id
        db_session.delete(sample_website)
        db_session.commit()

        deleted_check = db_session.query(MonitorCheck).filter_by(id=check_id).first()
        assert deleted_check is None


class TestDowntimeWindowModel:
    """Test DowntimeWindow ORM model"""

    def test_create_downtime_window(self, db_session, sample_website):
        started = datetime.utcnow()
        downtime = DowntimeWindow(
            website_id=sample_website.id,
            started_at=started,
            initial_status=MonitorStatus.DOWN,
            affected_checks_count=5,
        )
        db_session.add(downtime)
        db_session.commit()
        db_session.refresh(downtime)

        assert downtime.id is not None
        assert downtime.website_id == sample_website.id
        assert downtime.started_at == started
        assert downtime.ended_at is None
        assert downtime.initial_status == MonitorStatus.DOWN
        assert downtime.affected_checks_count == 5

    def test_complete_downtime_window(self, db_session, sample_website):
        started = datetime.utcnow()
        ended = started + timedelta(minutes=10)

        downtime = DowntimeWindow(
            website_id=sample_website.id,
            started_at=started,
            ended_at=ended,
            duration_seconds=600,
            initial_status=MonitorStatus.DOWN,
            recovery_status=MonitorStatus.UP,
            affected_checks_count=10,
        )
        db_session.add(downtime)
        db_session.commit()
        db_session.refresh(downtime)

        assert downtime.ended_at == ended
        assert downtime.duration_seconds == 600
        assert downtime.recovery_status == MonitorStatus.UP


class TestDebugSessionModel:
    """Test DebugSession ORM model"""

    def test_create_debug_session(self, db_session, sample_website):
        session = DebugSession(
            website_id=sample_website.id,
            session_key="test-session-123",
            user_agent="Mozilla/5.0",
            browser_type="chromium",
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.id is not None
        assert session.session_key == "test-session-123"
        assert session.user_agent == "Mozilla/5.0"
        assert session.browser_type == "chromium"
        assert session.started_at is not None
        assert session.completed_at is None
        assert session.success is None

    def test_debug_session_unique_key(self, db_session, sample_website):
        session1 = DebugSession(
            website_id=sample_website.id, session_key="duplicate-key"
        )
        db_session.add(session1)
        db_session.commit()

        session2 = DebugSession(
            website_id=sample_website.id, session_key="duplicate-key"
        )
        db_session.add(session2)

        with pytest.raises(Exception):
            db_session.commit()


class TestNetworkEventModel:
    """Test NetworkEvent ORM model"""

    def test_create_network_event(self, db_session, sample_website):
        session = DebugSession(
            website_id=sample_website.id, session_key="test-session"
        )
        db_session.add(session)
        db_session.commit()

        event = NetworkEvent(
            debug_session_id=session.id,
            event_type=NetworkEventType.REQUEST,
            url="https://example.com/api",
            method=HTTPMethod.GET,
            request_headers='{"Content-Type": "application/json"}',
            duration_ms=50.5,
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.id is not None
        assert event.debug_session_id == session.id
        assert event.event_type == NetworkEventType.REQUEST
        assert event.url == "https://example.com/api"
        assert event.method == HTTPMethod.GET
        assert event.duration_ms == 50.5

    def test_network_event_with_response(self, db_session, sample_website):
        session = DebugSession(
            website_id=sample_website.id, session_key="test-session-2"
        )
        db_session.add(session)
        db_session.commit()

        event = NetworkEvent(
            debug_session_id=session.id,
            event_type=NetworkEventType.RESPONSE,
            url="https://example.com/api",
            method=HTTPMethod.POST,
            status_code=200,
            response_headers='{"Content-Type": "application/json"}',
            response_payload='{"status": "success"}',
        )
        db_session.add(event)
        db_session.commit()

        assert event.event_type == NetworkEventType.RESPONSE
        assert event.status_code == 200
        assert event.response_payload == '{"status": "success"}'


class TestWebsiteCRUD:
    """Test Website CRUD operations"""

    def test_create_website_crud(self, db_session):
        website_data = WebsiteCreate(
            url="https://crud-test.com",
            name="CRUD Test",
            check_interval=120,
            timeout=15,
        )
        website = WebsiteCRUD.create(db_session, website_data)

        assert website.id is not None
        assert website.url == "https://crud-test.com"
        assert website.name == "CRUD Test"

    def test_get_website_by_id(self, db_session, sample_website):
        website = WebsiteCRUD.get_by_id(db_session, sample_website.id)
        assert website is not None
        assert website.id == sample_website.id

    def test_get_website_by_url(self, db_session, sample_website):
        website = WebsiteCRUD.get_by_url(db_session, sample_website.url)
        assert website is not None
        assert website.url == sample_website.url

    def test_get_active_websites(self, db_session):
        active = WebsiteCreate(
            url="https://active.com", name="Active", is_active=True
        )
        inactive = WebsiteCreate(
            url="https://inactive.com", name="Inactive", is_active=False
        )

        WebsiteCRUD.create(db_session, active)
        WebsiteCRUD.create(db_session, inactive)

        active_sites = WebsiteCRUD.get_active_websites(db_session)
        assert len(active_sites) == 1
        assert active_sites[0].url == "https://active.com"

    def test_update_website(self, db_session, sample_website):
        update_data = WebsiteUpdate(name="Updated Name", check_interval=600)
        updated = WebsiteCRUD.update(db_session, sample_website.id, update_data)

        assert updated.name == "Updated Name"
        assert updated.check_interval == 600
        assert updated.url == sample_website.url

    def test_delete_website(self, db_session, sample_website):
        website_id = sample_website.id
        result = WebsiteCRUD.delete(db_session, website_id)

        assert result is True
        deleted = WebsiteCRUD.get_by_id(db_session, website_id)
        assert deleted is None


class TestMonitorCheckCRUD:
    """Test MonitorCheck CRUD operations"""

    def test_create_monitor_check_crud(self, db_session, sample_website):
        check_data = MonitorCheckCreate(
            website_id=sample_website.id,
            status=MonitorStatus.UP,
            http_status_code=200,
            response_time_ms=100.0,
        )
        check = MonitorCheckCRUD.create(db_session, check_data)

        assert check.id is not None
        assert check.status == MonitorStatus.UP
        assert check.http_status_code == 200

    def test_get_checks_by_website(self, db_session, sample_website):
        for i in range(5):
            check_data = MonitorCheckCreate(
                website_id=sample_website.id, status=MonitorStatus.UP
            )
            MonitorCheckCRUD.create(db_session, check_data)

        checks, total = MonitorCheckCRUD.get_by_website(
            db_session, sample_website.id, limit=10
        )
        assert total == 5
        assert len(checks) == 5

    def test_get_latest_check(self, db_session, sample_website):
        for i in range(3):
            check_data = MonitorCheckCreate(
                website_id=sample_website.id, status=MonitorStatus.UP
            )
            MonitorCheckCRUD.create(db_session, check_data)

        latest = MonitorCheckCRUD.get_latest_by_website(
            db_session, sample_website.id
        )
        assert latest is not None
        assert latest.status == MonitorStatus.UP

    def test_calculate_uptime_percentage(self, db_session, sample_website):
        for i in range(8):
            check_data = MonitorCheckCreate(
                website_id=sample_website.id, status=MonitorStatus.UP
            )
            MonitorCheckCRUD.create(db_session, check_data)

        for i in range(2):
            check_data = MonitorCheckCreate(
                website_id=sample_website.id, status=MonitorStatus.DOWN
            )
            MonitorCheckCRUD.create(db_session, check_data)

        uptime = MonitorCheckCRUD.calculate_uptime_percentage(
            db_session, sample_website.id, hours=24
        )
        assert uptime == 80.0


class TestDowntimeWindowCRUD:
    """Test DowntimeWindow CRUD operations"""

    def test_create_downtime_crud(self, db_session, sample_website):
        downtime_data = DowntimeWindowCreate(
            website_id=sample_website.id,
            started_at=datetime.utcnow(),
            initial_status=MonitorStatus.DOWN,
        )
        downtime = DowntimeWindowCRUD.create(db_session, downtime_data)

        assert downtime.id is not None
        assert downtime.website_id == sample_website.id
        assert downtime.ended_at is None

    def test_get_ongoing_downtime(self, db_session, sample_website):
        ongoing = DowntimeWindowCreate(
            website_id=sample_website.id,
            started_at=datetime.utcnow(),
            initial_status=MonitorStatus.DOWN,
        )
        created = DowntimeWindowCRUD.create(db_session, ongoing)

        found = DowntimeWindowCRUD.get_ongoing_downtime(db_session, sample_website.id)
        assert found is not None
        assert found.id == created.id

    def test_update_downtime_window(self, db_session, sample_website):
        downtime_data = DowntimeWindowCreate(
            website_id=sample_website.id,
            started_at=datetime.utcnow(),
            initial_status=MonitorStatus.DOWN,
        )
        downtime = DowntimeWindowCRUD.create(db_session, downtime_data)

        update_data = DowntimeWindowUpdate(
            ended_at=datetime.utcnow(),
            recovery_status=MonitorStatus.UP,
            affected_checks_count=10,
        )
        updated = DowntimeWindowCRUD.update(db_session, downtime.id, update_data)

        assert updated.ended_at is not None
        assert updated.recovery_status == MonitorStatus.UP
        assert updated.duration_seconds is not None


class TestDebugSessionCRUD:
    """Test DebugSession CRUD operations"""

    def test_create_debug_session_crud(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="test-key-123",
            browser_type="chromium",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        assert session.id is not None
        assert session.session_key == "test-key-123"
        assert session.started_at is not None

    def test_get_by_session_key(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="unique-key",
        )
        created = DebugSessionCRUD.create(db_session, session_data)

        found = DebugSessionCRUD.get_by_session_key(db_session, "unique-key")
        assert found is not None
        assert found.id == created.id

    def test_update_debug_session(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="update-test",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        update_data = DebugSessionUpdate(
            completed_at=datetime.utcnow(),
            success=True,
        )
        updated = DebugSessionCRUD.update(db_session, session.id, update_data)

        assert updated.completed_at is not None
        assert updated.success is True


class TestNetworkEventCRUD:
    """Test NetworkEvent CRUD operations"""

    def test_create_network_event_crud(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="event-test",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        event_data = NetworkEventCreate(
            debug_session_id=session.id,
            event_type=NetworkEventType.REQUEST,
            url="https://test.com",
            method=HTTPMethod.GET,
        )
        event = NetworkEventCRUD.create(db_session, event_data)

        assert event.id is not None
        assert event.debug_session_id == session.id

    def test_bulk_create_events(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="bulk-test",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        events_data = [
            NetworkEventCreate(
                debug_session_id=session.id,
                event_type=NetworkEventType.REQUEST,
                url=f"https://test.com/{i}",
            )
            for i in range(5)
        ]

        events = NetworkEventCRUD.bulk_create(db_session, events_data)
        assert len(events) == 5

    def test_get_events_by_session(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="query-test",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        for i in range(3):
            event_data = NetworkEventCreate(
                debug_session_id=session.id,
                event_type=NetworkEventType.REQUEST,
                url=f"https://test.com/{i}",
            )
            NetworkEventCRUD.create(db_session, event_data)

        events, total = NetworkEventCRUD.get_by_session(db_session, session.id)
        assert total == 3
        assert len(events) == 3

    def test_get_events_by_time_range(self, db_session, sample_website):
        session_data = DebugSessionCreate(
            website_id=sample_website.id,
            session_key="time-test",
        )
        session = DebugSessionCRUD.create(db_session, session_data)

        start_time = datetime.utcnow() - timedelta(seconds=10)
        for i in range(3):
            event_data = NetworkEventCreate(
                debug_session_id=session.id,
                event_type=NetworkEventType.REQUEST,
                url=f"https://test.com/{i}",
                timestamp=start_time + timedelta(seconds=i + 1),
            )
            NetworkEventCRUD.create(db_session, event_data)

        end_time = datetime.utcnow() + timedelta(seconds=10)

        events = NetworkEventCRUD.get_by_time_range(
            db_session, session.id, start_time, end_time
        )
        assert len(events) == 3

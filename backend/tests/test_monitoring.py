import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Website, MonitorCheck, DowntimeWindow
from app.core.database import Base
from app.services.monitoring import MonitoringService


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_website(db_session):
    """Create a test website."""
    website = Website(
        url="https://example.com",
        name="Example Site",
        enabled=True,
        check_interval=300,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)
    return website


@pytest.mark.asyncio
async def test_check_website_success(db_session, test_website):
    """Test successful website check."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        is_available, status_code, response_time, error_message = await monitoring_service.check_website(
            db_session, test_website
        )
    
    assert is_available is True
    assert status_code == 200
    assert response_time is not None
    assert response_time > 0
    assert error_message is None


@pytest.mark.asyncio
async def test_check_website_404(db_session, test_website):
    """Test website check with 404 status."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    mock_response = AsyncMock()
    mock_response.status_code = 404
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        is_available, status_code, response_time, error_message = await monitoring_service.check_website(
            db_session, test_website
        )
    
    assert is_available is False
    assert status_code == 404
    assert response_time is not None
    assert error_message is None


@pytest.mark.asyncio
async def test_check_website_timeout(db_session, test_website):
    """Test website check with timeout."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        is_available, status_code, response_time, error_message = await monitoring_service.check_website(
            db_session, test_website
        )
    
    assert is_available is False
    assert status_code is None
    assert response_time is not None
    assert "Timeout" in error_message


@pytest.mark.asyncio
async def test_check_website_connection_error(db_session, test_website):
    """Test website check with connection error."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        is_available, status_code, response_time, error_message = await monitoring_service.check_website(
            db_session, test_website
        )
    
    assert is_available is False
    assert status_code is None
    assert response_time is not None
    assert "Connection error" in error_message


@pytest.mark.asyncio
async def test_perform_check_persists_data(db_session, test_website):
    """Test that perform_check persists monitor check data."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        monitor_check = await monitoring_service.perform_check(db_session, test_website)
    
    assert monitor_check.id is not None
    assert monitor_check.website_id == test_website.id
    assert monitor_check.is_available is True
    assert monitor_check.status_code == 200
    assert monitor_check.response_time is not None
    
    # Verify it's in the database
    db_check = db_session.query(MonitorCheck).filter_by(id=monitor_check.id).first()
    assert db_check is not None
    assert db_check.website_id == test_website.id


@pytest.mark.asyncio
async def test_downtime_window_opens_on_failure(db_session, test_website):
    """Test that downtime window opens when website becomes unavailable."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        await monitoring_service.perform_check(db_session, test_website)
    
    # Check that a downtime window was created
    downtime_window = db_session.query(DowntimeWindow).filter_by(website_id=test_website.id).first()
    assert downtime_window is not None
    assert downtime_window.start_time is not None
    assert downtime_window.end_time is None


@pytest.mark.asyncio
async def test_downtime_window_closes_on_recovery(db_session, test_website):
    """Test that downtime window closes when website recovers."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    # First, create a failure to open a downtime window
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        await monitoring_service.perform_check(db_session, test_website)
    
    # Verify downtime window is open
    downtime_window = db_session.query(DowntimeWindow).filter_by(website_id=test_website.id).first()
    assert downtime_window is not None
    assert downtime_window.end_time is None
    
    # Now simulate recovery
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        await monitoring_service.perform_check(db_session, test_website)
    
    # Verify downtime window is closed
    db_session.refresh(downtime_window)
    assert downtime_window.end_time is not None
    assert downtime_window.end_time > downtime_window.start_time


@pytest.mark.asyncio
async def test_multiple_checks_create_multiple_records(db_session, test_website):
    """Test that multiple checks create multiple monitor check records."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        check1 = await monitoring_service.perform_check(db_session, test_website)
        check2 = await monitoring_service.perform_check(db_session, test_website)
        check3 = await monitoring_service.perform_check(db_session, test_website)
    
    checks = db_session.query(MonitorCheck).filter_by(website_id=test_website.id).all()
    assert len(checks) == 3
    assert check1.id != check2.id != check3.id


@pytest.mark.asyncio
async def test_no_duplicate_downtime_windows(db_session, test_website):
    """Test that multiple failures don't create duplicate downtime windows."""
    monitoring_service = MonitoringService(timeout=10.0, max_retries=2)
    
    # Simulate multiple failures
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        await monitoring_service.perform_check(db_session, test_website)
        await monitoring_service.perform_check(db_session, test_website)
        await monitoring_service.perform_check(db_session, test_website)
    
    # Should only have one open downtime window
    downtime_windows = db_session.query(DowntimeWindow).filter_by(
        website_id=test_website.id,
        end_time=None
    ).all()
    assert len(downtime_windows) == 1

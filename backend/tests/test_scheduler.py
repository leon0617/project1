import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Website, MonitorCheck
from app.core.database import Base
from app.services.scheduler import SchedulerService, CircuitBreaker


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
def test_websites(db_session):
    """Create test websites."""
    website1 = Website(
        url="https://example1.com",
        name="Example Site 1",
        enabled=True,
        check_interval=300,
    )
    website2 = Website(
        url="https://example2.com",
        name="Example Site 2",
        enabled=True,
        check_interval=600,
    )
    website3 = Website(
        url="https://example3.com",
        name="Example Site 3",
        enabled=False,
        check_interval=300,
    )
    db_session.add_all([website1, website2, website3])
    db_session.commit()
    db_session.refresh(website1)
    db_session.refresh(website2)
    db_session.refresh(website3)
    return [website1, website2, website3]


def test_circuit_breaker_records_failure():
    """Test that circuit breaker records failures."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    
    cb.record_failure(1)
    assert cb.failures[1] == 1
    assert not cb.is_blocked(1)
    
    cb.record_failure(1)
    assert cb.failures[1] == 2
    assert not cb.is_blocked(1)
    
    cb.record_failure(1)
    assert cb.failures[1] == 3
    assert cb.is_blocked(1)


def test_circuit_breaker_records_success():
    """Test that circuit breaker resets on success."""
    cb = CircuitBreaker(failure_threshold=3, timeout=60)
    
    cb.record_failure(1)
    cb.record_failure(1)
    assert cb.failures[1] == 2
    
    cb.record_success(1)
    assert 1 not in cb.failures
    assert not cb.is_blocked(1)


def test_circuit_breaker_blocks_after_threshold():
    """Test that circuit breaker blocks after threshold."""
    cb = CircuitBreaker(failure_threshold=5, timeout=60)
    
    for i in range(5):
        cb.record_failure(1)
    
    assert cb.is_blocked(1)


@patch("app.services.scheduler.settings")
def test_scheduler_start_disabled(mock_settings):
    """Test that scheduler doesn't start when disabled."""
    mock_settings.scheduler_enabled = False
    
    scheduler_service = SchedulerService()
    scheduler_service.start()
    
    assert scheduler_service.scheduler is None


@patch("app.services.scheduler.settings")
def test_scheduler_start_enabled(mock_settings):
    """Test that scheduler starts when enabled."""
    mock_settings.scheduler_enabled = True
    mock_settings.scheduler_timezone = "UTC"
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        scheduler_service.start()
        
        mock_scheduler_class.assert_called_once_with(timezone="UTC")
        mock_scheduler.start.assert_called_once()


@patch("app.services.scheduler.settings")
@patch("app.services.scheduler.SessionLocal")
def test_scheduler_sync_jobs_adds_active_websites(mock_session_local, mock_settings):
    """Test that sync_jobs adds jobs for active websites."""
    mock_settings.scheduler_enabled = True
    mock_settings.scheduler_timezone = "UTC"
    
    # Create mock websites
    website1 = Website(id=1, url="https://example1.com", name="Site 1", enabled=True, check_interval=300)
    website2 = Website(id=2, url="https://example2.com", name="Site 2", enabled=True, check_interval=600)
    website3 = Website(id=3, url="https://example3.com", name="Site 3", enabled=False, check_interval=300)
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [website1, website2]
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        scheduler_service.start()
        
        # Verify jobs were added for active websites
        assert mock_scheduler.add_job.call_count == 2
        assert 1 in scheduler_service.job_ids
        assert 2 in scheduler_service.job_ids
        assert 3 not in scheduler_service.job_ids


@patch("app.services.scheduler.settings")
def test_scheduler_add_or_update_job(mock_settings):
    """Test adding or updating a job."""
    mock_settings.scheduler_enabled = True
    mock_settings.scheduler_timezone = "UTC"
    
    website = Website(id=1, url="https://example.com", name="Site", enabled=True, check_interval=300)
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        scheduler_service.start()
        mock_scheduler.add_job.reset_mock()  # Reset calls from start()
        
        scheduler_service.add_or_update_job(website)
        
        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args
        assert call_args[1]["id"] == "monitor_1"
        assert call_args[1]["name"] == "Monitor Site"
        assert 1 in scheduler_service.job_ids


@patch("app.services.scheduler.settings")
def test_scheduler_remove_job(mock_settings):
    """Test removing a job."""
    mock_settings.scheduler_enabled = True
    mock_settings.scheduler_timezone = "UTC"
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        scheduler_service.start()
        scheduler_service.job_ids[1] = "monitor_1"
        
        scheduler_service.remove_job(1)
        
        mock_scheduler.remove_job.assert_called_with("monitor_1")
        assert 1 not in scheduler_service.job_ids


@pytest.mark.asyncio
@patch("app.services.scheduler.SessionLocal")
async def test_check_website_wrapper_success(mock_session_local):
    """Test the check website wrapper function."""
    website = Website(id=1, url="https://example.com", name="Site", enabled=True, check_interval=300)
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = website
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.monitoring_service.perform_check") as mock_perform_check:
        mock_perform_check.return_value = AsyncMock()
        
        await scheduler_service._check_website_wrapper(1)
        
        mock_perform_check.assert_called_once_with(mock_db, website)


@pytest.mark.asyncio
@patch("app.services.scheduler.SessionLocal")
async def test_check_website_wrapper_removes_job_if_not_found(mock_session_local):
    """Test that wrapper removes job if website not found."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    scheduler_service.job_ids[1] = "monitor_1"
    
    with patch.object(scheduler_service, "remove_job") as mock_remove_job:
        await scheduler_service._check_website_wrapper(1)
        
        mock_remove_job.assert_called_once_with(1)


@pytest.mark.asyncio
@patch("app.services.scheduler.SessionLocal")
async def test_check_website_wrapper_removes_job_if_disabled(mock_session_local):
    """Test that wrapper removes job if website is disabled."""
    website = Website(id=1, url="https://example.com", name="Site", enabled=False, check_interval=300)
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = website
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    scheduler_service.job_ids[1] = "monitor_1"
    
    with patch.object(scheduler_service, "remove_job") as mock_remove_job:
        await scheduler_service._check_website_wrapper(1)
        
        mock_remove_job.assert_called_once_with(1)


@pytest.mark.asyncio
@patch("app.services.scheduler.SessionLocal")
async def test_check_website_wrapper_circuit_breaker(mock_session_local):
    """Test that circuit breaker prevents checks when open."""
    website = Website(id=1, url="https://example.com", name="Site", enabled=True, check_interval=300)
    
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    
    # Trigger circuit breaker
    for _ in range(5):
        scheduler_service.circuit_breaker.record_failure(1)
    
    with patch("app.services.scheduler.monitoring_service.perform_check") as mock_perform_check:
        await scheduler_service._check_website_wrapper(1)
        
        # Should not have called perform_check
        mock_perform_check.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.scheduler.SessionLocal")
async def test_check_website_wrapper_records_failure_in_circuit_breaker(mock_session_local):
    """Test that wrapper records failures in circuit breaker."""
    website = Website(id=1, url="https://example.com", name="Site", enabled=True, check_interval=300)
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = website
    mock_session_local.return_value = mock_db
    
    scheduler_service = SchedulerService()
    
    with patch("app.services.scheduler.monitoring_service.perform_check") as mock_perform_check:
        mock_perform_check.side_effect = Exception("Test error")
        
        await scheduler_service._check_website_wrapper(1)
        
        # Should have recorded failure
        assert scheduler_service.circuit_breaker.failures.get(1, 0) == 1

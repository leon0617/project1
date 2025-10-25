"""
Integration test to validate the complete monitoring flow:
1. Create a website via API
2. Trigger a monitoring check
3. Verify MonitorCheck record is created
4. Simulate downtime and verify DowntimeWindow opens
5. Simulate recovery and verify DowntimeWindow closes
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Website, MonitorCheck, DowntimeWindow
from app.core.database import Base
from app.services.monitoring import monitoring_service


# Create test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = TestingSessionLocal()
    # Clear tables
    session.query(MonitorCheck).delete()
    session.query(DowntimeWindow).delete()
    session.query(Website).delete()
    session.commit()
    yield session
    session.close()


@pytest.mark.asyncio
async def test_complete_monitoring_flow(db_session):
    """Test the complete monitoring flow from website creation to downtime tracking."""
    
    # Step 1: Create a website
    website = Website(
        url="https://example.com",
        name="Example Site",
        enabled=True,
        check_interval=300,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)
    
    assert website.id is not None
    assert website.enabled is True
    
    # Step 2: Perform initial successful check
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        check1 = await monitoring_service.perform_check(db_session, website)
    
    # Verify check was recorded
    assert check1.id is not None
    assert check1.is_available is True
    assert check1.status_code == 200
    assert check1.response_time is not None
    
    # Verify no downtime window was created
    downtime_windows = db_session.query(DowntimeWindow).filter_by(website_id=website.id).all()
    assert len(downtime_windows) == 0
    
    # Step 3: Simulate website going down
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        check2 = await monitoring_service.perform_check(db_session, website)
    
    # Verify failure was recorded
    assert check2.is_available is False
    assert check2.status_code is None
    assert "Unexpected error" in check2.error_message
    
    # Verify downtime window was opened
    downtime_windows = db_session.query(DowntimeWindow).filter_by(website_id=website.id).all()
    assert len(downtime_windows) == 1
    assert downtime_windows[0].end_time is None  # Still open
    assert downtime_windows[0].start_time is not None
    
    # Step 4: Simulate continued downtime (should not create new window)
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
        check3 = await monitoring_service.perform_check(db_session, website)
    
    # Verify failure was recorded
    assert check3.is_available is False
    
    # Verify still only one downtime window (no duplicate)
    downtime_windows = db_session.query(DowntimeWindow).filter_by(website_id=website.id).all()
    assert len(downtime_windows) == 1
    assert downtime_windows[0].end_time is None  # Still open
    
    # Step 5: Simulate website recovery
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        check4 = await monitoring_service.perform_check(db_session, website)
    
    # Verify success was recorded
    assert check4.is_available is True
    assert check4.status_code == 200
    
    # Verify downtime window was closed
    db_session.refresh(downtime_windows[0])
    assert downtime_windows[0].end_time is not None
    assert downtime_windows[0].end_time > downtime_windows[0].start_time
    
    # Step 6: Verify all checks were recorded
    all_checks = db_session.query(MonitorCheck).filter_by(website_id=website.id).order_by(MonitorCheck.timestamp).all()
    assert len(all_checks) == 4
    assert all_checks[0].is_available is True   # Initial success
    assert all_checks[1].is_available is False  # First failure
    assert all_checks[2].is_available is False  # Continued failure
    assert all_checks[3].is_available is True   # Recovery
    
    # Step 7: Simulate another downtime cycle
    with patch("httpx.AsyncClient.get", side_effect=Exception("Timeout")):
        check5 = await monitoring_service.perform_check(db_session, website)
    
    # Verify new downtime window was opened
    downtime_windows = db_session.query(DowntimeWindow).filter_by(website_id=website.id).order_by(DowntimeWindow.start_time).all()
    assert len(downtime_windows) == 2
    assert downtime_windows[0].end_time is not None  # First window closed
    assert downtime_windows[1].end_time is None      # Second window open
    
    # Step 8: Close second downtime window
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        check6 = await monitoring_service.perform_check(db_session, website)
    
    # Verify second downtime window was closed
    db_session.refresh(downtime_windows[1])
    assert downtime_windows[1].end_time is not None
    
    # Final verification: 6 checks total, 2 complete downtime windows
    all_checks = db_session.query(MonitorCheck).filter_by(website_id=website.id).all()
    assert len(all_checks) == 6
    
    downtime_windows = db_session.query(DowntimeWindow).filter_by(website_id=website.id).all()
    assert len(downtime_windows) == 2
    assert all(dw.end_time is not None for dw in downtime_windows)

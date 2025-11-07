"""
Tests for monitoring task functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.website import Website
from app.models.monitoring_result import MonitoringResult
from app.models.debug_session import DebugSession


client = TestClient(app)


def test_trigger_manual_check(db_session: Session):
    """Test manually triggering a website check."""
    # Create a test website
    website = Website(
        url="https://www.google.com",
        name="Google",
        check_interval=300,
        enabled=True,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)

    # Trigger a manual check
    response = client.post(f"/api/monitoring/check/{website.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify the response contains monitoring result data
    assert "id" in data
    assert "website_id" in data
    assert data["website_id"] == website.id
    assert "status_code" in data
    assert "response_time" in data
    assert "success" in data
    assert "timestamp" in data

    # Verify the result was saved to database
    result = db_session.query(MonitoringResult).filter(
        MonitoringResult.website_id == website.id
    ).first()

    assert result is not None
    assert result.website_id == website.id
    assert result.status_code is not None
    assert result.response_time > 0


def test_trigger_manual_check_website_not_found(db_session: Session):
    """Test manually triggering a check for non-existent website."""
    response = client.post("/api/monitoring/check/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_manual_check_with_debug_session(db_session: Session):
    """Test manual check captures network events when debug session is active."""
    # Create a test website
    website = Website(
        url="https://www.google.com",
        name="Google",
        check_interval=300,
        enabled=True,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)

    # Start a debug session
    debug_response = client.post(
        "/api/debug/sessions",
        json={"website_id": website.id}
    )
    assert debug_response.status_code == 201
    debug_session_id = debug_response.json()["id"]

    # Trigger a manual check
    response = client.post(f"/api/monitoring/check/{website.id}")
    assert response.status_code == 200

    # Verify network events were captured
    events_response = client.get(
        "/api/debug/events",
        params={"debug_session_id": debug_session_id}
    )
    assert events_response.status_code == 200

    events_data = events_response.json()
    # Should have captured at least one network event (the main page request)
    assert events_data["total"] >= 1

    # Stop the debug session
    client.post(f"/api/debug/sessions/{debug_session_id}/stop")


@pytest.mark.asyncio
async def test_monitoring_task_check_website(db_session: Session):
    """Test the MonitoringTask.check_website function directly."""
    from app.tasks.monitoring_task import MonitoringTask

    # Create a test website
    website = Website(
        url="https://www.example.com",
        name="Example",
        check_interval=300,
        enabled=True,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)

    # Check the website
    result = await MonitoringTask.check_website(website, db_session)

    assert result is not None
    assert result.website_id == website.id
    assert result.status_code is not None
    assert result.response_time > 0
    assert isinstance(result.success, int)

    # Clean up browser
    await MonitoringTask.close_browser()


@pytest.mark.asyncio
async def test_monitoring_task_check_all_enabled_websites(db_session: Session):
    """Test checking all enabled websites."""
    from app.tasks.monitoring_task import MonitoringTask

    # Create multiple test websites
    websites = [
        Website(url="https://www.google.com", name="Google", enabled=True),
        Website(url="https://www.github.com", name="GitHub", enabled=True),
        Website(url="https://www.disabled.com", name="Disabled", enabled=False),
    ]

    for website in websites:
        db_session.add(website)
    db_session.commit()

    # Run the monitoring task
    await MonitoringTask.check_all_enabled_websites()

    # Verify results were created for enabled websites only
    results = db_session.query(MonitoringResult).all()

    # Should have 2 results (for enabled websites only)
    assert len(results) >= 2

    # Verify the disabled website was not checked
    disabled_website = db_session.query(Website).filter(
        Website.name == "Disabled"
    ).first()

    disabled_results = db_session.query(MonitoringResult).filter(
        MonitoringResult.website_id == disabled_website.id
    ).all()

    assert len(disabled_results) == 0

    # Clean up browser
    await MonitoringTask.close_browser()


def test_scheduler_initialization():
    """Test that the scheduler can be initialized."""
    from app.tasks.scheduler import TaskScheduler

    scheduler = TaskScheduler()
    assert scheduler.scheduler is None
    assert scheduler._initialized is False

    # Note: We don't actually start the scheduler in tests
    # as it would require the scheduler_enabled setting to be True


@pytest.mark.asyncio
async def test_monitoring_task_error_handling(db_session: Session):
    """Test monitoring task handles errors gracefully."""
    from app.tasks.monitoring_task import MonitoringTask

    # Create a website with invalid URL that will fail
    website = Website(
        url="https://this-domain-definitely-does-not-exist-12345.com",
        name="Invalid",
        check_interval=300,
        enabled=True,
    )
    db_session.add(website)
    db_session.commit()
    db_session.refresh(website)

    # Check the website - should not raise exception
    result = await MonitoringTask.check_website(website, db_session)

    assert result is not None
    assert result.website_id == website.id
    assert result.success == 0  # Should be marked as failure
    assert result.error_message is not None

    # Clean up browser
    await MonitoringTask.close_browser()

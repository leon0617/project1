import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import create_application
from app.core.database import Base, get_db
from app.models import Website, MonitorCheck, DowntimeWindow


# Create test database with StaticPool to share connection
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create all tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_app():
    """Create test app with overridden dependencies."""
    app = create_application()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture(scope="module")
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_db():
    """Clear database before each test."""
    # Clear tables
    with TestingSessionLocal() as db:
        try:
            db.query(MonitorCheck).delete()
            db.query(DowntimeWindow).delete()
            db.query(Website).delete()
            db.commit()
        except:
            db.rollback()
    yield


def test_create_website(client):
    """Test creating a new website."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["name"] == "Example Site"
    assert data["enabled"] is True
    assert data["check_interval"] == 300
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_website_duplicate_url(client):
    """Test creating a website with duplicate URL."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        # Create first website
        client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site 2",
                "enabled": True,
                "check_interval": 300,
            },
        )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_website_invalid_url(client):
    """Test creating a website with invalid URL."""
    response = client.post(
        "/api/websites",
        json={
            "url": "not-a-valid-url",
            "name": "Example Site",
            "enabled": True,
            "check_interval": 300,
        },
    )
    
    assert response.status_code == 422


def test_list_websites(client):
    """Test listing all websites."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        # Create some websites
        client.post(
            "/api/websites",
            json={
                "url": "https://example1.com",
                "name": "Example Site 1",
                "enabled": True,
                "check_interval": 300,
            },
        )
        client.post(
            "/api/websites",
            json={
                "url": "https://example2.com",
                "name": "Example Site 2",
                "enabled": False,
                "check_interval": 600,
            },
        )
    
    response = client.get("/api/websites")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["url"] == "https://example1.com"
    assert data[1]["url"] == "https://example2.com"


def test_get_website(client):
    """Test getting a specific website."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        create_response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
    
    website_id = create_response.json()["id"]
    response = client.get(f"/api/websites/{website_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == website_id
    assert data["url"] == "https://example.com"


def test_get_website_not_found(client):
    """Test getting a non-existent website."""
    response = client.get("/api/websites/999")
    
    assert response.status_code == 404


def test_update_website(client):
    """Test updating a website."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        create_response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
        
        website_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/websites/{website_id}",
            json={
                "name": "Updated Site",
                "check_interval": 600,
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Site"
    assert data["check_interval"] == 600
    assert data["url"] == "https://example.com"  # Should not change


def test_update_website_enable_adds_job(client):
    """Test that enabling a website adds it to scheduler."""
    with patch("app.api.websites.scheduler_service.add_or_update_job") as mock_add_job:
        create_response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": False,
                "check_interval": 300,
            },
        )
        
        website_id = create_response.json()["id"]
        mock_add_job.reset_mock()
        
        response = client.patch(
            f"/api/websites/{website_id}",
            json={"enabled": True},
        )
        
        assert response.status_code == 200
        assert response.json()["enabled"] is True
        mock_add_job.assert_called_once()


def test_update_website_disable_removes_job(client):
    """Test that disabling a website removes it from scheduler."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        create_response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
        
        website_id = create_response.json()["id"]
    
    with patch("app.api.websites.scheduler_service.remove_job") as mock_remove_job:
        response = client.patch(
            f"/api/websites/{website_id}",
            json={"enabled": False},
        )
        
        assert response.status_code == 200
        assert response.json()["enabled"] is False
        mock_remove_job.assert_called_once_with(website_id)


def test_delete_website(client):
    """Test deleting a website."""
    with patch("app.api.websites.scheduler_service.add_or_update_job"):
        create_response = client.post(
            "/api/websites",
            json={
                "url": "https://example.com",
                "name": "Example Site",
                "enabled": True,
                "check_interval": 300,
            },
        )
    
    website_id = create_response.json()["id"]
    
    with patch("app.api.websites.scheduler_service.remove_job") as mock_remove_job:
        response = client.delete(f"/api/websites/{website_id}")
        
        assert response.status_code == 204
        mock_remove_job.assert_called_once_with(website_id)
    
    # Verify website is deleted
    get_response = client.get(f"/api/websites/{website_id}")
    assert get_response.status_code == 404


def test_delete_website_not_found(client):
    """Test deleting a non-existent website."""
    response = client.delete("/api/websites/999")
    
    assert response.status_code == 404

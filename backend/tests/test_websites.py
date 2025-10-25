import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_website():
    response = client.post(
        "/api/websites/",
        json={
            "url": "https://example.com",
            "name": "Example Website",
            "check_interval": 300,
            "enabled": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["name"] == "Example Website"
    assert data["check_interval"] == 300
    assert data["enabled"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_website_invalid_url():
    response = client.post(
        "/api/websites/",
        json={
            "url": "invalid-url",
            "name": "Invalid Website",
            "check_interval": 300,
        },
    )
    assert response.status_code == 422


def test_create_duplicate_website():
    website_data = {
        "url": "https://example.com",
        "name": "Example Website",
        "check_interval": 300,
    }
    response1 = client.post("/api/websites/", json=website_data)
    assert response1.status_code == 201
    
    response2 = client.post("/api/websites/", json=website_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_list_websites():
    client.post(
        "/api/websites/",
        json={"url": "https://example1.com", "name": "Example 1", "check_interval": 300},
    )
    client.post(
        "/api/websites/",
        json={"url": "https://example2.com", "name": "Example 2", "check_interval": 300},
    )
    
    response = client.get("/api/websites/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_websites_with_pagination():
    for i in range(5):
        client.post(
            "/api/websites/",
            json={
                "url": f"https://example{i}.com",
                "name": f"Example {i}",
                "check_interval": 300,
            },
        )
    
    response = client.get("/api/websites/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


def test_get_website():
    create_response = client.post(
        "/api/websites/",
        json={"url": "https://example.com", "name": "Example", "check_interval": 300},
    )
    website_id = create_response.json()["id"]
    
    response = client.get(f"/api/websites/{website_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == website_id
    assert data["url"] == "https://example.com"


def test_get_website_not_found():
    response = client.get("/api/websites/9999")
    assert response.status_code == 404


def test_update_website():
    create_response = client.post(
        "/api/websites/",
        json={"url": "https://example.com", "name": "Example", "check_interval": 300},
    )
    website_id = create_response.json()["id"]
    
    response = client.put(
        f"/api/websites/{website_id}",
        json={"name": "Updated Example", "check_interval": 600},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Example"
    assert data["check_interval"] == 600
    assert data["url"] == "https://example.com"


def test_update_website_not_found():
    response = client.put(
        "/api/websites/9999",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


def test_delete_website():
    create_response = client.post(
        "/api/websites/",
        json={"url": "https://example.com", "name": "Example", "check_interval": 300},
    )
    website_id = create_response.json()["id"]
    
    response = client.delete(f"/api/websites/{website_id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/websites/{website_id}")
    assert get_response.status_code == 404


def test_delete_website_not_found():
    response = client.delete("/api/websites/9999")
    assert response.status_code == 404

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.website import Website
from app.models.monitoring_result import MonitoringResult

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


@pytest.fixture
def sample_website():
    db = TestingSessionLocal()
    website = Website(
        url="https://example.com",
        name="Example Website",
        check_interval=300,
        enabled=True,
    )
    db.add(website)
    db.commit()
    db.refresh(website)
    yield website
    db.close()


@pytest.fixture
def sample_monitoring_results(sample_website):
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    
    for i in range(10):
        result = MonitoringResult(
            website_id=sample_website.id,
            timestamp=now - timedelta(hours=i),
            status_code=200 if i % 3 != 0 else 500,
            response_time=0.5 + (i * 0.1),
            success=1 if i % 3 != 0 else 0,
        )
        db.add(result)
    
    db.commit()
    yield
    db.close()


def test_list_monitoring_results(sample_monitoring_results):
    response = client.get("/api/monitoring/results")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 10


def test_list_monitoring_results_with_website_filter(sample_website, sample_monitoring_results):
    response = client.get(f"/api/monitoring/results?website_id={sample_website.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10
    for item in data["items"]:
        assert item["website_id"] == sample_website.id


def test_list_monitoring_results_with_time_filter(sample_website, sample_monitoring_results):
    from urllib.parse import quote
    now = datetime.now(timezone.utc)
    start_time = (now - timedelta(hours=5)).isoformat()
    
    response = client.get(f"/api/monitoring/results?start_time={quote(start_time)}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] <= 10


def test_list_monitoring_results_pagination(sample_monitoring_results):
    response = client.get("/api/monitoring/results?skip=5&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["skip"] == 5
    assert data["limit"] == 3

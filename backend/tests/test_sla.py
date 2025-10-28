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
def sample_website_with_results():
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
    
    now = datetime.now(timezone.utc)
    for i in range(20):
        result = MonitoringResult(
            website_id=website.id,
            timestamp=now - timedelta(hours=i),
            status_code=200 if i % 5 != 0 else 500,
            response_time=0.5 + (i * 0.05),
            success=1 if i % 5 != 0 else 0,
        )
        db.add(result)
    
    db.commit()
    yield website
    db.close()


def test_get_sla_analytics(sample_website_with_results):
    response = client.post("/api/sla/analytics", json={})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    metric = data[0]
    assert "website_id" in metric
    assert "website_name" in metric
    assert "uptime_percentage" in metric
    assert "total_checks" in metric
    assert "successful_checks" in metric
    assert "failed_checks" in metric
    assert "average_response_time" in metric
    assert "start_date" in metric
    assert "end_date" in metric


def test_get_sla_analytics_with_website_filter(sample_website_with_results):
    response = client.post(
        "/api/sla/analytics",
        json={"website_id": sample_website_with_results.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["website_id"] == sample_website_with_results.id
    assert data[0]["total_checks"] == 20
    assert data[0]["successful_checks"] == 16
    assert data[0]["failed_checks"] == 4
    assert data[0]["uptime_percentage"] == 80.0


def test_get_sla_analytics_with_date_range(sample_website_with_results):
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=7)).isoformat()
    end_date = now.isoformat()
    
    response = client.post(
        "/api/sla/analytics",
        json={
            "website_id": sample_website_with_results.id,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_sla_analytics_no_data():
    response = client.post("/api/sla/analytics", json={})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

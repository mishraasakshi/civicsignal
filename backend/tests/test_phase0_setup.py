from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "CivicSignal"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "Amity University Lucknow" in data["pilot_target"]

def test_domain_constants():
    # 8 fixed categories
    assert len(settings.CATEGORIES) == 8
    assert "water_plumbing" in settings.CATEGORIES
    assert "cleanliness" in settings.CATEGORIES
    assert "internet_wifi" in settings.CATEGORIES

    # 2 roles
    assert settings.ROLES == ["reporter", "supervisor"]

    # 7 statuses
    assert "Submitted" in settings.STATUSES
    assert "Needs More Information" in settings.STATUSES

def test_standardized_error_format():
    # Test 404 error response structure: {"error": {"code": str, "message": str}}
    response = client.get("/non-existent-route-for-testing")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert data["error"]["code"] == "NOT_FOUND"

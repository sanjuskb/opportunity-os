from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_application


def test_settings_loaded():
    assert settings.APP_NAME == "Opportunity OS API"
    assert settings.ENVIRONMENT in ["development", "test", "production"]


def test_health_endpoint():
    app = create_application()
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"

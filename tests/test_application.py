from fastapi.testclient import TestClient

from apps.backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "NexoTP"}


def test_home_is_available_through_gateway():
    response = client.get("/")
    assert response.status_code == 200
    assert "NexoTP" in response.text


def test_security_headers_are_present():
    response = client.get("/login")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in response.headers["content-security-policy"]


def test_admin_login_page_is_available():
    response = client.get("/admin-nexotp")
    assert response.status_code == 200
    assert "Admin" in response.text


def test_post_requests_require_csrf_token():
    response = client.post("/login", data={"email": "x@example.com", "password": "invalid"})
    assert response.status_code == 400
    assert response.json()["ok"] is False


def test_csrf_token_is_exposed_to_same_origin_forms():
    response = client.get("/login")
    assert 'meta name="csrf-token" content="' in response.text

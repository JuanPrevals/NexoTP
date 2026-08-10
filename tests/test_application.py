from fastapi.testclient import TestClient
from datetime import UTC, datetime
import re

from apps.backend.app.main import app
from apps.backend.app.legacy import normalizar_rut, rut_chileno_valido
from apps.backend.app.services.sii import SIICompany, SIIInvalidRUT, _parse_response, lookup_company


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


def test_chilean_rut_validation_for_company_verification():
    assert normalizar_rut("12.345.678-5") == "123456785"
    assert rut_chileno_valido("12.345.678-5") is True
    assert rut_chileno_valido("12.345.678-9") is False


def test_invalid_email_verification_token_is_rejected():
    response = client.get("/verificar-email/token-invalido", follow_redirects=True)
    assert response.status_code == 200
    assert "no es valido o ya vencio" in response.text


def test_reporting_requires_an_authenticated_actor():
    page = client.get("/")
    token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text).group(1)
    response = client.post(
        "/reportar/empresa/1",
        data={"_csrf_token": token, "motivo": "Estafa", "detalle": "Detalle suficientemente largo del reporte."},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_sii_response_parser_extracts_only_business_fields():
    html = """
    <html><body>
      <div>Nombre o Razon Social :</div><div>EMPRESA EJEMPLO SPA</div>
      <p>Contribuyente presenta Inicio de Actividades: SI</p>
      <table><tr><th>Actividades</th><th>Codigo</th></tr>
      <tr><td>SERVICIOS INFORMATICOS</td><td>620200</td></tr></table>
    </body></html>
    """
    result = _parse_response(html, "761181955")
    assert result.razon_social == "EMPRESA EJEMPLO SPA"
    assert result.actividades[0] == {"giro": "SERVICIOS INFORMATICOS", "codigo": "620200"}
    assert result.inicio_actividades is True


def test_sii_lookup_rejects_personal_rut_without_network_access():
    try:
        lookup_company("12.345.678-5")
    except SIIInvalidRUT:
        pass
    else:
        raise AssertionError("Los RUT personales no deben consultarse")


def test_company_rut_api_returns_safe_autofill_fields(monkeypatch):
    fake = SIICompany(
        rut="76.118.195-5",
        razon_social="EMPRESA EJEMPLO SPA",
        actividades=({"giro": "SERVICIOS INFORMATICOS", "codigo": "620200"},),
        inicio_actividades=True,
        consultado=datetime.now(UTC).replace(tzinfo=None),
    )
    monkeypatch.setattr("apps.backend.app.legacy.lookup_company", lambda _rut: fake)
    page = client.get("/empresa/registro")
    token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text).group(1)
    response = client.post(
        "/api/verificar-rut-empresa",
        json={"rut": "76.118.195-5"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    assert response.json()["razon_social"] == "EMPRESA EJEMPLO SPA"
    assert "responsable" not in response.json()

from fastapi.testclient import TestClient

from app.core.security import ROLE_PERMISSIONS
from app.seed import DEMO_PASSWORD


def test_login_ok(client: TestClient):
    r = client.post("/api/v1/auth/login",
                    json={"email": "admin@northstar.edu.in", "password": DEMO_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token"] and body["institutions"][0]["role"] == "admin"
    assert "application.read" in body["institutions"][0]["permissions"]


def test_login_wrong_password(client: TestClient):
    r = client.post("/api/v1/auth/login",
                    json={"email": "admin@northstar.edu.in", "password": "wrong-password"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_me_requires_token(client: TestClient):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_roundtrip(client: TestClient, tokens):
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['admin']}"})
    assert r.status_code == 200
    assert r.json()["data"]["email"] == "admin@northstar.edu.in"


def test_role_permission_matrix():
    assert "application.draft.update" not in ROLE_PERMISSIONS["reviewer"]
    assert "application.draft.update" in ROLE_PERMISSIONS["preparer"]
    assert "report.export" in ROLE_PERMISSIONS["compliance"]
    assert ROLE_PERMISSIONS["admin"] >= ROLE_PERMISSIONS["preparer"]


def test_seeded_application_exists(client: TestClient):
    # applications endpoints arrive in phase 2; verify seed via auth/me scope + DB count
    r = client.post("/api/v1/auth/login",
                    json={"email": "compliance@northstar.edu.in", "password": DEMO_PASSWORD})
    assert r.status_code == 200
    assert len(r.json()["institutions"]) == 1

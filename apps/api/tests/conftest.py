import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

# Tests must be deterministic and must never call an external LLM.
settings.LLM_API_KEY = ""

from app.main import create_app  # noqa: E402
from app.seed import DEMO_PASSWORD  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return create_app(db_url="sqlite://", serve_static=False, seed_mode="northstar")


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session")
def inst_id(client):
    r = client.post("/api/v1/auth/login",
                    json={"email": "admin@northstar.edu.in", "password": DEMO_PASSWORD})
    assert r.status_code == 200
    return r.json()["institutions"][0]["institution_id"]


@pytest.fixture(scope="session")
def tokens(client):
    out = {}
    for email in ("admin@northstar.edu.in", "preparer@northstar.edu.in",
                  "compliance@northstar.edu.in", "reviewer@aicte.gov.in"):
        r = client.post("/api/v1/auth/login",
                        json={"email": email, "password": DEMO_PASSWORD})
        assert r.status_code == 200
        out[email.split("@")[0]] = r.json()["token"]
    return out


@pytest.fixture(scope="session")
def app_id(client, tokens):
    r = client.get("/api/v1/applications", headers=auth(tokens["admin"]))
    applications = r.json()["data"]
    return next(a["application_id"] for a in applications
                if a["reference_no"] == "NIT-DEL-2026-0142")


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _uuid4() -> str:
    return str(uuid.uuid4())

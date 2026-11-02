from fastapi.testclient import TestClient

from app.main import create_app

from .conftest import auth


def _aarohan():
    return TestClient(create_app(db_url="sqlite://", serve_static=False, seed_mode="aarohan"))


def _aarohan_token(client):
    r = client.post("/api/v1/auth/login",
                    json={"email": "inst.admin@aarohan.demo", "password": "demo1234"})
    assert r.status_code == 200
    return r.json()["token"]


def test_workflow_catalog(client, tokens):
    r = client.get("/api/v1/workflows", headers=auth(tokens["admin"]))
    assert r.status_code == 200
    keys = {w["key"] for w in r.json()["data"]}
    assert {"eoa_self_disclosure", "increase_intake", "change_of_site", "closure"} <= keys


def test_workflow_detail_stages(client, tokens):
    r = client.get("/api/v1/workflows/increase_intake", headers=auth(tokens["admin"]))
    assert r.status_code == 200
    data = r.json()["data"]
    stage_keys = {s["key"] for s in data["stages"]}
    assert "scrutiny_committee" in stage_keys and "evc" in stage_keys
    assert data["evc"] == "required"


def test_aarohan_demo_application_and_checklist():
    client = _aarohan()
    token = _aarohan_token(client)
    headers = auth(token)
    apps = client.get("/api/v1/applications", headers=headers).json()["data"]
    assert apps and apps[0]["reference_no"] == "DEMO-EVENT-2026-001"
    app_id = apps[0]["application_id"]

    summary = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()["data"]
    assert summary["category"] == "increase_intake"
    assert "Increase in Intake" in summary["category_title"]
    assert any(s["key"] == "programme_details" for s in summary["sections"])

    checklist = client.get(f"/api/v1/applications/{app_id}/checklist",
                           headers=headers).json()["data"]
    assert checklist["missing"] >= 10
    states = {i["key"]: i["state"] for i in checklist["items"]}
    assert states["previous_eoa"] == "uploaded"


def test_create_application_with_category(client, tokens, inst_id):
    r = client.post("/api/v1/applications", json={
        "institution_id": inst_id, "application_type": "Increase in Intake",
        "academic_year": "2027-28", "category": "increase_intake",
    }, headers=auth(tokens["admin"]))
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["category"] == "increase_intake"
    section_keys = {s["key"] for s in data["sections"]}
    assert {"programme_details", "finance"} <= section_keys


def test_invalid_category_rejected(client, tokens, inst_id):
    r = client.post("/api/v1/applications", json={
        "institution_id": inst_id, "application_type": "X",
        "academic_year": "2027-28", "category": "not_a_category",
    }, headers=auth(tokens["admin"]))
    assert r.status_code == 422


def test_demo_reset_requires_admin(client, tokens):
    r = client.post("/api/v1/admin/reset-demo", headers=auth(tokens["reviewer"]))
    assert r.status_code == 403

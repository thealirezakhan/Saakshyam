from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

from .conftest import auth

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "demo-data" / "documents"


def _client():
    return TestClient(create_app(db_url="sqlite://", serve_static=False, seed_mode="aarohan"))


def _login(client):
    r = client.post("/api/v1/auth/login",
                    json={"email": "inst.admin@aarohan.demo", "password": "demo1234"})
    assert r.status_code == 200
    return r.json()["token"]


def _context(client, token):
    headers = auth(token)
    me = client.get("/api/v1/auth/me", headers=headers).json()["data"]
    inst = me["institutions"][0]["institution_id"]
    app = client.get("/api/v1/applications", headers=headers).json()["data"][0]["application_id"]
    return headers, inst, app


def _upload(client, headers, inst, app, name):
    path = DOCS / name
    mime = "application/pdf" if name.endswith(".pdf") else "image/png"
    return client.post("/api/v1/documents/upload",
                       files={"files": (name, path.read_bytes(), mime)},
                       data={"institution_id": inst, "application_id": app},
                       headers=headers)


def test_demo_documents_classified_and_extracted():
    client = _client()
    headers, inst, app = _context(client, _login(client))
    cases = {
        "01_Previous_EOA_Letter_2025-26.pdf": ("previous_eoa", {"eoa_number": "DEMO/EOA/2025-26/0142"}),
        "03_Faculty_Information_Declaration.pdf": ("faculty_declaration", {"total_faculty": "48"}),
        "04_Faculty_Appointment_Qualification_Summary.pdf": ("faculty_statement", {"total_faculty": "45"}),
        "05_Trust_Registration_Certificate.pdf": ("trust_registration", {"registration_number": "MAH/1234/2008"}),
        "07_Payment_Receipt_TER_2026.pdf": ("payment_receipt", {"amount": "350000"}),
        "09_Building_Occupancy_Certificate.pdf": ("occupancy_certificate", {"certificate_number": "OC/PUN/2024/7781"}),
        "10_Fire_Safety_Certificate.pdf": ("fire_noc", {"fire_noc_expiry": "2025-12-31"}),
        "11_Building_Floor_Plan.pdf": ("floor_plan", {"built_up_sqm": "14280"}),
        "14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf": ("scrutiny_report", {"eoa_reference": "DEMO/EOA/2025-26/0143"}),
    }
    for name, (expected_class, expected_fields) in cases.items():
        up = _upload(client, headers, inst, app, name)
        assert up.status_code == 201, name
        did = up.json()["data"][0]["document_id"]
        status = client.get(f"/api/v1/documents/{did}/status", headers=headers).json()["data"]
        assert status["doc_class"] == expected_class, f"{name}: {status}"
        fields = {f["field_name"]: f["value"] for f in
                  client.get(f"/api/v1/documents/{did}/fields", headers=headers).json()["data"]["fields"]}
        for key, value in expected_fields.items():
            assert fields.get(key) == value, f"{name}: {fields}"


def test_reference_and_duplicate_rules_fail():
    client = _client()
    headers, inst, app = _context(client, _login(client))
    for name in ("03_Faculty_Information_Declaration.pdf",
                 "04_Faculty_Appointment_Qualification_Summary.pdf",
                 "10_Fire_Safety_Certificate.pdf",
                 "03_Faculty_Information_Declaration.pdf"):
        assert _upload(client, headers, inst, app, name).status_code == 201

    run = client.post(f"/api/v1/applications/{app}/validations",
                      headers=headers, json={}).json()["data"]
    findings = {f["rule_id"]: f for f in client.get(
        f"/api/v1/validations/{run['run_id']}/findings", headers=headers).json()["data"]}
    assert findings["DEMO-FAC-001"]["status"] == "FAIL"
    assert findings["DEMO-FAC-002"]["status"] == "FAIL"
    assert findings["DEMO-NOC-001"]["status"] == "FAIL"
    assert findings["DEMO-DOC-001"]["status"] == "FAIL"
    assert findings["DEMO-FAC-002"]["institutional_record"]


def test_simulated_verification_outcomes():
    client = _client()
    headers, inst, app = _context(client, _login(client))
    cases = {
        "01_Previous_EOA_Letter_2025-26.pdf": "verified",
        "03_Faculty_Information_Declaration.pdf": "mismatch",
        "05_Trust_Registration_Certificate.pdf": "pending",
        "09_Building_Occupancy_Certificate.pdf": "source_unavailable",
        "10_Fire_Safety_Certificate.pdf": "expired",
        "08_Institutional_Compliance_Declaration.pdf": "manual_review",
    }
    for name, expected in cases.items():
        up = _upload(client, headers, inst, app, name)
        did = up.json()["data"][0]["document_id"]
        res = client.post(f"/api/v1/documents/{did}/verify", headers=headers)
        assert res.status_code == 201, name
        data = res.json()["data"]
        assert data["result"] == expected, f"{name}: {data}"
        assert "SIMULATED" in data["banner"]
        assert data["request_id"].startswith("VR-")

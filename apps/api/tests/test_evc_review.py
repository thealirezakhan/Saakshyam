from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

from .conftest import auth

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "demo-data" / "documents"


def _client():
    return TestClient(create_app(db_url="sqlite://", serve_static=False, seed_mode="aarohan"))


def _login(client, email="inst.admin@aarohan.demo"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert r.status_code == 200
    return r.json()["token"]


def _context(client):
    headers = auth(_login(client))
    me = client.get("/api/v1/auth/me", headers=headers).json()["data"]
    inst = me["institutions"][0]["institution_id"]
    app = client.get("/api/v1/applications", headers=headers).json()["data"][0]["application_id"]
    return headers, inst, app


def _upload(client, headers, inst, app, name, corrected=False):
    path = (DOCS / "corrected" / name) if corrected else (DOCS / name)
    mime = "application/pdf" if name.endswith(".pdf") else "image/png"
    return client.post("/api/v1/documents/upload",
                       files={"files": (name, path.read_bytes(), mime)},
                       data={"institution_id": inst, "application_id": app},
                       headers=headers)


def _run_validation(client, headers, app):
    run = client.post(f"/api/v1/applications/{app}/validations",
                      headers=headers, json={}).json()["data"]
    return {f["rule_id"]: f for f in client.get(
        f"/api/v1/validations/{run['run_id']}/findings", headers=headers).json()["data"]}


def test_infrastructure_analysis_and_evc():
    client = _client()
    headers, inst, app = _context(client)
    for name in ("11_Building_Floor_Plan.pdf",
                 "12_Laboratory_Photograph_CSE.png",
                 "13_Library_Equipment_Evidence.png"):
        assert _upload(client, headers, inst, app, name).status_code == 201

    analysis = client.post(f"/api/v1/applications/{app}/infrastructure/analyze",
                           headers=headers).json()["data"]
    assert analysis["duplicate_groups"], "expected a duplicate image group"
    assert "physical inspection" in analysis["disclaimer"]

    reviewer_headers = auth(_login(client, "scrutiny@aicte.demo"))
    rec = client.post(f"/api/v1/applications/{app}/evc/recommend", headers=reviewer_headers,
                      json={"reason": "Duplicate image", "visit_mode": "online"})
    assert rec.status_code == 200
    assert rec.json()["data"]["status"] == "recommended"

    note = client.post(f"/api/v1/applications/{app}/evc/notes", headers=reviewer_headers,
                       json={"note": "Synthetic visit note."})
    assert note.status_code == 200
    assert note.json()["data"]["notes"]
    summary = client.get(f"/api/v1/applications/{app}", headers=headers).json()["data"]
    assert summary["workflow_stage"] == "evc_notes_recorded"


def test_rectification_lifecycle_resolves_faculty_record():
    client = _client()
    headers, inst, app = _context(client)
    assert _upload(client, headers, inst, app,
                   "04_Faculty_Appointment_Qualification_Summary.pdf").status_code == 201
    findings = _run_validation(client, headers, app)
    target = findings["DEMO-FAC-002"]["finding_id"]
    assert findings["DEMO-FAC-002"]["status"] == "FAIL"

    corrected = _upload(client, headers, inst, app,
                        "17_Faculty_Appointment_Summary_CORRECTED.pdf", corrected=True)
    doc_id = corrected.json()["data"][0]["document_id"]
    clar = client.post(f"/api/v1/findings/{target}/clarification", headers=headers,
                       json={"note": "Corrected faculty summary uploaded.", "document_id": doc_id})
    assert clar.status_code == 200
    assert clar.json()["data"]["lifecycle_status"] == "Correction Submitted"

    res = client.post(f"/api/v1/findings/{target}/revalidate", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["finding"]["lifecycle_status"] == "Resolved"

    history = client.get(f"/api/v1/findings/{target}/history", headers=headers).json()["data"]
    assert len(history) >= 2
    assert any(h["lifecycle_status"] in ("Resolved", "Correction Submitted") for h in history)


def test_reviewer_actions_and_report():
    client = _client()
    headers, inst, app = _context(client)
    _upload(client, headers, inst, app, "10_Fire_Safety_Certificate.pdf")
    findings = _run_validation(client, headers, app)
    finding_id = findings["DEMO-NOC-001"]["finding_id"]

    reviewer_headers = auth(_login(client, "scrutiny@aicte.demo"))
    assert client.post(f"/api/v1/findings/{finding_id}/review/observe",
                       headers=reviewer_headers,
                       json={"note": "Fire NOC appears expired."}).status_code == 200
    assert client.post(f"/api/v1/findings/{finding_id}/review/request-evidence",
                       headers=reviewer_headers,
                       json={"note": "Please upload the renewed NOC."}).status_code == 200
    assert client.post(f"/api/v1/findings/{finding_id}/review/mark-manual",
                       headers=reviewer_headers,
                       json={"note": "Manual verification required."}).status_code == 200

    queue = client.get("/api/v1/review/queue", headers=reviewer_headers).json()["data"]
    assert queue
    report = client.get(f"/api/v1/applications/{app}/report",
                        headers=reviewer_headers).json()["data"]
    assert report["review_actions"]
    assert "verifications" in report

    # No statutory approval endpoint exists.
    assert client.post(f"/api/v1/findings/{finding_id}/review/approve",
                       headers=reviewer_headers, json={}).status_code in (404, 405)


def test_copilot_checklist_verification_infrastructure_intents():
    client = _client()
    headers, inst, app = _context(client)
    conv = client.post("/api/v1/copilot/conversations",
                       json={"application_id": app}, headers=headers).json()["data"]["conversation_id"]

    def tools_for(message: str) -> set[str]:
        r = client.post(f"/api/v1/copilot/conversations/{conv}/messages",
                        headers=headers, json={"content": message})
        assert r.status_code == 200
        out = set()
        for block in r.text.split("\n\n"):
            event = None
            data = None
            for line in block.splitlines():
                if line.startswith("event:"):
                    event = line.removeprefix("event:").strip()
                elif line.startswith("data:"):
                    import json
                    data = json.loads(line.removeprefix("data:").strip())
            if event == "tool.started" and data:
                out.add(data["tool"])
        return out

    assert "get_checklist" in tools_for("What documents do I need for this application?")
    assert "get_verifications" in tools_for("Verify this certificate.")
    assert "analyze_infrastructure" in tools_for(
        "Check whether the infrastructure evidence is sufficient.")

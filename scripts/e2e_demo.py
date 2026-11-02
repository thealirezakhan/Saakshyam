"""End-to-end demo verification (Phase 11).

Runs the full institution + reviewer journey against the real API using an
in-memory database. No external server or LLM is required.

    python scripts/e2e_demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

DOCS = ROOT / "demo-data" / "documents"
PASSWORD = "demo1234"


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, f"login failed for {email}: {r.text}"
    return {"Authorization": "Bearer " + r.json()["token"]}


def upload(client, headers, inst, app, name, corrected=False):
    path = (DOCS / "corrected" / name) if corrected else (DOCS / name)
    mime = "application/pdf" if name.endswith(".pdf") else "image/png"
    r = client.post("/api/v1/documents/upload",
                    files={"files": (name, path.read_bytes(), mime)},
                    data={"institution_id": inst, "application_id": app},
                    headers=headers)
    assert r.status_code == 201, f"upload failed for {name}: {r.text}"
    return r.json()["data"][0]


def main() -> int:
    client = TestClient(create_app(db_url="sqlite://", serve_static=False, seed_mode="aarohan"))
    headers = login(client, "inst.admin@aarohan.demo")
    me = client.get("/api/v1/auth/me", headers=headers).json()["data"]
    inst = me["institutions"][0]["institution_id"]
    app = client.get("/api/v1/applications", headers=headers).json()["data"][0]["application_id"]

    print("1. Tenant:", me["name"], client.get(f"/api/v1/applications/{app}", headers=headers).json()["data"]["reference_no"])

    names = [
        "01_Previous_EOA_Letter_2025-26.pdf", "02_Application_Form_AY2026-27.pdf",
        "03_Faculty_Information_Declaration.pdf", "04_Faculty_Appointment_Qualification_Summary.pdf",
        "05_Trust_Registration_Certificate.pdf", "06_Affidavit_Increase_Intake.pdf",
        "07_Payment_Receipt_TER_2026.pdf", "08_Institutional_Compliance_Declaration.pdf",
        "09_Building_Occupancy_Certificate.pdf", "10_Fire_Safety_Certificate.pdf",
        "11_Building_Floor_Plan.pdf", "12_Laboratory_Photograph_CSE.png",
        "13_Library_Equipment_Evidence.png", "14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf",
        "15_Compliance_Response_2025-26.pdf", "16_Fire_Safety_Certificate_Altered.png",
    ]
    for name in names:
        upload(client, headers, inst, app, name)
    docs = {d["filename"]: d["document_id"] for d in client.get("/api/v1/documents", headers=headers).json()["data"]}
    duplicates = [d for d in client.get("/api/v1/documents", headers=headers).json()["data"] if d["status"] == "needs_review"]
    print(f"2. Uploaded {len(names)} documents; flagged duplicates/review: {len(duplicates)}")

    run = client.post(f"/api/v1/applications/{app}/validations", headers=headers, json={}).json()["data"]
    findings = {f["rule_id"]: f for f in client.get(
        f"/api/v1/validations/{run['run_id']}/findings", headers=headers).json()["data"]}
    for rule in ("DEMO-FAC-001", "DEMO-FAC-002", "DEMO-NOC-001", "DEMO-DOC-001"):
        assert findings[rule]["status"] == "FAIL", (rule, findings[rule])
    print("3. Validation findings:", {r: findings[r]["status"] for r in findings})

    expected = {
        "01_Previous_EOA_Letter_2025-26.pdf": "verified",
        "03_Faculty_Information_Declaration.pdf": "mismatch",
        "05_Trust_Registration_Certificate.pdf": "pending",
        "09_Building_Occupancy_Certificate.pdf": "source_unavailable",
        "10_Fire_Safety_Certificate.pdf": "expired",
        "08_Institutional_Compliance_Declaration.pdf": "manual_review",
    }
    for name, outcome in expected.items():
        res = client.post(f"/api/v1/documents/{docs[name]}/verify", headers=headers).json()["data"]
        assert res["result"] == outcome, (name, res)
        assert "SIMULATED" in res["banner"]
    print("4. Simulated verification outcomes:", list(expected.values()))

    analysis = client.post(f"/api/v1/applications/{app}/infrastructure/analyze", headers=headers).json()["data"]
    assert analysis["duplicate_groups"], analysis
    print("5. Infrastructure duplicate groups:", len(analysis["duplicate_groups"]),
          "| missing:", analysis["missing_evidence"])

    reviewer = login(client, "scrutiny@aicte.demo")
    rec = client.post(f"/api/v1/applications/{app}/evc/recommend", headers=reviewer,
                      json={"reason": "Duplicate image", "visit_mode": "online"})
    assert rec.status_code == 200, rec.text
    note = client.post(f"/api/v1/applications/{app}/evc/notes", headers=reviewer,
                       json={"note": "Synthetic EVC observation."})
    assert note.status_code == 200
    print("6. EVC recommended and note recorded:", note.json()["data"]["status"])

    corrected = upload(client, headers, inst, app, "17_Faculty_Appointment_Summary_CORRECTED.pdf", corrected=True)
    target = findings["DEMO-FAC-002"]["finding_id"]
    clar = client.post(f"/api/v1/findings/{target}/clarification", headers=headers,
                       json={"note": "Corrected faculty summary uploaded.", "document_id": corrected["document_id"]})
    assert clar.status_code == 200
    reval = client.post(f"/api/v1/findings/{target}/revalidate", headers=headers)
    assert reval.status_code == 200, reval.text
    assert reval.json()["data"]["finding"]["lifecycle_status"] == "Resolved", reval.json()
    print("7. Rectification resolved DEMO-FAC-002; history retained:",
          len(client.get(f"/api/v1/findings/{target}/history", headers=headers).json()["data"]), "entries")

    noc = findings["DEMO-NOC-001"]["finding_id"]
    assert client.post(f"/api/v1/findings/{noc}/review/observe", headers=reviewer,
                       json={"note": "Fire NOC expired."}).status_code == 200
    assert client.post(f"/api/v1/findings/{noc}/review/request-evidence", headers=reviewer,
                       json={"note": "Upload renewed NOC."}).status_code == 200
    assert client.post(f"/api/v1/findings/{noc}/review/mark-manual", headers=reviewer,
                       json={"note": "Manual verification."}).status_code == 200
    print("8. Reviewer observations/evidence request recorded")

    report = client.get(f"/api/v1/applications/{app}/report", headers=reviewer).json()["data"]
    for key in ("findings", "verifications", "review_actions", "evc", "statuses"):
        assert key in report, key
    assert report["simulated_sources"] is True
    print("9. Report sections:", ", ".join(sorted(report.keys())))

    queue = client.get("/api/v1/review/queue", headers=reviewer).json()["data"]
    assert queue
    print("10. Review queue applications:", len(queue))
    print("\nE2E DEMO: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from fastapi.testclient import TestClient

from .conftest import auth


def _run(client, tokens, app_id, who="compliance"):
    return client.post(f"/api/v1/applications/{app_id}/validations",
                       json={}, headers=auth(tokens[who]))


def _fresh_application(client, tokens, inst_id):
    r = client.post("/api/v1/applications",
                    json={"institution_id": inst_id, "application_type": "New College",
                          "academic_year": "2026-27"}, headers=auth(tokens["admin"]))
    return r.json()["data"]["application_id"]


def test_validation_generates_findings(client, tokens, inst_id):
    app_id = _fresh_application(client, tokens, inst_id)
    r = _run(client, tokens, app_id)
    assert r.status_code == 201
    run_id = r.json()["data"]["run_id"]
    findings = client.get(f"/api/v1/validations/{run_id}/findings",
                          headers=auth(tokens["compliance"])).json()["data"]
    by_rule = {f["rule_id"]: f for f in findings}
    # fresh application: required fields missing -> FAIL
    assert by_rule["APH-4.1"]["status"] == "FAIL"
    assert by_rule["APH-4.2"]["status"] == "FAIL"
    assert by_rule["APH-8.1"]["status"] == "FAIL"
    # ratio rule cannot evaluate without intake/faculty -> NOT_EVALUATED
    assert by_rule["APH-7.2.1"]["status"] == "NOT_EVALUATED"
    # every finding carries a rule id (AC-07)
    assert all(f["rule_id"].startswith("APH") for f in findings)


def test_cross_doc_mismatch_flagged(client, tokens, inst_id, app_id):
    # application says 48 faculty; upload a statement claiming 51 -> FAIL with evidence
    import io
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Faculty Statement\nTotal Faculty: 51\nSanctioned Intake: 1020")
    content = doc.tobytes()
    doc.close()
    up = client.post("/api/v1/documents/upload",
                     files={"files": ("fac2.pdf", io.BytesIO(content), "application/pdf")},
                     data={"institution_id": inst_id, "application_id": app_id},
                     headers=auth(tokens["preparer"]))
    assert up.status_code == 201
    r = _run(client, tokens, app_id)
    run_id = r.json()["data"]["run_id"]
    findings = client.get(f"/api/v1/validations/{run_id}/findings",
                          headers=auth(tokens["compliance"])).json()["data"]
    f = next(x for x in findings if x["rule_id"] == "APH-13.1")
    assert f["status"] == "FAIL"
    # AC-07 evidence traceability: finding has evidence reference
    detail = client.get(f"/api/v1/findings/{f['finding_id']}",
                        headers=auth(tokens["compliance"])).json()["data"]
    assert detail["evidence"]["extracted_value"] == "51"


def test_revalidation_after_correction(client, tokens, app_id):
    # correct total_faculty to 51 -> ratio rule reruns and passes
    summary = client.get(f"/api/v1/applications/{app_id}",
                         headers=auth(tokens["admin"])).json()["data"]
    field = next(f for s in summary["sections"] for f in s["fields"]
                 if f["key"] == "total_faculty")
    r = client.patch(f"/api/v1/applications/{app_id}/fields/{field['field_id']}",
                     json={"value": "51"}, headers=auth(tokens["preparer"]))
    assert r.status_code == 200
    run = _run(client, tokens, app_id)
    run_id = run.json()["data"]["run_id"]
    findings = client.get(f"/api/v1/validations/{run_id}/findings",
                          headers=auth(tokens["compliance"])).json()["data"]
    ratio = next(x for x in findings if x["rule_id"] == "APH-7.2.1")
    assert ratio["status"] == "PASS"


def test_reviewer_cannot_run_validation(client, tokens, app_id):
    r = _run(client, tokens, app_id, who="reviewer")
    assert r.status_code == 403


def test_rules_listed(client, tokens):
    r = client.get("/api/v1/regulatory-rules", headers=auth(tokens["admin"]))
    assert r.status_code == 200
    assert any(x["rule_id"] == "APH-7.2.1" for x in r.json()["data"])

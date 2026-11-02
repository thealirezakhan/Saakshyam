from fastapi.testclient import TestClient

from .conftest import auth


def test_report_export_requires_permission(client, tokens, app_id):
    r = client.get(f"/api/v1/applications/{app_id}/report/export",
                   headers=auth(tokens["reviewer"]))
    assert r.status_code == 403


def test_report_view_allowed_for_members(client, tokens, app_id):
    r = client.get(f"/api/v1/applications/{app_id}/report", headers=auth(tokens["reviewer"]))
    assert r.status_code == 200


def test_report_sourced_from_persisted_findings(client, tokens, app_id):
    # run a validation first so findings exist
    client.post(f"/api/v1/applications/{app_id}/validations", json={},
                headers=auth(tokens["compliance"]))
    r = client.get(f"/api/v1/applications/{app_id}/report",
                   headers=auth(tokens["compliance"]))
    assert r.status_code == 200
    report = r.json()["data"]
    assert "statuses" in report and "findings" in report
    assert report["findings"], "expected non-empty findings after a validation run"
    # AC-07: findings carry rule reference (rule_id) — evidence where applicable
    for f in report["findings"]:
        assert f["rule_id"].startswith("APH")


def test_report_audited(client, tokens, app_id):
    client.get(f"/api/v1/applications/{app_id}/report/export",
               headers=auth(tokens["compliance"]))
    r = client.get(f"/api/v1/applications/{app_id}/audit", headers=auth(tokens["admin"]))
    actions = [e["action"] for e in r.json()["data"]]
    assert "report.export" in actions

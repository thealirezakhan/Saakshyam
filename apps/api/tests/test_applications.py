from fastapi.testclient import TestClient

from .conftest import auth


def _patch(client, tokens, app_id, field_id, value, who="preparer", version=None):
    body = {"value": value}
    if version is not None:
        body["version"] = version
    return client.patch(f"/api/v1/applications/{app_id}/fields/{field_id}",
                        json=body, headers=auth(tokens[who]))


def _summary(client, tokens, app_id, who="admin"):
    return client.get(f"/api/v1/applications/{app_id}", headers=auth(tokens[who])).json()["data"]


def _find_field(summary, key):
    for s in summary["sections"]:
        for f in s["fields"]:
            if f["key"] == key:
                return f
    raise AssertionError(f"field {key} not found")


def test_list_applications(client, tokens):
    r = client.get("/api/v1/applications", headers=auth(tokens["admin"]))
    assert r.status_code == 200
    assert any(a["reference_no"] == "NIT-DEL-2026-0142" for a in r.json()["data"])


def test_get_application_summary(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    assert summary["reference_no"] == "NIT-DEL-2026-0142"
    assert summary["completion_pct"] > 0
    assert any(s["key"] == "faculty_cadre" for s in summary["sections"])


def test_patch_field_updates_value_and_version(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    field = _find_field(summary, "registered_address")
    assert field["value"] == ""  # left empty by seed for the demo

    r = _patch(client, tokens, app_id, field["field_id"], "Plot 42, Knowledge Park III")
    assert r.status_code == 200
    updated = _find_field(_summary(client, tokens, app_id), "registered_address")
    assert updated["value"] == "Plot 42, Knowledge Park III"
    assert updated["version"] == 1


def test_stale_version_conflict(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    field = _find_field(summary, "contact_email")
    # field is empty; pretend we read version 0 but a concurrent write bumped it
    r1 = _patch(client, tokens, app_id, field["field_id"], "first@example.com", version=0)
    assert r1.status_code == 200
    r2 = _patch(client, tokens, app_id, field["field_id"], "second@example.com", version=0)
    assert r2.status_code == 409


def test_locked_field_rejected(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    field = _find_field(summary, "required_faculty")
    assert field["locked"] is True
    r = _patch(client, tokens, app_id, field["field_id"], "999")
    assert r.status_code == 409


def test_reviewer_cannot_update_draft(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    field = _find_field(summary, "registered_address")
    r = _patch(client, tokens, app_id, field["field_id"], "blocked", who="reviewer")
    assert r.status_code == 403


def test_number_field_type_check(client, tokens, app_id):
    summary = _summary(client, tokens, app_id)
    field = _find_field(summary, "land_area_acres")
    r = _patch(client, tokens, app_id, field["field_id"], "not-a-number")
    assert r.status_code == 422


def test_cross_institution_access_blocked(client, tokens, app_id):
    # create a second institution owned by preparer; admin has no membership there
    r = client.post("/api/v1/institutions", json={"name": "Other College", "code": "OTH"},
                    headers=auth(tokens["preparer"]))
    other_inst = r.json()["data"]["institution_id"]
    r = client.post("/api/v1/applications",
                    json={"institution_id": other_inst,
                          "application_type": "New", "academic_year": "2026-27"},
                    headers=auth(tokens["preparer"]))
    other_app = r.json()["data"]["application_id"]
    # admin has no membership in Other College
    r = client.get(f"/api/v1/applications/{other_app}", headers=auth(tokens["admin"]))
    assert r.status_code == 403


def test_audit_trail_records_field_update(client, tokens, app_id):
    r = client.get(f"/api/v1/applications/{app_id}/audit", headers=auth(tokens["admin"]))
    assert r.status_code == 200
    actions = [e["action"] for e in r.json()["data"]]
    assert "application.field.update" in actions

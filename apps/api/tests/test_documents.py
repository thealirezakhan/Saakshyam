import io

from fastapi.testclient import TestClient

from .conftest import auth


def _make_faculty_pdf() -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Faculty Statement - Northstar Institute of Technology\n"
                               "Total Faculty: 48\n"
                               "Sanctioned Intake: 1020\n"
                               "Ph.D holders: 42")
    buf = doc.tobytes()
    doc.close()
    return buf


def _make_land_pdf() -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Land Registry Deed\nPlot 42, Knowledge Park III\n"
                               "Land Area: 5.20 Acres")
    buf = doc.tobytes()
    doc.close()
    return buf


def _upload(client, tokens, content, filename, who="preparer", inst_id=None, app_id=None):
    files = {"files": (filename, io.BytesIO(content), "application/pdf")}
    data = {}
    if inst_id:
        data["institution_id"] = inst_id
    if app_id:
        data["application_id"] = app_id
    return client.post("/api/v1/documents/upload", files=files, data=data,
                       headers=auth(tokens[who]))


def test_upload_and_extract_faculty(client, tokens, inst_id, app_id):
    r = _upload(client, tokens, _make_faculty_pdf(), "faculty.pdf",
                inst_id=inst_id, app_id=app_id)
    assert r.status_code == 201
    doc_id = r.json()["data"][0]["document_id"]
    assert r.json()["data"][0]["duplicate"] is False

    status = client.get(f"/api/v1/documents/{doc_id}/status",
                        headers=auth(tokens["preparer"])).json()["data"]
    assert status["status"] == "succeeded"
    assert status["doc_class"] == "faculty_statement"

    fields = client.get(f"/api/v1/documents/{doc_id}/fields",
                        headers=auth(tokens["preparer"])).json()["data"]["fields"]
    by_name = {f["field_name"]: f for f in fields}
    assert by_name["total_faculty"]["value"] == "48"
    assert by_name["total_faculty"]["page"] >= 1  # AC-02 evidence reference
    assert by_name["sanctioned_intake"]["value"] == "1020"


def test_upload_land_deed_extracts_acres(client, tokens, inst_id, app_id):
    r = _upload(client, tokens, _make_land_pdf(), "land.pdf",
                inst_id=inst_id, app_id=app_id)
    doc_id = r.json()["data"][0]["document_id"]
    fields = client.get(f"/api/v1/documents/{doc_id}/fields",
                        headers=auth(tokens["preparer"])).json()["data"]["fields"]
    by_name = {f["field_name"]: f for f in fields}
    assert by_name["land_area_acres"]["value"] == "5.20"


def test_duplicate_upload_detected(client, tokens, inst_id, app_id):
    content = _make_faculty_pdf()
    r1 = _upload(client, tokens, content, "faculty.pdf", inst_id=inst_id, app_id=app_id)
    r2 = _upload(client, tokens, content, "faculty.pdf", inst_id=inst_id, app_id=app_id)
    first = r1.json()["data"][0]
    second = r2.json()["data"][0]
    assert second["duplicate"] is True
    assert second["document_id"] != first["document_id"]
    assert second["duplicate_of"] == first["document_id"]
    status = client.get(f"/api/v1/documents/{second['document_id']}/status",
                        headers=auth(tokens["preparer"])).json()["data"]
    assert status["status"] == "needs_review"


def test_image_upload_needs_review(client, tokens, inst_id, app_id):
    # minimal 1x1 PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
    )
    r = _upload(client, tokens, png, "scan.png", inst_id=inst_id, app_id=app_id)
    doc_id = r.json()["data"][0]["document_id"]
    status = client.get(f"/api/v1/documents/{doc_id}/status",
                        headers=auth(tokens["preparer"])).json()["data"]
    assert status["status"] == "needs_review"


def test_reviewer_cannot_upload(client, tokens, inst_id, app_id):
    r = _upload(client, tokens, _make_faculty_pdf(), "x.pdf", who="reviewer",
                inst_id=inst_id, app_id=app_id)
    assert r.status_code == 403


def test_list_documents_scoped(client, tokens, inst_id):
    r = client.get("/api/v1/documents", headers=auth(tokens["preparer"]))
    assert r.status_code == 200
    assert all(d["institution_id"] == inst_id for d in r.json()["data"])

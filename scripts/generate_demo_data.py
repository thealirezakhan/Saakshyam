"""Generate deterministic synthetic demo data for the AICTE Copilot MVP.

Creates:
  demo-data/documents/*.pdf|png        (16 primary files)
  demo-data/documents/corrected/*.pdf  (2 correction files)
  demo-data/document_metadata.json
  demo-data/dataset.json

Every document is fictional and carries the synthetic watermark.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "demo-data" / "documents"
CORRECTED = DOCS / "corrected"
WATERMARK = "SYNTHETIC DEMO DATA - NOT AN OFFICIAL AICTE DOCUMENT"
INSTITUTION = "Aarohan Institute of Technology, Pune"
APP_ID = "DEMO-EVENT-2026-001"
INST_ID = "DEMO-AICTE-0001"


def _pdf(path: Path, title: str, lines: list[str]) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((60, 60), INSTITUTION, fontsize=11, fontname="helv")
    page.insert_text((60, 82), title, fontsize=16, fontname="hebo")
    page.draw_line(fitz.Point(60, 92), fitz.Point(535, 92), color=(0.3, 0.3, 0.3))
    y = 120
    for line in lines:
        page.insert_text((60, y), line, fontsize=10, fontname="helv")
        y += 17
    page.insert_text((60, 810), WATERMARK, fontsize=8, fontname="helv", color=(0.65, 0, 0))
    doc.set_metadata({"title": title, "author": "Synthetic demo", "subject": APP_ID})
    doc.save(path)
    doc.close()


def _image(path: Path, heading: str, caption: str, altered: bool = False) -> None:
    img = Image.new("RGB", (1200, 800), (245, 246, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 1160, 760], outline=(60, 70, 90), width=3)
    d.text((70, 70), INSTITUTION, fill=(30, 40, 60))
    d.text((70, 100), heading, fill=(20, 30, 60))
    d.rectangle([70, 140, 1130, 640], fill=(210, 220, 225), outline=(80, 90, 110), width=2)
    d.text((90, 170), caption, fill=(40, 50, 70))
    if altered:
        d.rectangle([700, 430, 1040, 500], fill=(255, 245, 200), outline=(200, 60, 60), width=3)
        d.text((715, 445), "valid till: 2027-03-31", fill=(150, 20, 20))
        d.text((715, 470), "[date field visually altered]", fill=(150, 20, 20))
    d.text((70, 700), WATERMARK, fill=(150, 20, 20))
    img.save(path, format="PNG")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    CORRECTED.mkdir(parents=True, exist_ok=True)

    _pdf(DOCS / "01_Previous_EOA_Letter_2025-26.pdf", "EXTENSION OF APPROVAL (EoA) LETTER", [
        "EoA No: DEMO/EOA/2025-26/0142",
        "Institution: Aarohan Institute of Technology",
        "Academic Year: 2025-26",
        "Approved Intake: 240",
        "Land Area: 5.20 Acres",
        "Approved Programmes: CSE (120), ECE (60), Mechanical (60)",
        "This approval is valid till 31 March 2026.",
        "Status: Extension of Approval granted for AY 2025-26.",
    ])
    _pdf(DOCS / "02_Application_Form_AY2026-27.pdf", "APPLICATION FORM - AY 2026-27", [
        "Application No: DEMO-EVENT-2026-001",
        "Category: Increase in Intake / Additional Course",
        "Academic Year: 2026-27",
        "Institution: Aarohan Institute of Technology, Pune",
        "Proposed Intake: 330",
        "Proposed CSE: 180, ECE: 90, Mechanical: 60",
        "Total Faculty: 48",
        "Fire NOC valid till: 2027-03-31",
        "Declaration: information submitted is true to the best of our knowledge.",
    ])
    _pdf(DOCS / "03_Faculty_Information_Declaration.pdf", "FACULTY INFORMATION DECLARATION", [
        "Declaration for AY 2026-27",
        "Institution: Aarohan Institute of Technology, Pune",
        "Total Faculty: 48",
        "Ph.D holders: 30",
        "We declare the above faculty strength for the proposed intake.",
        "Note: this figure is a declaration; see the appointment summary for details.",
    ])
    _pdf(DOCS / "04_Faculty_Appointment_Qualification_Summary.pdf", "FACULTY APPOINTMENT & QUALIFICATION SUMMARY", [
        "Institution: Aarohan Institute of Technology, Pune",
        "Total Faculty: 45",
        "Ph.D holders: 27",
        "CSE: 18, ECE: 14, Mechanical: 13",
        "The list below is the current appointment record at the time of application.",
    ])
    _pdf(DOCS / "05_Trust_Registration_Certificate.pdf", "TRUST / SOCIETY REGISTRATION CERTIFICATE", [
        "Trust: Aarohan Education Society",
        "Registration No: MAH/1234/2008",
        "Registration Date: 2008-06-14",
        "Registering Authority: Office of the Charity Commissioner, Maharashtra (simulated)",
        "Status: registered society in good standing.",
    ])
    _pdf(DOCS / "06_Affidavit_Increase_Intake.pdf", "AFFIDAVIT FOR INCREASE IN INTAKE", [
        "Deponent: Aarohan Education Society",
        "Institution: Aarohan Institute of Technology",
        "City: Nagpur",
        "Affidavit Date: 2026-01-10",
        "We affirm that the information and documents submitted are true.",
        "This is a synthetic illustrative affidavit, not an official form.",
    ])
    _pdf(DOCS / "07_Payment_Receipt_TER_2026.pdf", "TECHNICAL EDUCATION REGULATORY (TER) PAYMENT RECEIPT", [
        "Receipt No: TER/2026/000981",
        "Institution: Aarohan Institute of Technology, Pune",
        "Amount: 350000",
        "Payment Date: 2026-01-12",
        "Payment mode: online (simulated gateway)",
        "Status: received.",
    ])
    _pdf(DOCS / "08_Institutional_Compliance_Declaration.pdf", "INSTITUTIONAL COMPLIANCE DECLARATION", [
        "Institution: Aarohan Institute of Technology, Pune",
        "Declaration Date: 2026-01-11",
        "We confirm compliance with applicable norms for the proposed intake.",
        "Signature of Principal: ______________________",
        "Note: signature field is blank in this synthetic copy.",
    ])
    _pdf(DOCS / "09_Building_Occupancy_Certificate.pdf", "BUILDING OCCUPANCY CERTIFICATE", [
        "Certificate No: OC/PUN/2024/7781",
        "Issuer: Pune Municipal Corporation (simulated)",
        "Valid Until: 2029-03-31",
        "Built-up Area: 14280 sqm",
        "Status: valid.",
    ])
    _pdf(DOCS / "10_Fire_Safety_Certificate.pdf", "FIRE SAFETY CERTIFICATE (NOC)", [
        "NOC No: FS/PUN/2024/5567",
        "Issuer: Fire and Emergency Services, Pune (simulated)",
        "Valid till: 2025-12-31",
        "Premises: Aarohan Institute of Technology, Pune",
        "Status: expired for AY 2026-27.",
    ])
    _pdf(DOCS / "11_Building_Floor_Plan.pdf", "BUILDING FLOOR PLAN", [
        "Institution: Aarohan Institute of Technology, Pune",
        "Built-up Area: 14280 sqm",
        "Floors: 4",
        "Blocks: Academic, Laboratory, Library, Administrative",
        "Note: synthetic illustrative floor plan, not an official drawing.",
    ])
    _pdf(DOCS / "14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf",
         "PREVIOUS SCRUTINY DEFICIENCY REPORT", [
        "EoA Reference: DEMO/EOA/2025-26/0143",
        "Report Date: 2025-08-20",
        "Observation 1: Faculty shortfall (42 on record vs 45 listed).",
        "Observation 2: Fire NOC renewal required.",
        "Status: deficiencies communicated to the institution.",
    ])
    _pdf(DOCS / "15_Compliance_Response_2025-26.pdf", "INSTITUTIONAL COMPLIANCE RESPONSE", [
        "Response Reference: AIT/COMP/2025-26/07",
        "Response Date: 2025-09-10",
        "We have initiated faculty recruitment and fire NOC renewal.",
        "Supporting documents are attached in the portal (simulated).",
    ])

    # Duplicate evidence: identical bytes on purpose.
    lab = DOCS / "12_Laboratory_Photograph_CSE.png"
    _image(lab, "INFRASTRUCTURE EVIDENCE", "CSE Laboratory - synthetic illustrative photograph")
    (DOCS / "13_Library_Equipment_Evidence.png").write_bytes(lab.read_bytes())

    _image(DOCS / "16_Fire_Safety_Certificate_Altered.png", "FIRE SAFETY CERTIFICATE (SCAN)",
           "Certificate No: FS/PUN/2024/5567", altered=True)

    _pdf(CORRECTED / "17_Faculty_Appointment_Summary_CORRECTED.pdf",
         "FACULTY APPOINTMENT & QUALIFICATION SUMMARY (CORRECTED)", [
        "Institution: Aarohan Institute of Technology, Pune",
        "Total Faculty: 42",
        "Ph.D holders: 24",
        "CSE: 17, ECE: 13, Mechanical: 12",
        "This corrected summary reconciles with the institutional record.",
    ])
    _pdf(CORRECTED / "18_Fire_Safety_Certificate_RENEWED.pdf",
         "FIRE SAFETY CERTIFICATE (RENEWED)", [
        "NOC No: FS/PUN/2026/1189",
        "Issuer: Fire and Emergency Services, Pune (simulated)",
        "Valid till: 2027-03-31",
        "Premises: Aarohan Institute of Technology, Pune",
        "Status: valid.",
    ])

    _write_metadata()
    _write_dataset()
    print("generated", len(list(DOCS.glob("*"))), "primary files")


def _file_meta(name: str, category: str, issuer: str, issued: str, expiry: str | None,
               ref: str, fields: dict, outcome: str, findings: list[str]) -> dict:
    return {
        "document_id": "DOC-" + hashlib.sha256(name.encode()).hexdigest()[:8].upper(),
        "filename": name,
        "application_id": APP_ID,
        "institution_id": INST_ID,
        "category": category,
        "issuer": issuer,
        "issue_date": issued,
        "expiry_date": expiry,
        "reference_number": ref,
        "institution_name": INSTITUTION,
        "extractable_fields": fields,
        "expected_validation_outcome": outcome,
        "associated_findings": findings,
        "synthetic": True,
    }


def _write_metadata() -> None:
    meta = [
        _file_meta("01_Previous_EOA_Letter_2025-26.pdf", "previous_eoa", "AICTE (simulated)",
                   "2025-04-01", "2026-03-31", "DEMO/EOA/2025-26/0142",
                   {"eoa_number": "DEMO/EOA/2025-26/0142", "approved_intake": "240"},
                   "valid", []),
        _file_meta("02_Application_Form_AY2026-27.pdf", "application_form", "Institution",
                   "2026-01-11", None, APP_ID,
                   {"application_number": APP_ID, "proposed_intake": "330"},
                   "valid", []),
        _file_meta("03_Faculty_Information_Declaration.pdf", "faculty_declaration", "Institution",
                   "2026-01-10", None, "AIT/FAC/2026-01",
                   {"total_faculty": "48", "faculty_phd_count": "30"},
                   "inconsistent", ["DEMO-FAC-001"]),
        _file_meta("04_Faculty_Appointment_Qualification_Summary.pdf", "faculty_summary", "Institution",
                   "2026-01-10", None, "AIT/FAC/2026-02",
                   {"total_faculty": "45", "faculty_phd_count": "27"},
                   "inconsistent", ["DEMO-FAC-001", "DEMO-FAC-002"]),
        _file_meta("05_Trust_Registration_Certificate.pdf", "trust_registration", "Charity Commissioner (simulated)",
                   "2008-06-14", None, "MAH/1234/2008",
                   {"registration_number": "MAH/1234/2008"},
                   "verification_pending", ["DEMO-VER-001"]),
        _file_meta("06_Affidavit_Increase_Intake.pdf", "affidavit", "Institution",
                   "2026-01-10", None, "AIT/AFF/2026-01",
                   {"deponent": "Aarohan Education Society", "city": "Nagpur"},
                   "inconsistent", ["DEMO-ID-001"]),
        _file_meta("07_Payment_Receipt_TER_2026.pdf", "payment_receipt", "AICTE (simulated)",
                   "2026-01-12", None, "TER/2026/000981",
                   {"receipt_number": "TER/2026/000981", "amount": "350000"},
                   "valid", []),
        _file_meta("08_Institutional_Compliance_Declaration.pdf", "compliance_declaration", "Institution",
                   "2026-01-11", None, "AIT/COMP/2026-01",
                   {"declaration_date": "2026-01-11"},
                   "incomplete", ["DEMO-CHK-001"]),
        _file_meta("09_Building_Occupancy_Certificate.pdf", "occupancy_certificate", "Municipal Corporation (simulated)",
                   "2024-04-01", "2029-03-31", "OC/PUN/2024/7781",
                   {"certificate_number": "OC/PUN/2024/7781"},
                   "valid", []),
        _file_meta("10_Fire_Safety_Certificate.pdf", "fire_noc", "Fire Services (simulated)",
                   "2024-01-01", "2025-12-31", "FS/PUN/2024/5567",
                   {"noc_number": "FS/PUN/2024/5567", "valid_until": "2025-12-31"},
                   "expired", ["DEMO-NOC-001"]),
        _file_meta("11_Building_Floor_Plan.pdf", "floor_plan", "Institution",
                   "2024-05-01", None, "AIT/PLAN/2024-01",
                   {"built_up_sqm": "14280", "floors": "4"},
                   "valid", []),
        _file_meta("12_Laboratory_Photograph_CSE.png", "infrastructure_photo", "Institution",
                   "2025-12-01", None, "AIT/PHOTO/2025-01",
                   {"label": "CSE Laboratory"}, "duplicate", ["DEMO-DOC-001"]),
        _file_meta("13_Library_Equipment_Evidence.png", "infrastructure_photo", "Institution",
                   "2025-12-01", None, "AIT/PHOTO/2025-02",
                   {"label": "Library"}, "duplicate", ["DEMO-DOC-001"]),
        _file_meta("14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf", "scrutiny_report", "AICTE (simulated)",
                   "2025-08-20", None, "DEMO/EOA/2025-26/0143",
                   {"eoa_reference": "DEMO/EOA/2025-26/0143"},
                   "reference_mismatch", ["DEMO-DOC-002"]),
        _file_meta("15_Compliance_Response_2025-26.pdf", "compliance_response", "Institution",
                   "2025-09-10", None, "AIT/COMP/2025-26/07",
                   {"response_reference": "AIT/COMP/2025-26/07"},
                   "valid", []),
        _file_meta("16_Fire_Safety_Certificate_Altered.png", "fire_noc_scan", "Fire Services (simulated)",
                   "2024-01-01", "2027-03-31", "FS/PUN/2024/5567",
                   {"valid_until": "2027-03-31"},
                   "anomaly_review", ["DEMO-ANOM-001"]),
        _file_meta("corrected/17_Faculty_Appointment_Summary_CORRECTED.pdf", "faculty_summary", "Institution",
                   "2026-01-20", None, "AIT/FAC/2026-03",
                   {"total_faculty": "42", "faculty_phd_count": "24"},
                   "corrected", ["DEMO-FAC-001", "DEMO-FAC-002"]),
        _file_meta("corrected/18_Fire_Safety_Certificate_RENEWED.pdf", "fire_noc", "Fire Services (simulated)",
                   "2026-01-20", "2027-03-31", "FS/PUN/2026/1189",
                   {"valid_until": "2027-03-31"},
                   "corrected", ["DEMO-NOC-001"]),
    ]
    (ROOT / "demo-data" / "document_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_dataset() -> None:
    dataset = {
        "synthetic": True,
        "notice": "SYNTHETIC DEMO DATA - NOT AN OFFICIAL AICTE DOCUMENT",
        "institution": {
            "institution_id": INST_ID,
            "name": "Aarohan Institute of Technology",
            "code": "AIT-PUNE",
            "city": "Pune",
            "state": "Maharashtra",
            "trust": "Aarohan Education Society",
        },
        "users": [
            {"email": "inst.admin@aarohan.demo", "name": "Meera Kulkarni", "role": "admin"},
            {"email": "scrutiny@aicte.demo", "name": "Reviewer S. Nair", "role": "reviewer"},
            {"email": "evc@aicte.demo", "name": "EVC Member R. Deshpande", "role": "evc"},
            {"email": "sysadmin@aicte.demo", "name": "System Administrator", "role": "admin"},
        ],
        "application": {
            "application_id": APP_ID,
            "institution_id": INST_ID,
            "category": "increase_intake",
            "application_type": "Increase in Intake / Additional Course",
            "academic_year": "2026-27",
            "proposed_intake": 330,
            "existing_intake": 240,
        },
        "historical_records": {
            "approved_programmes": {"CSE": 120, "ECE": 60, "Mechanical": 60},
            "approved_intake": 240,
            "faculty_on_record": 42,
            "faculty_phd_on_record": 24,
            "land_acres": 5.20,
            "previous_eoa": "DEMO/EOA/2025-26/0142",
            "previous_observation": "Faculty shortfall (42 on record vs 45 listed); fire NOC renewal required.",
        },
        "expected_findings": [
            {"rule_id": "DEMO-FAC-001", "severity": "High", "title": "Faculty count inconsistency",
             "values": {"declared": 48, "list": 45, "record": 42}},
            {"rule_id": "DEMO-FAC-002", "severity": "High", "title": "Faculty vs institutional record",
             "values": {"list": 45, "record": 42}},
            {"rule_id": "DEMO-NOC-001", "severity": "High", "title": "Fire NOC expired",
             "values": {"document": "2025-12-31", "application": "2027-03-31"}},
            {"rule_id": "DEMO-DOC-001", "severity": "Medium", "title": "Duplicate/reused evidence",
             "values": {"documents": [12, 13]}},
            {"rule_id": "DEMO-DOC-002", "severity": "Medium", "title": "Inconsistent reference",
             "values": {"eoa": "0142", "scrutiny": "0143"}},
            {"rule_id": "DEMO-ID-001", "severity": "Medium", "title": "Institution detail inconsistency",
             "values": {"affidavit_city": "Nagpur", "actual_city": "Pune"}},
            {"rule_id": "DEMO-INF-001", "severity": "Medium", "title": "Infrastructure evidence gap",
             "values": {"missing": "library equipment list"}},
            {"rule_id": "DEMO-VER-001", "severity": "Informational", "title": "Verification pending",
             "values": {"document": "trust_registration"}},
            {"rule_id": "DEMO-CHK-001", "severity": "Medium", "title": "Incomplete declaration",
             "values": {"document": "compliance_declaration", "missing": "signature"}},
        ],
        "verification_cases": [
            {"document": "01_Previous_EOA_Letter_2025-26.pdf", "result": "verified"},
            {"document": "03_Faculty_Information_Declaration.pdf", "result": "mismatch"},
            {"document": "05_Trust_Registration_Certificate.pdf", "result": "pending"},
            {"document": "08_Institutional_Compliance_Declaration.pdf", "result": "manual_review"},
            {"document": "09_Building_Occupancy_Certificate.pdf", "result": "source_unavailable"},
            {"document": "10_Fire_Safety_Certificate.pdf", "result": "expired"},
        ],
        "audit_seed": [
            {"action": "application.create", "target": APP_ID},
            {"action": "document.upload", "target": "01_Previous_EOA_Letter_2025-26.pdf"},
            {"action": "validation.run", "target": "initial"},
        ],
    }
    (ROOT / "demo-data" / "dataset.json").write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

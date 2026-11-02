from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .core.security import hash_password
from .models import (
    Application,
    ApplicationField,
    ApplicationSection,
    Document,
    DocumentProcessingRun,
    DocumentVersion,
    EvidenceReference,
    ExtractedField,
    Institution,
    InstitutionMembership,
    InstitutionalReferenceRecord,
    RegulatoryRule,
    RegulatorySource,
    User,
)

DEMO_PASSWORD = "demo1234"

SECTIONS: list[dict] = [
    {
        "key": "institution_profile", "title": "Institution Profile & Location",
        "fields": [
            ("institution_name", "Institution Full Legal Name", "text", True, True),
            ("registered_address", "Registered Parcel Address", "text", True, False),
            ("urban_category", "Urban Category / Location Norm", "text", True, False),
            ("contact_email", "Institution Contact Email", "text", False, False),
            ("establishment_year", "Year of Establishment", "number", True, False),
        ],
    },
    {
        "key": "faculty_cadre", "title": "Faculty Cadre & Cadre Ratios",
        "fields": [
            ("sanctioned_intake", "Sanctioned Intake", "number", True, False),
            ("total_faculty", "Verified Faculty (Count)", "number", True, False),
            ("required_faculty", "Required Faculty", "number", True, True),
            ("faculty_phd_count", "Faculty with Ph.D (Count)", "number", True, False),
        ],
    },
    {
        "key": "land_infrastructure", "title": "Land & Built-up Norms",
        "fields": [
            ("land_area_acres", "Land Area (Acres)", "number", True, False),
            ("built_up_sqm", "Total Built-up Area (sq.m)", "number", True, False),
        ],
    },
    {
        "key": "statutory_approvals", "title": "Statutory Approvals & Safety",
        "fields": [
            ("fire_noc_expiry", "Fire Safety NOC Valid Until", "date", True, False),
            ("occupancy_certificate", "Occupancy Certificate", "text", True, False),
            ("building_stability", "Building Stability Certificate", "text", True, False),
        ],
    },
]

EXTRA_SECTIONS: dict[str, list[dict]] = {
    "increase_intake": [
        {
            "key": "programme_details", "title": "Programme & Proposed Intake",
            "fields": [
                ("programme_name", "Programme", "text", True, False),
                ("existing_intake", "Existing Approved Intake", "number", True, False),
                ("proposed_intake", "Proposed Intake", "number", True, False),
            ],
        },
        {
            "key": "finance", "title": "Financial Records",
            "fields": [
                ("audited_financials", "Audited Financial Statements", "text", True, False),
            ],
        },
    ],
}


def sections_for(category: str) -> list[dict]:
    """Base sections plus category-specific sections, in display order."""
    extras = EXTRA_SECTIONS.get(category, [])
    if not extras:
        return list(SECTIONS)
    after_profile = [e for e in extras if e["key"] == "programme_details"]
    tail = [e for e in extras if e["key"] != "programme_details"]
    return [SECTIONS[0]] + after_profile + list(SECTIONS[1:]) + tail


SEED_VALUES: dict[str, str] = {
    "institution_name": "Northstar Institute of Technology",
    "urban_category": "Urban / National Capital Region (2.50 Acre norm)",
    "sanctioned_intake": "1020",
    "total_faculty": "48",
    "required_faculty": "51",
    "faculty_phd_count": "42",
    "land_area_acres": "5.20",
    "built_up_sqm": "14280",
    "fire_noc_expiry": "2026-05-15",
    "occupancy_certificate": "Valid — issued 2024",
    # registered_address, contact_email, establishment_year left empty for the demo
    # (copilot fills them from uploaded evidence)
}


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(User)) > 0:
        return
    seed_identity(db)
    application = seed_application(db)
    seed_regulations(db)
    seed_documents(db, application)
    db.commit()


def seed_identity(db: Session) -> None:
    inst = Institution(name="Northstar Institute of Technology", code="NIT-DEL")
    db.add(inst)
    db.flush()
    users = [
        ("admin@northstar.edu.in", "Dr. Ramanathan", "admin"),
        ("preparer@northstar.edu.in", "Priya Sharma", "preparer"),
        ("compliance@northstar.edu.in", "Vikram Mehta", "compliance"),
        ("reviewer@aicte.gov.in", "Official Reviewer", "reviewer"),
    ]
    for email, name, role in users:
        user = User(email=email, name=name, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()
        db.add(InstitutionMembership(user_id=user.id, institution_id=inst.id, role=role))


def _build_application(db: Session, *, institution_id, reference_no: str,
                       application_type: str, academic_year: str, category: str,
                       values: dict[str, str]) -> Application:
    application = Application(
        institution_id=institution_id, reference_no=reference_no,
        application_type=application_type, academic_year=academic_year,
        category=category, workflow_stage="initial_validation", status="draft",
    )
    db.add(application)
    db.flush()
    from .models import ApplicationFieldValue
    for i, spec in enumerate(sections_for(category)):
        section = ApplicationSection(
            application_id=application.id, key=spec["key"],
            title=spec["title"], order=i + 1,
        )
        db.add(section)
        db.flush()
        for j, (key, label, type_, required, locked) in enumerate(spec["fields"]):
            field = ApplicationField(
                section_id=section.id, key=key, label=label, type=type_,
                required=required, locked=locked, order=j + 1,
            )
            db.add(field)
            db.flush()
            if key in values:
                db.add(ApplicationFieldValue(field_id=field.id, value=values[key]))
    return application


def seed_application(db: Session) -> Application:
    inst = db.scalar(select(Institution).where(Institution.code == "NIT-DEL"))
    return _build_application(
        db, institution_id=inst.id, reference_no="NIT-DEL-2026-0142",
        application_type="Extension of Approval (EoA)", academic_year="2026-27",
        category="eoa_self_disclosure", values=SEED_VALUES,
    )


AAROHAN_VALUES: dict[str, str] = {
    "institution_name": "Aarohan Institute of Technology",
    "registered_address": "Survey No. 42, Baner Road, Pune, Maharashtra 411045",
    "urban_category": "Urban / Pune Municipal Corporation (2.50 Acre norm)",
    "contact_email": "registrar@aarohan.demo",
    "establishment_year": "2008",
    "programme_name": "Computer Science and Engineering",
    "existing_intake": "240",
    "proposed_intake": "330",
    "sanctioned_intake": "330",
    "total_faculty": "48",
    "required_faculty": "17",
    "faculty_phd_count": "30",
    "land_area_acres": "5.20",
    "built_up_sqm": "14280",
    "fire_noc_expiry": "2027-03-31",
    "occupancy_certificate": "OC/PUN/2024/7781",
    # building_stability intentionally left empty to demonstrate a deficiency
    "audited_financials": "Audited FY 2024-25",
}

AAROHAN_REFERENCES: list[tuple[str, str, str, str]] = [
    ("approved_intake", "240", "Simulated AICTE archive", "2025-26"),
    ("approved_programmes", "CSE:120;ECE:60;Mechanical:60", "Simulated AICTE archive", "2025-26"),
    ("faculty_on_record", "42", "Simulated institutional record", "2026-01"),
    ("faculty_phd_on_record", "24", "Simulated institutional record", "2026-01"),
    ("land_acres", "5.20", "Simulated institutional record", "2026-01"),
    ("previous_eoa", "DEMO/EOA/2025-26/0142", "Simulated AICTE archive", "2025-26"),
]


def seed_demo_if_empty(db: Session) -> None:
    """Seed the SIH demo tenant (Aarohan) when DEMO_MODE=aarohan."""
    if db.scalar(select(func.count()).select_from(User)) > 0:
        return
    seed_aarohan(db)
    seed_regulations(db)
    db.commit()


def seed_aarohan(db: Session) -> tuple[Institution, Application]:
    inst = Institution(name="Aarohan Institute of Technology", code="AIT-PUNE")
    db.add(inst)
    db.flush()

    users = [
        ("inst.admin@aarohan.demo", "Meera Kulkarni", "preparer"),
        ("scrutiny@aicte.demo", "Reviewer S. Nair", "reviewer"),
        ("evc@aicte.demo", "EVC Member R. Deshpande", "evc"),
        ("sysadmin@aicte.demo", "System Administrator", "admin"),
    ]
    admin_user = None
    for email, name, role in users:
        user = User(email=email, name=name, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()
        db.add(InstitutionMembership(user_id=user.id, institution_id=inst.id, role=role))
        if email == "sysadmin@aicte.demo":
            admin_user = user

    application = _build_application(
        db, institution_id=inst.id, reference_no="DEMO-EVENT-2026-001",
        application_type="Increase in Intake / Additional Course", academic_year="2026-27",
        category="increase_intake", values=AAROHAN_VALUES,
    )

    for key, value, label, as_of in AAROHAN_REFERENCES:
        db.add(InstitutionalReferenceRecord(
            institution_id=inst.id, key=key, value=value, source_label=label, as_of=as_of))

    _seed_historical_documents(db, application, inst, admin_user)
    return inst, application


def _seed_historical_documents(db: Session, application: Application,
                               inst: Institution, actor) -> None:
    import hashlib

    specs = [
        ("01_Previous_EOA_Letter_2025-26.pdf", "previous_eoa",
         "Prior EoA verified - approved intake 240.",
         [("eoa_number", "DEMO/EOA/2025-26/0142", 1,
           "EoA No: DEMO/EOA/2025-26/0142"),
          ("approved_intake", "240", 1, "Approved Intake: 240")]),
        ("14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf", "scrutiny_report",
         "Previous scrutiny observations available.",
         [("eoa_reference", "DEMO/EOA/2025-26/0143", 1,
           "EoA Reference: DEMO/EOA/2025-26/0143")]),
        ("15_Compliance_Response_2025-26.pdf", "compliance_response",
         "Prior compliance response recorded.",
         [("response_reference", "AIT/COMP/2025-26/07", 1,
           "Response Reference: AIT/COMP/2025-26/07")]),
    ]
    for filename, doc_class, detail, fields in specs:
        checksum = hashlib.sha256(filename.encode()).hexdigest()
        doc = Document(
            institution_id=inst.id, application_id=application.id, filename=filename,
            mime_type="application/pdf", size_bytes=0, checksum=checksum,
            doc_class=doc_class, status="succeeded", status_detail=detail,
            uploaded_by=actor.id if actor else None,
        )
        db.add(doc)
        db.flush()
        db.add(DocumentVersion(document_id=doc.id, version_no=1, checksum=checksum,
                               storage_path="demo/" + checksum + ".pdf"))
        db.add(DocumentProcessingRun(document_id=doc.id, status="SUCCEEDED"))
        for name, value, page, span in fields:
            ef = ExtractedField(document_id=doc.id, field_name=name, value=value,
                                confidence=0.97, page=page, text_span=span,
                                extraction_method="demo")
            db.add(ef)
            db.flush()
            db.add(EvidenceReference(document_id=doc.id, page=page, text_span=span,
                                     extracted_field_id=ef.id, checksum=checksum))


# Sample rule set (SAMPLE — illustrative APH 2025-26; real corpus is an open decision).
# check_kind maps to evaluators in modules/validation.py.
SEED_RULES: list[dict] = [
    {
        "rule_id": "APH-4.1", "title": "Institution name required", "source_section": "4.1",
        "check_kind": "required_field", "field_keys": ["institution_name"],
        "severity": "high", "explanation": "Institution full legal name is mandatory.",
        "remediation": "Provide the institution name.",
    },
    {
        "rule_id": "APH-4.2", "title": "Registered address required", "source_section": "4.2",
        "check_kind": "required_field", "field_keys": ["registered_address"],
        "severity": "high", "explanation": "Registered parcel address is mandatory.",
        "remediation": "Provide the registered address (extractable from the Land Registry Deed).",
    },
    {
        "rule_id": "APH-4.3", "title": "Contact email format", "source_section": "4.3",
        "check_kind": "format_email", "field_keys": ["contact_email"],
        "severity": "medium", "explanation": "Contact email, when provided, must be a valid address.",
        "remediation": "Correct the contact email format.",
    },
    {
        "rule_id": "APH-7.2.1", "title": "Faculty cadre ratio (1:20)", "source_section": "7.2.1",
        "check_kind": "ratio_min", "field_keys": ["total_faculty", "sanctioned_intake", "required_faculty"],
        "params": {"numerator": "total_faculty", "denominator": "sanctioned_intake", "ratio": 20},
        "severity": "high",
        "explanation": "Faculty count must satisfy the 1:20 student-faculty ratio against sanctioned intake.",
        "remediation": "Recruit or reclassify eligible faculty to close the cadre shortfall.",
    },
    {
        "rule_id": "APH-7.2.2", "title": "Ph.D faculty sufficiency", "source_section": "7.2.2",
        "check_kind": "min_value", "field_keys": ["faculty_phd_count"],
        "params": {"field": "faculty_phd_count", "minimum": 40},
        "severity": "medium",
        "explanation": "A minimum number of Ph.D-qualified faculty is expected.",
        "remediation": "Increase Ph.D-qualified faculty count.",
    },
    {
        "rule_id": "APH-8.1", "title": "Land area norm (urban 2.50 acre)", "source_section": "8.1",
        "check_kind": "min_value", "field_keys": ["land_area_acres"],
        "params": {"field": "land_area_acres", "minimum": 2.50},
        "severity": "high",
        "explanation": "Urban institutions require at least 2.50 acres of contiguous land.",
        "remediation": "Provide land records proving the required area.",
    },
    {
        "rule_id": "APH-8.2", "title": "Built-up area norm", "source_section": "8.2",
        "check_kind": "min_value", "field_keys": ["built_up_sqm"],
        "params": {"field": "built_up_sqm", "minimum": 10000},
        "severity": "medium",
        "explanation": "Total built-up area must meet the minimum norm.",
        "remediation": "Provide built-up area records.",
    },
    {
        "rule_id": "APH-9.1", "title": "Fire NOC not expiring", "source_section": "9.1",
        "check_kind": "expiry_within", "field_keys": ["fire_noc_expiry"],
        "params": {"field": "fire_noc_expiry", "min_days": 30},
        "severity": "high",
        "explanation": "Fire Safety NOC must be valid (not expiring within 30 days).",
        "remediation": "Renew the Fire Safety NOC.",
    },
    {
        "rule_id": "APH-9.2", "title": "Occupancy certificate required", "source_section": "9.2",
        "check_kind": "required_field", "field_keys": ["occupancy_certificate"],
        "severity": "high", "explanation": "Occupancy certificate is mandatory.",
        "remediation": "Upload the occupancy certificate.",
    },
    {
        "rule_id": "APH-10.1", "title": "Building stability required", "source_section": "10.1",
        "check_kind": "required_field", "field_keys": ["building_stability"],
        "severity": "medium", "explanation": "Building stability certificate is mandatory.",
        "remediation": "Upload the building stability certificate.",
    },
    {
        "rule_id": "APH-13.1", "title": "Faculty count matches evidence", "source_section": "13.1",
        "check_kind": "cross_doc_match", "field_keys": ["total_faculty"],
        "params": {"field": "total_faculty", "extracted_field": "total_faculty",
                   "doc_class": "faculty_statement"},
        "severity": "high",
        "explanation": "The faculty count in the application must match the count extracted from the faculty statement.",
        "remediation": "Reconcile the faculty count with the uploaded faculty statement.",
        "categories": ["eoa_self_disclosure"],
    },
    {
        "rule_id": "DEMO-FAC-001", "title": "Faculty declaration matches faculty list",
        "source_section": "DEMO", "check_kind": "cross_doc_match",
        "field_keys": ["total_faculty"],
        "params": {"field": "total_faculty", "extracted_field": "total_faculty",
                   "doc_class": "faculty_statement"},
        "severity": "high",
        "explanation": "The faculty count declared in the application should match the uploaded faculty list.",
        "remediation": "Reconcile the declared faculty count with the faculty list.",
        "categories": ["increase_intake"], "official": False,
    },
    {
        "rule_id": "DEMO-FAC-002", "title": "Faculty list matches institutional record",
        "source_section": "DEMO", "check_kind": "reference_match",
        "field_keys": ["total_faculty"],
        "params": {"field": "total_faculty", "source": "extracted",
                   "doc_class": "faculty_statement", "extracted_field": "total_faculty",
                   "reference_key": "faculty_on_record"},
        "severity": "high",
        "explanation": "The uploaded faculty list should align with the institutional record.",
        "remediation": "Clarify the faculty count and provide supporting appointments.",
        "categories": ["increase_intake"], "official": False,
    },
    {
        "rule_id": "DEMO-NOC-001", "title": "Fire NOC matches declared expiry",
        "source_section": "DEMO", "check_kind": "cross_doc_match",
        "field_keys": ["fire_noc_expiry"],
        "params": {"field": "fire_noc_expiry", "extracted_field": "fire_noc_expiry",
                   "doc_class": "fire_noc"},
        "severity": "high",
        "explanation": "The fire NOC expiry declared in the application should match the uploaded NOC.",
        "remediation": "Upload a valid, current fire NOC.",
        "categories": ["increase_intake"], "official": False,
    },
    {
        "rule_id": "DEMO-DOC-001", "title": "Duplicate or reused evidence",
        "source_section": "DEMO", "check_kind": "duplicate_document",
        "field_keys": [], "params": {},
        "severity": "medium",
        "explanation": "Identical documents may indicate reused evidence and require human review.",
        "remediation": "Replace or clarify the duplicated evidence.",
        "categories": ["increase_intake"], "official": False,
    },
    {
        "rule_id": "APH-8.3", "title": "Land area matches evidence", "source_section": "8.3",
        "check_kind": "cross_doc_match", "field_keys": ["land_area_acres"],
        "params": {"field": "land_area_acres", "extracted_field": "land_area_acres",
                   "doc_class": "land_deed", "tolerance": 0.1},
        "severity": "high",
        "explanation": "The land area in the application must match the area extracted from the land deed.",
        "remediation": "Reconcile the land area with the uploaded land deed.",
    },
]


def seed_documents(db: Session, application: Application) -> None:
    """Illustrative indexed documents so the Evidence Hub is populated on first run."""
    import hashlib

    inst = application.institution_id
    admin = db.scalar(select(User).where(User.email == "admin@northstar.edu.in"))
    actor = admin.id if admin else None

    demo_docs = [
        {
            "filename": "Land_Registry_Deed_Plot_K142.pdf", "doc_class": "land_deed",
            "status": "succeeded", "detail": "Land deed verified - 5.20 acres, Plot K-142/2.",
            "size": 842112,
            "fields": [
                ("land_area_acres", "5.20", 1,
                 "Total contiguous land parcel admeasuring 5.20 Acres at Knowledge Park III, Plot K-142/2."),
                ("plot_no", "K-142/2", 1, "Plot/Khasra No. K-142/2, Knowledge Park III."),
                ("registered_address",
                 "Plot K-142/2, Knowledge Park III, Greater Noida, Delhi NCR - 201310", 1,
                 "Registered parcel address: Plot K-142/2, Knowledge Park III, Greater Noida, Delhi NCR - 201310."),
            ],
        },
        {
            "filename": "Faculty_Cadre_Statement_2026.pdf", "doc_class": "faculty_statement",
            "status": "succeeded", "detail": "Faculty statement verified - 48 on rolls, 42 with Ph.D.",
            "size": 623400,
            "fields": [
                ("total_faculty", "48", 2, "Total verified faculty on rolls: 48 across all departments."),
                ("sanctioned_intake", "1020", 2, "Sanctioned intake for AY 2026-27: 1020 seats."),
                ("faculty_phd_count", "42", 3, "Faculty holding a Ph.D / doctorate: 42."),
            ],
        },
        {
            "filename": "Fire_Safety_NOC_FS-2025-8891.pdf", "doc_class": "fire_noc",
            "status": "succeeded", "detail": "Fire NOC parsed - valid till 15 May 2026.",
            "size": 410240,
            "fields": [
                ("fire_noc_expiry", "2026-05-15", 1,
                 "This No Objection Certificate is valid till 15 May 2026."),
                ("noc_number", "FS-2025-8891", 1, "NOC No. FS-2025-8891 issued by Delhi Fire Service."),
            ],
        },
        {
            "filename": "Audited_Financial_Accounts_FY2024-25.pdf", "doc_class": "audited_accounts",
            "status": "succeeded", "detail": "Audited accounts indexed for FY 2024-25.",
            "size": 1204880,
            "fields": [
                ("financial_year", "2024-25", 1, "Audited financial statements for FY 2024-25."),
            ],
        },
        {
            "filename": "Building_Stability_Certificate_2025.pdf", "doc_class": "building_stability",
            "status": "succeeded", "detail": "Structural stability certificate verified.",
            "size": 388920,
            "fields": [],
        },
        {
            "filename": "Affiliation_Letter_Scan.pdf", "doc_class": "unclassified",
            "status": "needs_review",
            "detail": "Document type could not be classified; manual review required.",
            "size": 2048512,
            "fields": [],
        },
    ]

    for spec in demo_docs:
        checksum = hashlib.sha256(spec["filename"].encode()).hexdigest()
        doc = Document(
            institution_id=inst, application_id=application.id,
            filename=spec["filename"], mime_type="application/pdf",
            size_bytes=spec["size"], checksum=checksum, doc_class=spec["doc_class"],
            status=spec["status"], status_detail=spec["detail"], uploaded_by=actor,
        )
        db.add(doc)
        db.flush()
        db.add(DocumentVersion(document_id=doc.id, version_no=1, checksum=checksum,
                               storage_path="demo/" + checksum + ".pdf"))
        db.add(DocumentProcessingRun(
            document_id=doc.id,
            status="SUCCEEDED" if spec["status"] == "succeeded" else "NEEDS_REVIEW",
        ))
        for name, value, page, span in spec["fields"]:
            ef = ExtractedField(document_id=doc.id, field_name=name, value=value,
                                confidence=0.96, page=page, text_span=span,
                                extraction_method="demo")
            db.add(ef)
            db.flush()
            db.add(EvidenceReference(document_id=doc.id, page=page, text_span=span,
                                     extracted_field_id=ef.id, checksum=checksum))


def seed_regulations(db: Session) -> None:
    source = RegulatorySource(
        title="AICTE Approval Process Handbook 2025-26", authority="AICTE",
        version="2025-26", note="SAMPLE — illustrative rule set for the prototype; "
        "not the authoritative corpus (open decision, systemdesign §19).",
    )
    db.add(source)
    db.flush()
    for r in SEED_RULES:
        db.add(RegulatoryRule(
            rule_id=r["rule_id"], title=r["title"], source_id=source.id,
            source_section=r["source_section"], version="1.0",
            check_kind=r["check_kind"], field_keys=r["field_keys"],
            params=r.get("params", {}), severity=r["severity"],
            explanation=r["explanation"], remediation=r["remediation"],
            applicability={}, active=True,
            academic_year="2026-27",
            application_categories=r.get("categories", []),
            official=r.get("official", r["rule_id"].startswith("APH")),
            needs_confirmation=r.get("needs_confirmation", False),
            source_document=("AICTE Approval Process Handbook 2025-26 (sample)"
                             if r["rule_id"].startswith("APH")
                             else "Prototype demonstration rule"),
        ))

import uuid as uuidlib
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db
from ..core.security import (
    AuthContext,
    get_auth,
    require_membership,
    require_permission,
)
from ..models import (
    Application,
    ApplicationField,
    ApplicationFieldValue,
    ApplicationSection,
    AuditEvent,
    Document,
    ExtractedField,
    Institution,
    InstitutionMembership,
)
from ..seed import sections_for
from ..workflows import STAGES, get_workflow

router = APIRouter(prefix="/api/v1", tags=["applications"])


# --- helpers (also used by copilot tools) ---

def load_application(db: Session, application_id: uuidlib.UUID | str) -> Application:
    application = db.get(Application, uuidlib.UUID(str(application_id)))
    if application is None:
        raise HTTPException(404, "Application not found")
    return application


def current_value(db: Session, field: ApplicationField) -> ApplicationFieldValue | None:
    rows = db.scalars(
        select(ApplicationFieldValue).where(ApplicationFieldValue.field_id == field.id)
        .order_by(ApplicationFieldValue.created_at.desc(), ApplicationFieldValue.version.desc())
    ).all()
    return rows[0] if rows else None


def field_map(db: Session, application: Application) -> dict[str, ApplicationField]:
    out = {}
    for section in application.sections:
        for f in section.fields:
            out[f.key] = f
    return out


def application_summary(db: Session, application: Application) -> dict:
    sections = []
    required_total = required_filled = 0
    for section in application.sections:
        sec_fields, sec_req, sec_filled = [], 0, 0
        for f in section.fields:
            val = current_value(db, f)
            filled = bool(val and val.value.strip())
            if f.required:
                required_total += 1
                sec_req += 1
                if filled:
                    required_filled += 1
                    sec_filled += 1
            sec_fields.append({
                "field_id": str(f.id), "key": f.key, "label": f.label,
                "type": f.type, "required": f.required, "locked": f.locked,
                "value": val.value if val else "",
                "version": val.version if val else 0,
                "source_document_id": str(val.source_document_id) if val and val.source_document_id else None,
            })
        sections.append({
            "section_id": str(section.id), "key": section.key, "title": section.title,
            "completion": round(100 * sec_filled / sec_req) if sec_req else 100,
            "fields": sec_fields,
        })
    completion = round(100 * required_filled / required_total) if required_total else 100
    return {
        "application_id": str(application.id),
        "institution_id": str(application.institution_id),
        "reference_no": application.reference_no,
        "application_type": application.application_type,
        "academic_year": application.academic_year,
        "category": application.category,
        "category_title": get_workflow(application.category).title,
        "workflow_stage": application.workflow_stage,
        "stages": [{"key": s, "title": STAGES.get(s, s)}
                   for s in get_workflow(application.category).stages],
        "status": application.status,
        "completion_pct": completion,
        "required_fields": {"total": required_total, "filled": required_filled},
        "sections": sections,
    }


def set_field_value(db: Session, *, field: ApplicationField, value: str,
                    actor_id=None, source_document_id=None,
                    source_extracted_field_id=None, expected_version: int | None = None) -> ApplicationFieldValue:
    if field.locked:
        raise HTTPException(409, f"Field '{field.key}' is locked")
    prev = current_value(db, field)
    if expected_version is not None:
        current_version = prev.version if prev else 0
        if current_version != expected_version:
            raise HTTPException(409, "Stale version — refresh and retry")
    if field.type == "number":
        try:
            float(value)
        except ValueError:
            raise HTTPException(422, f"Field '{field.key}' expects a number")
    if field.type == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            raise HTTPException(422, f"Field '{field.key}' expects ISO date (YYYY-MM-DD)")
    row = ApplicationFieldValue(
        field_id=field.id, value=value,
        version=(prev.version + 1) if prev else 1,
        updated_by=actor_id,
        source_document_id=source_document_id,
        source_extracted_field_id=source_extracted_field_id,
    )
    db.add(row)
    audit(db, action="application.field.update", actor_id=actor_id,
          application_id=field.section.application_id if field.section else None,
          target=field.key, before={"value": prev.value if prev else ""},
          after={"value": value, "version": row.version})
    return row


# --- institutions ---

class InstitutionIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=64)


@router.get("/institutions")
def list_institutions(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    out = []
    for inst_id, membership in auth.memberships.items():
        inst = db.get(Institution, inst_id)
        out.append({"institution_id": str(inst.id), "name": inst.name,
                    "code": inst.code, "role": membership.role})
    return {"data": out}


@router.post("/institutions", status_code=201)
def create_institution(body: InstitutionIn, auth: AuthContext = Depends(get_auth),
                       db: Session = Depends(get_db)):
    inst = Institution(name=body.name, code=body.code)
    db.add(inst)
    db.flush()
    db.add(InstitutionMembership(user_id=auth.user.id, institution_id=inst.id, role="admin"))
    audit(db, action="institution.create", actor_id=auth.user.id, institution_id=inst.id,
          target=body.code)
    db.commit()
    return {"data": {"institution_id": str(inst.id), "name": inst.name, "code": inst.code}}


# --- applications ---

class ApplicationIn(BaseModel):
    institution_id: str
    application_type: str = Field(max_length=128)
    academic_year: str = Field(max_length=32)
    category: str = "eoa_self_disclosure"


@router.get("/applications")
def list_applications(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    out = []
    for inst_id in auth.memberships:
        rows = db.scalars(select(Application).where(Application.institution_id == inst_id)).all()
        for a in rows:
            out.append({
                "application_id": str(a.id), "reference_no": a.reference_no,
                "application_type": a.application_type, "academic_year": a.academic_year,
                "status": a.status, "institution_id": str(a.institution_id),
            })
    return {"data": out}


@router.post("/applications", status_code=201)
def create_application(body: ApplicationIn, auth: AuthContext = Depends(get_auth),
                       db: Session = Depends(get_db)):
    inst_id = uuidlib.UUID(body.institution_id)
    require_membership(auth, inst_id)
    try:
        get_workflow(body.category)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    application = Application(
        institution_id=inst_id,
        reference_no=f"{db.get(Institution, inst_id).code}-{body.academic_year}-{uuidlib.uuid4().hex[:6].upper()}",
        application_type=body.application_type, academic_year=body.academic_year,
        category=body.category, workflow_stage="initial_validation", status="draft",
    )
    db.add(application)
    db.flush()
    for i, spec in enumerate(sections_for(body.category)):
        section = ApplicationSection(application_id=application.id, key=spec["key"],
                                     title=spec["title"], order=i + 1)
        db.add(section)
        db.flush()
        for j, (key, label, type_, required, locked) in enumerate(spec["fields"]):
            db.add(ApplicationField(section_id=section.id, key=key, label=label,
                                    type=type_, required=required, locked=locked,
                                    order=j + 1))
    audit(db, action="application.create", actor_id=auth.user.id,
          institution_id=inst_id, application_id=application.id,
          target=application.reference_no)
    db.commit()
    return {"data": application_summary(db, application)}


@router.get("/applications/{application_id}")
def get_application(application_id: str, auth: AuthContext = Depends(get_auth),
                    db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_membership(auth, application.institution_id)
    return {"data": application_summary(db, application)}


class FieldPatch(BaseModel):
    value: str = Field(max_length=2000)
    version: int | None = None


@router.patch("/applications/{application_id}/fields/{field_id}")
def patch_field(application_id: str, field_id: str, body: FieldPatch,
                auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "application.draft.update")
    field = db.get(ApplicationField, uuidlib.UUID(field_id))
    if field is None or field.key not in field_map(db, application):
        raise HTTPException(404, "Field not found in this application")
    set_field_value(db, field=field, value=body.value, actor_id=auth.user.id,
                    expected_version=body.version)
    db.commit()
    return {"data": application_summary(db, application)}


@router.get("/applications/{application_id}/audit")
def application_audit(application_id: str, auth: AuthContext = Depends(get_auth),
                      db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_membership(auth, application.institution_id)
    rows = db.scalars(
        select(AuditEvent).where(AuditEvent.application_id == application.id)
        .order_by(AuditEvent.created_at.desc()).limit(50)
    ).all()
    return {"data": [{
        "action": e.action, "target": e.target, "before": e.before, "after": e.after,
        "actor_id": str(e.actor_id) if e.actor_id else None,
        "at": str(e.created_at),
    } for e in rows]}


CHECKLIST_DOC_CLASS: dict[str, set[str]] = {
    "previous_eoa": {"previous_eoa"},
    "application_form": {"application_form"},
    "faculty_list": {"faculty_statement", "faculty_list"},
    "faculty_declaration": {"faculty_declaration", "faculty_statement"},
    "land_document": {"land_deed"},
    "lease_deed": {"land_deed"},
    "building_occupancy": {"occupancy_certificate"},
    "fire_safety": {"fire_noc"},
    "building_plan": {"floor_plan"},
    "laboratory_evidence": {"infrastructure_photo"},
    "library_evidence": {"infrastructure_photo"},
    "laboratory_equipment": {"infrastructure_photo", "equipment_list"},
    "payment_receipt": {"payment_receipt"},
    "affidavit": {"affidavit"},
    "compliance_declaration": {"compliance_declaration"},
    "self_disclosure_declaration": {"compliance_declaration"},
    "trust_registration": {"trust_registration"},
    "programme_details": {"application_form"},
    "infrastructure_evidence": {"infrastructure_photo", "floor_plan"},
    "affiliation_letter": {"affiliation_letter"},
    "state_noc": {"state_noc"},
    "site_photographs": {"infrastructure_photo"},
    "closure_application": {"closure_application"},
    "student_redistribution_plan": {"closure_application"},
    "university_noc": {"university_noc"},
    "approvals_both_entities": {"previous_eoa"},
    "amalgamation_resolution": {"trust_registration"},
    "registration_proof": {"trust_registration"},
    "updated_certificates": {"occupancy_certificate"},
    "trust_resolution": {"trust_registration"},
    "break_records": {"previous_eoa"},
    "compliance_response": {"compliance_response"},
    "faculty_student_records": {"faculty_statement"},
}


def build_checklist(db: Session, application: Application) -> dict:
    workflow = get_workflow(application.category)
    docs = db.scalars(select(Document).where(
        Document.application_id == application.id)).all()
    by_class: dict[str, list[Document]] = {}
    for d in docs:
        by_class.setdefault(d.doc_class, []).append(d)

    items = []
    for key in workflow.documents:
        classes = CHECKLIST_DOC_CLASS.get(key, {key})
        matches = [d for c in classes for d in by_class.get(c, [])]
        matches.sort(key=lambda d: d.created_at or "", reverse=True)
        doc = matches[0] if matches else None
        if doc is None:
            state = "missing"
        elif doc.status in ("processing", "uploaded"):
            state = "processing"
        elif doc.status == "needs_review":
            state = "unverified"
        elif key == "fire_safety":
            ef = db.scalar(select(ExtractedField).where(
                ExtractedField.document_id == doc.id,
                ExtractedField.field_name == "fire_noc_expiry").limit(1))
            state = "expired" if (ef and ef.value and ef.value < str(date.today())) else "uploaded"
        else:
            state = "uploaded"
        items.append({
            "key": key, "state": state,
            "document_id": str(doc.id) if doc else None,
            "filename": doc.filename if doc else None,
            "status_detail": doc.status_detail if doc else None,
        })
    return {
        "application_id": str(application.id),
        "category": application.category,
        "category_title": workflow.title,
        "items": items,
        "missing": sum(1 for i in items if i["state"] == "missing"),
    }


@router.get("/applications/{application_id}/checklist")
def application_checklist(application_id: str, auth: AuthContext = Depends(get_auth),
                          db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_membership(auth, application.institution_id)
    return {"data": build_checklist(db, application)}

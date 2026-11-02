from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db, utcnow
from ..core.security import AuthContext, get_auth, require_membership, require_permission
from ..models import Application, Document, EvcRecord, ExtractedField
from ..workflows import get_workflow
from .applications import current_value, field_map, load_application

router = APIRouter(prefix="/api/v1", tags=["evc"])

DISCLAIMER = ("Automated image analysis is preliminary and cannot replace a physical "
              "inspection or an authorised committee decision.")


def _field_value(db: Session, application: Application, key: str) -> str:
    field = field_map(db, application).get(key)
    value = current_value(db, field) if field else None
    return (value.value if value else "").strip()


def _latest_extracted(db: Session, application: Application, doc_class: str,
                      field_name: str) -> str:
    row = db.execute(
        select(ExtractedField)
        .join(Document, Document.id == ExtractedField.document_id)
        .where(Document.institution_id == application.institution_id,
               Document.doc_class == doc_class,
               ExtractedField.field_name == field_name)
        .order_by(ExtractedField.created_at.desc()).limit(1)
    ).scalars().first()
    return row.value if row else ""


def build_infrastructure_analysis(db: Session, application: Application) -> dict:
    docs = db.scalars(select(Document).where(
        Document.application_id == application.id)).all()
    evidence_docs = [d for d in docs
                     if d.doc_class in ("infrastructure_photo", "floor_plan")]
    groups: dict[str, list[Document]] = {}
    for d in evidence_docs:
        groups.setdefault(d.checksum, []).append(d)
    duplicates = [
        {"checksum": checksum,
         "documents": [{"document_id": str(x.id), "filename": x.filename} for x in group]}
        for checksum, group in groups.items() if len(group) > 1
    ]

    photos = [d for d in evidence_docs if d.doc_class == "infrastructure_photo"]
    floor_plans = [d for d in evidence_docs if d.doc_class == "floor_plan"]
    missing = []
    if not photos:
        missing.extend(["laboratory_evidence", "library_evidence"])
    elif len(photos) < 2:
        missing.append("library_evidence")
    if not floor_plans:
        missing.append("building_plan")

    declared_built = _field_value(db, application, "built_up_sqm")
    evidence_built = _latest_extracted(db, application, "floor_plan", "built_up_sqm")

    observations = []
    if duplicates:
        names = "; ".join(", ".join(x["filename"] for x in g["documents"]) for g in duplicates)
        observations.append(
            f"Potential duplicate/reused infrastructure evidence: {names}. "
            "Human review required; this is not proof of manipulation.")
    if missing:
        observations.append("Missing infrastructure evidence: " + ", ".join(missing) + ".")
    if declared_built and evidence_built and declared_built != evidence_built:
        observations.append(
            f"Declared built-up area {declared_built} sqm differs from the floor plan "
            f"value {evidence_built} sqm.")
    if not observations:
        observations.append("Evidence inventory is present; a physical inspection may still be required.")

    return {
        "application_id": str(application.id),
        "category": application.category,
        "category_title": get_workflow(application.category).title,
        "evidence": [{"document_id": str(d.id), "filename": d.filename,
                      "doc_class": d.doc_class, "status": d.status} for d in evidence_docs],
        "duplicate_groups": duplicates,
        "missing_evidence": missing,
        "declared": {"built_up_sqm": declared_built},
        "evidence_values": {"built_up_sqm": evidence_built},
        "observations": observations,
        "evc_recommended": bool(duplicates or missing or
                                (declared_built and evidence_built and declared_built != evidence_built)),
        "disclaimer": DISCLAIMER,
        "simulated": True,
    }


def _evc_json(record: EvcRecord | None) -> dict | None:
    if record is None:
        return None
    return {
        "evc_id": str(record.id),
        "status": record.status,
        "reason": record.reason,
        "visit_mode": record.visit_mode,
        "checklist": record.checklist or [],
        "notes": record.notes or [],
        "updated_at": str(record.updated_at),
        "simulated": True,
    }


def _get_or_create(db: Session, application: Application, actor_id) -> EvcRecord:
    record = db.scalar(select(EvcRecord).where(
        EvcRecord.application_id == application.id).limit(1))
    if record is None:
        record = EvcRecord(application_id=application.id, created_by=actor_id,
                           checklist=[], notes=[])
        db.add(record)
        db.flush()
    return record


@router.post("/applications/{application_id}/infrastructure/analyze")
def analyze_infrastructure(application_id: str, auth: AuthContext = Depends(get_auth),
                           db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "application.read")
    return {"data": build_infrastructure_analysis(db, application)}


class EvcRecommendIn(BaseModel):
    reason: str = ""
    visit_mode: str = "online"


@router.post("/applications/{application_id}/evc/recommend")
def recommend_evc(application_id: str, body: EvcRecommendIn,
                  auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "evc.manage")
    analysis = build_infrastructure_analysis(db, application)
    record = _get_or_create(db, application, auth.user.id)
    record.status = "recommended"
    record.reason = body.reason or "EVC recommended after infrastructure evidence review."
    record.visit_mode = body.visit_mode if body.visit_mode in ("online", "offline") else "online"
    record.checklist = [
        {"item": o, "status": "open"} for o in analysis["observations"]
    ] + [{"item": m, "status": "missing"} for m in analysis["missing_evidence"]]
    application.workflow_stage = "evc_recommended"
    audit(db, action="evc.recommended", actor_id=auth.user.id,
          application_id=application.id, target="evc",
          after={"visit_mode": record.visit_mode})
    db.commit()
    return {"data": _evc_json(record)}


class EvcNoteIn(BaseModel):
    note: str


@router.post("/applications/{application_id}/evc/notes")
def add_evc_note(application_id: str, body: EvcNoteIn,
                 auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "evc.manage")
    if not body.note.strip():
        raise HTTPException(422, "Note cannot be empty")
    record = _get_or_create(db, application, auth.user.id)
    notes = list(record.notes or [])
    notes.append({"author": auth.user.name, "note": body.note.strip(),
                  "at": utcnow().isoformat(timespec="seconds")})
    record.notes = notes
    record.status = "notes_recorded"
    application.workflow_stage = "evc_notes_recorded"
    audit(db, action="evc.note.added", actor_id=auth.user.id,
          application_id=application.id, target="evc")
    db.commit()
    return {"data": _evc_json(record)}


@router.get("/applications/{application_id}/evc")
def get_evc(application_id: str, auth: AuthContext = Depends(get_auth),
            db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_membership(auth, application.institution_id)
    record = db.scalar(select(EvcRecord).where(
        EvcRecord.application_id == application.id).limit(1))
    return {"data": {"evc": _evc_json(record),
                     "workflow_stage": application.workflow_stage}}

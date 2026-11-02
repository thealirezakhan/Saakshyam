import uuid as uuidlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db
from ..core.security import AuthContext, get_auth, require_membership, require_permission
from ..models import (
    Document,
    EvidenceReference,
    EvcRecord,
    ExtractedField,
    ReviewAction,
    ValidationFinding,
    ValidationRun,
    VerificationRecord,
)
from .applications import application_summary, load_application
from .validation import _finding_json, latest_findings

router = APIRouter(prefix="/api/v1", tags=["reporting"])


def build_compliance_report(db: Session, application) -> dict:
    findings = latest_findings(db, application.id)
    statuses = {"PASS": 0, "FAIL": 0, "NEEDS_REVIEW": 0, "NOT_APPLICABLE": 0, "NOT_EVALUATED": 0}
    for f in findings:
        statuses[f.status] = statuses.get(f.status, 0) + 1
    doc_ids = [d.id for d in db.scalars(select(Document).where(
        Document.application_id == application.id)).all()]
    verifications = []
    if doc_ids:
        verifications = db.scalars(select(VerificationRecord).where(
            VerificationRecord.document_id.in_(doc_ids))
            .order_by(VerificationRecord.created_at.desc())).all()
    review_actions = db.scalars(select(ReviewAction).where(
        ReviewAction.application_id == application.id)
        .order_by(ReviewAction.created_at)).all()
    evc = db.scalar(select(EvcRecord).where(
        EvcRecord.application_id == application.id).limit(1))
    return {
        "application": {
            "reference_no": application.reference_no,
            "application_type": application.application_type,
            "academic_year": application.academic_year,
            "category": application.category,
            "workflow_stage": application.workflow_stage,
        },
        "completion_pct": application_summary(db, application)["completion_pct"],
        "statuses": statuses,
        "unresolved": [_finding_json(db, f, include_evidence=True) for f in findings
                       if f.status in ("FAIL", "NEEDS_REVIEW")],
        "findings": [_finding_json(db, f, include_evidence=True) for f in findings],
        "verifications": [{
            "request_id": v.request_id, "result": v.result, "source": v.source,
            "reference_number": v.reference_number,
            "submitted_value": v.submitted_value, "returned_value": v.returned_value,
            "manual_review_required": v.manual_review_required, "at": v.verified_at,
        } for v in verifications],
        "review_actions": [{
            "action": a.action, "note": a.note, "at": str(a.created_at),
            "finding_id": str(a.finding_id) if a.finding_id else None,
        } for a in review_actions],
        "evc": ({
            "status": evc.status, "reason": evc.reason, "visit_mode": evc.visit_mode,
            "checklist": evc.checklist or [], "notes": evc.notes or [],
        } if evc else None),
        "simulated_sources": True,
    }


@router.get("/applications/{application_id}/report")
def compliance_report(application_id: str, auth: AuthContext = Depends(get_auth),
                      db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "application.read")
    report = build_compliance_report(db, application)
    report["generated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    audit(db, action="report.view", actor_id=auth.user.id,
          application_id=application.id, target="compliance_report")
    db.commit()
    return {"data": report}


@router.get("/applications/{application_id}/report/export")
def export_report(application_id: str, auth: AuthContext = Depends(get_auth),
                  db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "report.export")
    report = build_compliance_report(db, application)
    report["generated_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    audit(db, action="report.export", actor_id=auth.user.id,
          application_id=application.id, target="compliance_report")
    db.commit()
    return {"data": report}

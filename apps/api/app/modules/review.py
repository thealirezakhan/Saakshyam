from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db
from ..core.security import AuthContext, get_auth, require_membership, require_permission
from ..models import Application, EvcRecord, ReviewAction, ValidationFinding, ValidationRun
from .applications import load_application

router = APIRouter(prefix="/api/v1", tags=["review"])


class NoteIn(BaseModel):
    note: str = ""


def _finding_context(db: Session, finding_id: str, auth: AuthContext):
    from .validation import _load_finding_context
    return _load_finding_context(db, finding_id, auth)


def _record(db: Session, application: Application, auth: AuthContext,
            action: str, note: str, finding_id=None) -> ReviewAction:
    row = ReviewAction(application_id=application.id, finding_id=finding_id,
                       reviewer_id=auth.user.id, action=action, note=note)
    db.add(row)
    db.flush()
    audit(db, action=f"review.{action}", actor_id=auth.user.id,
          application_id=application.id, target=str(finding_id or application.reference_no))
    return row


@router.get("/review/queue")
def review_queue(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    from .validation import latest_findings
    out = []
    for institution_id in auth.memberships:
        for application in db.scalars(select(Application).where(
                Application.institution_id == institution_id)).all():
            findings = latest_findings(db, application.id)
            out.append({
                "application_id": str(application.id),
                "reference_no": application.reference_no,
                "category": application.category,
                "workflow_stage": application.workflow_stage,
                "status": application.status,
                "open_findings": sum(1 for f in findings
                                     if f.status in ("FAIL", "NEEDS_REVIEW")),
                "human_review": sum(1 for f in findings if f.human_review_required),
            })
    return {"data": out}


@router.post("/findings/{finding_id}/review/observe")
def add_observation(finding_id: str, body: NoteIn,
                    auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    finding, application = _finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "review.manage")
    if not body.note.strip():
        raise HTTPException(422, "Observation cannot be empty")
    _record(db, application, auth, "observation", body.note.strip(), finding.id)
    db.commit()
    return {"data": {"ok": True}}


@router.post("/findings/{finding_id}/review/request-evidence")
def request_evidence(finding_id: str, body: NoteIn,
                     auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    finding, application = _finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "review.manage")
    finding.lifecycle_status = "Awaiting Institution Response"
    _record(db, application, auth, "evidence_requested", body.note.strip(), finding.id)
    db.commit()
    return {"data": {"ok": True}}


@router.post("/findings/{finding_id}/review/mark-manual")
def mark_manual(finding_id: str, body: NoteIn,
                auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    finding, application = _finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "review.manage")
    finding.human_review_required = True
    finding.lifecycle_status = "Escalated for Human Review"
    _record(db, application, auth, "manual_verification", body.note.strip(), finding.id)
    db.commit()
    return {"data": {"ok": True}}


class RecommendIn(BaseModel):
    note: str = ""
    visit_mode: str = "online"


@router.post("/applications/{application_id}/review/recommend-evc")
def review_recommend_evc(application_id: str, body: RecommendIn,
                         auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "review.manage")
    record = db.scalar(select(EvcRecord).where(
        EvcRecord.application_id == application.id).limit(1))
    if record is None:
        record = EvcRecord(application_id=application.id, created_by=auth.user.id,
                           checklist=[], notes=[])
        db.add(record)
        db.flush()
    record.status = "recommended"
    record.reason = body.note or "Reviewer recommended EVC."
    record.visit_mode = body.visit_mode if body.visit_mode in ("online", "offline") else "online"
    application.workflow_stage = "evc_recommended"
    _record(db, application, auth, "evc_recommended", record.reason)
    db.commit()
    return {"data": {"ok": True, "workflow_stage": application.workflow_stage}}


@router.get("/applications/{application_id}/review")
def application_review(application_id: str, auth: AuthContext = Depends(get_auth),
                       db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_membership(auth, application.institution_id)
    actions = db.scalars(select(ReviewAction).where(
        ReviewAction.application_id == application.id)
        .order_by(ReviewAction.created_at)).all()
    latest_run = db.scalar(select(ValidationRun).where(
        ValidationRun.application_id == application.id)
        .order_by(ValidationRun.created_at.desc()).limit(1))
    findings = []
    if latest_run:
        findings = db.scalars(select(ValidationFinding).where(
            ValidationFinding.run_id == latest_run.id)).all()
    return {"data": {
        "application_id": str(application.id),
        "reference_no": application.reference_no,
        "workflow_stage": application.workflow_stage,
        "actions": [{"action": a.action, "note": a.note, "at": str(a.created_at),
                     "reviewer_id": str(a.reviewer_id) if a.reviewer_id else None,
                     "finding_id": str(a.finding_id) if a.finding_id else None}
                    for a in actions],
        "findings": [{
            "finding_id": str(f.id), "rule_id": f.rule_id, "status": f.status,
            "severity": f.severity, "lifecycle_status": f.lifecycle_status,
            "human_review_required": f.human_review_required,
            "explanation": f.explanation,
        } for f in findings],
    }}

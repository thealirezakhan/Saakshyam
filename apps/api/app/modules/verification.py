import uuid as uuidlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db, utcnow
from ..core.security import AuthContext, get_auth, require_permission
from ..core.verification import MockVerificationAdapter
from ..models import Application, Document, ExtractedField, VerificationRecord
from .applications import load_application

router = APIRouter(prefix="/api/v1", tags=["verification"])

SIMULATED_BANNER = "SIMULATED VERIFICATION - NO LIVE GOVERNMENT OR ISSUING-AUTHORITY CONNECTION"


def _json(record: VerificationRecord) -> dict:
    return {
        "verification_id": str(record.id),
        "request_id": record.request_id,
        "document_id": str(record.document_id),
        "document_type": record.outcome,
        "method": record.method,
        "source": record.source,
        "reference_number": record.reference_number,
        "submitted_value": record.submitted_value,
        "returned_value": record.returned_value,
        "result": record.result,
        "timestamp": record.verified_at,
        "explanation": record.explanation,
        "manual_review_required": record.manual_review_required,
        "banner": SIMULATED_BANNER,
    }


@router.post("/documents/{document_id}/verify", status_code=201)
def verify_document(document_id: str, auth: AuthContext = Depends(get_auth),
                    db: Session = Depends(get_db)):
    document = db.get(Document, uuidlib.UUID(document_id))
    if document is None:
        raise HTTPException(404, "Document not found")
    require_permission(auth, document.institution_id, "document.read")

    fields = {f.field_name: f.value for f in db.scalars(select(ExtractedField).where(
        ExtractedField.document_id == document.id)).all()}
    result = MockVerificationAdapter().verify(document, fields)

    record = VerificationRecord(
        document_id=document.id, method="simulated", outcome=result.result,
        detail=result.explanation,
        request_id="VR-" + uuidlib.uuid4().hex[:10].upper(),
        source=result.source, reference_number=result.reference_number,
        submitted_value=result.submitted_value, returned_value=result.returned_value,
        result=result.result, explanation=result.explanation,
        manual_review_required=result.manual_review_required,
        verified_at=utcnow().isoformat(timespec="seconds"),
    )
    db.add(record)
    audit(db, action="verification.request", actor_id=auth.user.id,
          institution_id=document.institution_id, application_id=document.application_id,
          target=document.filename, after={"result": result.result, "simulated": True})
    db.commit()
    return {"data": _json(record)}


@router.get("/verifications/{verification_id}")
def get_verification(verification_id: str, auth: AuthContext = Depends(get_auth),
                     db: Session = Depends(get_db)):
    record = db.get(VerificationRecord, uuidlib.UUID(verification_id))
    if record is None:
        raise HTTPException(404, "Verification not found")
    document = db.get(Document, record.document_id)
    if document is None or document.institution_id not in auth.memberships:
        raise HTTPException(404, "Verification not found")
    return {"data": _json(record)}


@router.get("/applications/{application_id}/verifications")
def list_verifications(application_id: str, auth: AuthContext = Depends(get_auth),
                       db: Session = Depends(get_db)):
    application: Application = load_application(db, application_id)
    if application.institution_id not in auth.memberships:
        raise HTTPException(403, "No access to this application")
    doc_ids = [d.id for d in db.scalars(select(Document).where(
        Document.application_id == application.id)).all()]
    if not doc_ids:
        return {"data": []}
    records = db.scalars(select(VerificationRecord).where(
        VerificationRecord.document_id.in_(doc_ids))
        .order_by(VerificationRecord.created_at.desc())).all()
    return {"data": [_json(r) for r in records]}

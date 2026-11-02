import re
import uuid as uuidlib
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db, utcnow
from ..core.security import AuthContext, get_auth, require_membership, require_permission
from ..models import (
    Application,
    Document,
    EvidenceReference,
    ExtractedField,
    InstitutionalReferenceRecord,
    RegulatoryRule,
    ValidationFinding,
    ValidationRun,
)
from .applications import application_summary, current_value, field_map, load_application

router = APIRouter(prefix="/api/v1", tags=["validation"])

RULESET_VERSION = "1.0"


# --- deterministic evaluators (systemdesign ADR-004) ---

def _value(db, application, key):
    fm = field_map(db, application)
    field = fm.get(key)
    val = current_value(db, field) if field else None
    return (val.value if val else "").strip()


def _latest_evidence(db, doc_class: str, extracted_name: str):
    rows = db.execute(
        select(ExtractedField, Document)
        .join(Document, Document.id == ExtractedField.document_id)
        .where(Document.doc_class == doc_class, ExtractedField.field_name == extracted_name)
        .order_by(ExtractedField.created_at.desc())
        .limit(1)
    ).all()
    if not rows:
        return None, None
    ef, doc = rows[0]
    ref = db.scalar(select(EvidenceReference).where(
        EvidenceReference.extracted_field_id == ef.id).limit(1))
    return ef, ref


def evaluate(rule: RegulatoryRule, application: Application, db: Session) -> dict:
    kind = rule.check_kind
    params = rule.params or {}
    if kind == "required_field":
        key = rule.field_keys[0]
        value = _value(db, application, key)
        status = "PASS" if value else "FAIL"
        return {
            "status": status, "field_key": key, "application_value": value,
            "explanation": rule.explanation,
            "remediation": rule.remediation if status == "FAIL" else "",
        }
    if kind == "format_email":
        key = rule.field_keys[0]
        value = _value(db, application, key)
        if not value:
            return {"status": "NOT_APPLICABLE", "field_key": key, "application_value": value,
                    "explanation": "No email provided.", "remediation": ""}
        ok = bool(re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", value))
        return {"status": "PASS" if ok else "FAIL", "field_key": key,
                "application_value": value, "explanation": rule.explanation,
                "remediation": rule.remediation if not ok else ""}
    if kind == "min_value":
        key = params["field"]
        value = _value(db, application, key)
        if not value:
            return {"status": "FAIL", "field_key": key, "application_value": value,
                    "explanation": rule.explanation, "remediation": "Value missing."}
        try:
            numeric = float(value)
        except ValueError:
            return {"status": "NEEDS_REVIEW", "field_key": key, "application_value": value,
                    "explanation": "Value is not numeric.", "remediation": rule.remediation}
        ok = numeric >= params["minimum"]
        return {"status": "PASS" if ok else "FAIL", "field_key": key,
                "application_value": value, "explanation": rule.explanation,
                "remediation": rule.remediation if not ok else ""}
    if kind == "ratio_min":
        num = _value(db, application, params["numerator"])
        den = _value(db, application, params["denominator"])
        ratio = params["ratio"]
        if not num or not den:
            return {"status": "NOT_EVALUATED", "field_key": params["numerator"],
                    "application_value": f"{num}/{den}",
                    "explanation": "Faculty or intake not yet provided.",
                    "remediation": rule.remediation}
        try:
            required = -(-int(den) // ratio)  # ceil
            actual = int(float(num))
        except ValueError:
            return {"status": "NEEDS_REVIEW", "field_key": params["numerator"],
                    "application_value": f"{num}/{den}",
                    "explanation": "Non-numeric faculty/intake.", "remediation": rule.remediation}
        ok = actual >= required
        explanation = (f"Required faculty (intake/{ratio}): {required}; entered: {actual}. "
                       + rule.explanation)
        return {"status": "PASS" if ok else "FAIL", "field_key": params["numerator"],
                "application_value": f"{actual} / required {required}",
                "explanation": explanation, "remediation": rule.remediation if not ok else ""}
    if kind == "expiry_within":
        key = params["field"]
        value = _value(db, application, key)
        if not value:
            return {"status": "FAIL", "field_key": key, "application_value": value,
                    "explanation": "NOC expiry date missing.", "remediation": rule.remediation}
        try:
            expiry = date.fromisoformat(value)
        except ValueError:
            return {"status": "NEEDS_REVIEW", "field_key": key, "application_value": value,
                    "explanation": "Unparseable date.", "remediation": rule.remediation}
        deadline = date.today() + timedelta(days=params["min_days"])
        ok = expiry >= deadline
        return {"status": "PASS" if ok else "FAIL", "field_key": key,
                "application_value": value,
                "explanation": rule.explanation + f" Expiry: {value}.",
                "remediation": rule.remediation if not ok else ""}
    if kind == "cross_doc_match":
        key = params["field"]
        app_value = _value(db, application, key)
        ef, ref = _latest_evidence(db, params["doc_class"], params["extracted_field"])
        if not app_value:
            return {"status": "NOT_EVALUATED", "field_key": key, "application_value": app_value,
                    "explanation": "Application value not yet entered.", "remediation": ""}
        if ef is None:
            return {"status": "NEEDS_REVIEW", "field_key": key, "application_value": app_value,
                    "explanation": ("No uploaded evidence for this claim; manual verification required. "
                                    + rule.explanation),
                    "remediation": "Upload supporting evidence."}
        evidence_value = ef.value
        tolerance = params.get("tolerance")
        try:
            if tolerance is not None:
                match = abs(float(app_value) - float(evidence_value)) <= tolerance
            else:
                match = app_value == evidence_value
        except ValueError:
            match = app_value == evidence_value
        status = "PASS" if match else "FAIL"
        explanation = (
            f"Application value '{app_value}' vs extracted '{evidence_value}' "
            f"(document {str(ef.document_id)[:8]}…, page {ef.page}). " + rule.explanation)
        return {"status": status, "field_key": key, "application_value": app_value,
                "evidence_value": evidence_value, "evidence_ref_id": str(ref.id) if ref else None,
                "explanation": explanation,
                "remediation": rule.remediation if not match else ""}
    if kind == "reference_match":
        key = params["field"]
        if params.get("source") == "extracted":
            ef, _ = _latest_evidence(db, params["doc_class"],
                                     params.get("extracted_field", key))
            app_value = ef.value if ef else ""
        else:
            app_value = _value(db, application, key)
        ref_key = params.get("reference_key", key)
        record = db.scalar(select(InstitutionalReferenceRecord).where(
            InstitutionalReferenceRecord.institution_id == application.institution_id,
            InstitutionalReferenceRecord.key == ref_key)
            .order_by(InstitutionalReferenceRecord.created_at.desc()).limit(1))
        if not app_value:
            return {"status": "NOT_EVALUATED", "field_key": key, "application_value": "",
                    "explanation": "Application value not yet entered.", "remediation": ""}
        if record is None:
            return {"status": "NEEDS_REVIEW", "field_key": key, "application_value": app_value,
                    "explanation": "No institutional reference record available for comparison.",
                    "remediation": "Manual verification required."}
        tolerance = params.get("tolerance")
        try:
            if tolerance is not None:
                match = abs(float(app_value) - float(record.value)) <= tolerance
            else:
                match = app_value.strip() == record.value.strip()
        except ValueError:
            match = app_value.strip().lower() == record.value.strip().lower()
        status = "PASS" if match else "FAIL"
        return {
            "status": status, "field_key": key,
            "application_value": f"{app_value} (institutional record: {record.value})",
            "reference_value": record.value,
            "institutional_record": record.source_label,
            "explanation": (f"Application declares '{app_value}' but the institutional record "
                            f"shows '{record.value}' ({record.source_label}). " + rule.explanation),
            "remediation": rule.remediation if not match else "",
        }
    if kind == "duplicate_document":
        docs = db.scalars(select(Document).where(
            Document.institution_id == application.institution_id)).all()
        groups: dict[str, list[Document]] = {}
        for d in docs:
            groups.setdefault(d.checksum, []).append(d)
        duplicate_groups = [g for g in groups.values() if len(g) > 1]
        if not duplicate_groups:
            return {"status": "PASS", "field_key": "", "application_value": "0 duplicate groups",
                    "explanation": "No duplicate or reused evidence detected.", "remediation": ""}
        names = "; ".join(", ".join(d.filename for d in g) for g in duplicate_groups[:3])
        return {
            "status": "FAIL", "field_key": "",
            "application_value": f"{len(duplicate_groups)} duplicate group(s)",
            "explanation": (f"Potential duplicate/reused evidence detected: {names}. "
                            "Identical file hashes require human review; this is not proof of "
                            "manipulation."),
            "remediation": "Replace or clarify the duplicated evidence.",
        }
    return {"status": "NOT_EVALUATED", "field_key": "", "application_value": "",
            "explanation": f"Unsupported check kind: {kind}", "remediation": ""}


# --- run execution ---

def _run(db: Session, application: Application, rule_ids: list[str] | None,
         trigger: str, actor_id=None) -> ValidationRun:
    query = select(RegulatoryRule).where(RegulatoryRule.active.is_(True))
    if rule_ids:
        query = query.where(RegulatoryRule.rule_id.in_(rule_ids))
    rules = db.scalars(query).all()
    rules = [r for r in rules
             if not r.application_categories or application.category in r.application_categories]
    run = ValidationRun(
        application_id=application.id, status="RUNNING",
        rule_set_version=RULESET_VERSION, trigger=trigger,
        rule_ids=[r.rule_id for r in rules],
    )
    db.add(run)
    db.flush()
    for rule in rules:
        result = evaluate(rule, application, db)
        db.add(ValidationFinding(
            run_id=run.id, rule_id=rule.rule_id, rule_version=rule.version,
            status=result["status"], severity=rule.severity,
            field_key=result.get("field_key", ""),
            application_value=result.get("application_value", ""),
            evidence_ref_id=uuidlib.UUID(result["evidence_ref_id"]) if result.get("evidence_ref_id") else None,
            explanation=result["explanation"], remediation=result.get("remediation", ""),
            finding_type=rule.check_kind,
            lifecycle_status=("Open" if result["status"] in ("FAIL", "NEEDS_REVIEW") else "Closed"),
            human_review_required=(
                result["status"] in ("FAIL", "NEEDS_REVIEW")
                and (rule.severity in ("high", "critical")
                     or rule.check_kind in ("duplicate_document", "reference_match",
                                            "cross_doc_match"))
            ),
            rule_official=rule.official,
            reference_value=result.get("reference_value", ""),
            institutional_record=result.get("institutional_record", ""),
        ))
    # supersede prior findings for these rules
    prior = db.scalars(select(ValidationFinding).where(
        ValidationFinding.rule_id.in_([r.rule_id for r in rules]),
        ValidationFinding.run_id != run.id,
        ValidationFinding.superseded.is_(False))).all()
    for f in prior:
        f.superseded = True
    run.status = "SUCCEEDED"
    run.finished_at = utcnow()
    audit(db, action="validation.run", actor_id=actor_id,
          application_id=application.id, target=",".join([r.rule_id for r in rules]),
          after={"run_id": str(run.id), "rules": len(rules)})
    db.commit()
    return run


def run_validation(db: Session, application: Application, rule_ids: list[str] | None,
                   trigger: str, actor_id=None) -> ValidationRun:
    return _run(db, application, rule_ids, trigger, actor_id)


def revalidate_fields(db: Session, application: Application, field_keys: set[str],
                      actor_id=None) -> list[str]:
    affected = db.scalars(select(RegulatoryRule).where(RegulatoryRule.active.is_(True))).all()
    affected = [r for r in affected if set(r.field_keys or []) & field_keys]
    if not affected:
        return []
    _run(db, application, [r.rule_id for r in affected], "revalidation", actor_id)
    return [r.rule_id for r in affected]


def latest_findings(db: Session, application_id) -> list[ValidationFinding]:
    latest_run = db.scalar(select(ValidationRun).where(
        ValidationRun.application_id == application_id)
        .order_by(ValidationRun.created_at.desc()).limit(1))
    if latest_run is None:
        return []
    return db.scalars(select(ValidationFinding).where(
        ValidationFinding.run_id == latest_run.id).order_by(
        ValidationFinding.severity.desc())).all()


# --- endpoints ---

class ValidationIn(BaseModel):
    rule_ids: list[str] | None = None


@router.post("/applications/{application_id}/validations", status_code=201)
def trigger_validation(application_id: str, body: ValidationIn | None = None,
                       auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    application = load_application(db, application_id)
    require_permission(auth, application.institution_id, "validation.run")
    run = run_validation(db, application, body.rule_ids if body else None, "manual",
                         actor_id=auth.user.id)
    return {"data": {"run_id": str(run.id), "status": run.status}}


@router.get("/validations/{run_id}")
def get_run(run_id: str, auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    run = db.get(ValidationRun, uuidlib.UUID(run_id))
    if run is None:
        raise HTTPException(404, "Validation run not found")
    application = db.get(Application, run.application_id)
    require_membership(auth, application.institution_id)
    return {"data": {
        "run_id": str(run.id), "status": run.status, "trigger": run.trigger,
        "rule_set_version": run.rule_set_version, "rule_ids": run.rule_ids,
        "at": str(run.created_at),
    }}


@router.get("/validations/{run_id}/findings")
def get_findings(run_id: str, auth: AuthContext = Depends(get_auth),
                 db: Session = Depends(get_db)):
    run = db.get(ValidationRun, uuidlib.UUID(run_id))
    if run is None:
        raise HTTPException(404, "Validation run not found")
    application = db.get(Application, run.application_id)
    require_membership(auth, application.institution_id)
    findings = db.scalars(select(ValidationFinding).where(
        ValidationFinding.run_id == run.id).order_by(
        ValidationFinding.severity.desc())).all()
    return {"data": [_finding_json(db, f) for f in findings]}


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, auth: AuthContext = Depends(get_auth),
                db: Session = Depends(get_db)):
    finding = db.get(ValidationFinding, uuidlib.UUID(finding_id))
    if finding is None:
        raise HTTPException(404, "Finding not found")
    run = db.get(ValidationRun, finding.run_id)
    application = db.get(Application, run.application_id)
    require_membership(auth, application.institution_id)
    return {"data": _finding_json(db, finding, include_evidence=True)}


def _finding_json(db: Session, f: ValidationFinding, include_evidence: bool = False) -> dict:
    out = {
        "finding_id": str(f.id), "rule_id": f.rule_id, "rule_version": f.rule_version,
        "status": f.status, "severity": f.severity, "field_key": f.field_key,
        "application_value": f.application_value,
        "explanation": f.explanation, "remediation": f.remediation,
        "superseded": f.superseded,
        "finding_type": f.finding_type,
        "lifecycle_status": f.lifecycle_status,
        "human_review_required": f.human_review_required,
        "clarification": f.clarification,
        "correction_document_id": str(f.correction_document_id) if f.correction_document_id else None,
        "resolved_at": f.resolved_at,
        "rule_official": f.rule_official,
        "reference_value": f.reference_value,
        "institutional_record": f.institutional_record,
    }
    if include_evidence and f.evidence_ref_id:
        ref = db.get(EvidenceReference, f.evidence_ref_id)
        if ref:
            ef = db.get(ExtractedField, ref.extracted_field_id)
            doc = db.get(Document, ref.document_id)
            out["evidence"] = {
                "document_id": str(ref.document_id),
                "filename": doc.filename if doc else "",
                "page": ref.page, "text_span": ref.text_span,
                "extracted_value": ef.value if ef else "",
            }
    return out


@router.get("/regulatory-rules")
def list_rules(auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    rules = db.scalars(select(RegulatoryRule).where(RegulatoryRule.active.is_(True))
                       .order_by(RegulatoryRule.rule_id)).all()
    return {"data": [{
        "rule_id": r.rule_id, "title": r.title, "version": r.version,
        "source_section": r.source_section, "check_kind": r.check_kind,
        "severity": r.severity, "explanation": r.explanation,
        "remediation": r.remediation, "field_keys": r.field_keys,
    } for r in rules]}

# --- deficiency lifecycle ---

class ClarificationIn(BaseModel):
    note: str
    document_id: str | None = None


def _load_finding_context(db: Session, finding_id: str, auth: AuthContext):
    finding = db.get(ValidationFinding, uuidlib.UUID(finding_id))
    if finding is None:
        raise HTTPException(404, "Finding not found")
    run = db.get(ValidationRun, finding.run_id)
    application = db.get(Application, run.application_id) if run else None
    if application is None:
        raise HTTPException(404, "Finding not found")
    require_membership(auth, application.institution_id)
    return finding, application


@router.post("/findings/{finding_id}/clarification")
def submit_clarification(finding_id: str, body: ClarificationIn,
                         auth: AuthContext = Depends(get_auth),
                         db: Session = Depends(get_db)):
    finding, application = _load_finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "application.draft.update")
    finding.clarification = body.note.strip()
    if body.document_id:
        finding.correction_document_id = uuidlib.UUID(body.document_id)
    finding.lifecycle_status = "Correction Submitted"
    audit(db, action="finding.correction.submitted", actor_id=auth.user.id,
          application_id=application.id, target=finding.rule_id,
          after={"document_id": body.document_id})
    db.commit()
    return {"data": _finding_json(db, finding)}


@router.post("/findings/{finding_id}/revalidate")
def revalidate_finding(finding_id: str, auth: AuthContext = Depends(get_auth),
                       db: Session = Depends(get_db)):
    finding, application = _load_finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "validation.run")
    finding.lifecycle_status = "Revalidation Pending"
    db.commit()

    run = _run(db, application, None, "revalidation", actor_id=auth.user.id)
    new_finding = db.scalar(select(ValidationFinding).where(
        ValidationFinding.run_id == run.id,
        ValidationFinding.rule_id == finding.rule_id).limit(1))
    finding.superseded = True
    if new_finding is not None and new_finding.status == "PASS":
        finding.lifecycle_status = "Resolved"
        finding.resolved_at = utcnow().isoformat(timespec="seconds")
        application.workflow_stage = "revalidation"
    else:
        finding.lifecycle_status = "Unresolved"
    audit(db, action="finding.revalidated", actor_id=auth.user.id,
          application_id=application.id, target=finding.rule_id,
          after={"new_status": new_finding.status if new_finding else None})
    db.commit()
    return {"data": {
        "finding": _finding_json(db, finding),
        "revalidation": _finding_json(db, new_finding) if new_finding else None,
    }}


@router.post("/findings/{finding_id}/escalate")
def escalate_finding(finding_id: str, auth: AuthContext = Depends(get_auth),
                     db: Session = Depends(get_db)):
    finding, application = _load_finding_context(db, finding_id, auth)
    require_permission(auth, application.institution_id, "review.manage")
    finding.lifecycle_status = "Escalated for Human Review"
    finding.human_review_required = True
    application.workflow_stage = "human_review_pending"
    audit(db, action="finding.escalated", actor_id=auth.user.id,
          application_id=application.id, target=finding.rule_id)
    db.commit()
    return {"data": _finding_json(db, finding)}


@router.get("/findings/{finding_id}/history")
def finding_history(finding_id: str, auth: AuthContext = Depends(get_auth),
                    db: Session = Depends(get_db)):
    finding, application = _load_finding_context(db, finding_id, auth)
    run_ids = db.scalars(select(ValidationRun.id).where(
        ValidationRun.application_id == application.id)).all()
    rows = db.scalars(select(ValidationFinding).where(
        ValidationFinding.rule_id == finding.rule_id,
        ValidationFinding.run_id.in_(run_ids))
        .order_by(ValidationFinding.created_at)).all()
    return {"data": [{
        "run_id": str(r.run_id),
        "at": str(r.created_at),
        **_finding_json(db, r),
    } for r in rows]}

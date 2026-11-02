import uuid as uuidlib

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.config import settings
from ..core.db import Database, get_db
from ..core.security import AuthContext, get_auth, require_permission
from ..core.storage import ALLOWED_MIME, sha256, sniff_mime, storage
from ..models import (
    Document,
    DocumentProcessingRun,
    DocumentVersion,
    ExtractedField,
)
from ..workers.processing import process_document

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def enqueue_processing(database: Database, doc_id: str) -> None:
    """Run document processing inline (single-process demo)."""
    session = database.session()
    try:
        process_document(session, doc_id)
    finally:
        session.close()


@router.post("/upload", status_code=201)
async def upload_documents(
    request: Request,
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    institution_id: str = Form(...),
    application_id: str | None = Form(None),
    auth: AuthContext = Depends(get_auth),
    db: Session = Depends(get_db),
):
    inst_id = uuidlib.UUID(institution_id)
    require_permission(auth, inst_id, "document.upload")
    results = []
    for upload in files:
        data = await upload.read()
        if len(data) > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"{upload.filename} exceeds size limit")
        mime = sniff_mime(data)
        if mime is None:
            raise HTTPException(422, f"{upload.filename} is not a supported PDF/image")
        checksum = sha256(data)
        existing = db.scalar(select(Document).where(
            Document.institution_id == inst_id, Document.checksum == checksum))
        if existing:
            duplicate = Document(
                institution_id=inst_id,
                application_id=uuidlib.UUID(application_id) if application_id else existing.application_id,
                filename=upload.filename, mime_type=mime, size_bytes=len(data),
                checksum=checksum, doc_class=existing.doc_class, status="needs_review",
                status_detail=(f"Potential duplicate of {existing.filename} "
                               "(identical SHA-256); human review required."),
                uploaded_by=auth.user.id,
            )
            db.add(duplicate)
            db.flush()
            db.add(DocumentVersion(document_id=duplicate.id, version_no=1,
                                   checksum=checksum, storage_path="duplicates/" + checksum))
            db.add(DocumentProcessingRun(document_id=duplicate.id, status="NEEDS_REVIEW"))
            audit(db, action="document.duplicate", actor_id=auth.user.id,
                  institution_id=inst_id, application_id=duplicate.application_id,
                  target=upload.filename,
                  after={"duplicate_of": str(existing.id), "checksum": checksum})
            results.append({"document_id": str(duplicate.id), "duplicate": True,
                            "duplicate_of": str(existing.id),
                            "filename": upload.filename, "status": "needs_review"})
            continue
        rel = storage.put("", data)
        doc = Document(
            institution_id=inst_id,
            application_id=uuidlib.UUID(application_id) if application_id else None,
            filename=upload.filename, mime_type=mime, size_bytes=len(data),
            checksum=checksum, status="uploaded", uploaded_by=auth.user.id,
        )
        db.add(doc)
        db.flush()
        db.add(DocumentVersion(document_id=doc.id, version_no=1, checksum=checksum,
                              storage_path=rel))
        db.add(DocumentProcessingRun(document_id=doc.id, status="QUEUED"))
        audit(db, action="document.upload", actor_id=auth.user.id, institution_id=inst_id,
              application_id=doc.application_id, target=upload.filename)
        background.add_task(enqueue_processing, request.app.state.db, str(doc.id))
        results.append({"document_id": str(doc.id), "duplicate": False,
                        "filename": upload.filename, "status": "queued"})
    db.commit()
    return {"data": results}


@router.get("")
def list_documents(application_id: str | None = None,
                   auth: AuthContext = Depends(get_auth), db: Session = Depends(get_db)):
    rows = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
    out = []
    for doc in rows:
        if doc.institution_id not in auth.memberships:
            continue
        if application_id and str(doc.application_id) != application_id:
            continue
        out.append(_doc_brief(db, doc))
    return {"data": out}


@router.get("/{document_id}/status")
def document_status(document_id: str, auth: AuthContext = Depends(get_auth),
                    db: Session = Depends(get_db)):
    doc = _load_scoped(db, document_id, auth)
    run = db.scalar(select(DocumentProcessingRun).where(
        DocumentProcessingRun.document_id == doc.id)
        .order_by(DocumentProcessingRun.created_at.desc()).limit(1))
    return {"data": {
        "document_id": str(doc.id), "status": doc.status,
        "status_detail": doc.status_detail, "doc_class": doc.doc_class,
        "run_status": run.status if run else None,
    }}


@router.get("/{document_id}/fields")
def document_fields(document_id: str, auth: AuthContext = Depends(get_auth),
                    db: Session = Depends(get_db)):
    doc = _load_scoped(db, document_id, auth)
    fields = db.scalars(select(ExtractedField).where(
        ExtractedField.document_id == doc.id)).all()
    return {"data": {
        "document_id": str(doc.id), "doc_class": doc.doc_class,
        "fields": [{
            "field_name": f.field_name, "value": f.value,
            "confidence": f.confidence, "page": f.page, "text_span": f.text_span,
            "method": f.extraction_method,
        } for f in fields],
    }}


@router.get("/{document_id}/content")
def document_content(document_id: str, auth: AuthContext = Depends(get_auth),
                     db: Session = Depends(get_db)):
    doc = _load_scoped(db, document_id, auth)
    version = db.scalar(select(DocumentVersion).where(
        DocumentVersion.document_id == doc.id)
        .order_by(DocumentVersion.version_no.desc()).limit(1))
    try:
        data = storage.get(version.storage_path)
    except Exception:  # noqa: BLE001 - seeded demo docs have no stored bytes
        data = b""
    text = ""
    if doc.mime_type == "application/pdf" and data:
        import fitz
        with fitz.open(stream=data, filetype="pdf") as pdf:
            text = "\n".join(p.get_text() for p in pdf)
    return {"data": {"document_id": str(doc.id), "filename": doc.filename,
                     "mime_type": doc.mime_type, "text": text[:200_000]}}


def _load_scoped(db: Session, document_id: str, auth: AuthContext) -> Document:
    doc = db.get(Document, uuidlib.UUID(document_id))
    if doc is None:
        raise HTTPException(404, "Document not found")
    if doc.institution_id not in auth.memberships:
        raise HTTPException(403, "No access to this document")
    return doc


def _doc_brief(db: Session, doc: Document) -> dict:
    run = db.scalar(select(DocumentProcessingRun).where(
        DocumentProcessingRun.document_id == doc.id)
        .order_by(DocumentProcessingRun.created_at.desc()).limit(1))
    n_fields = db.scalar(select(func.count()).select_from(ExtractedField).where(
        ExtractedField.document_id == doc.id))
    return {
        "document_id": str(doc.id), "filename": doc.filename,
        "doc_class": doc.doc_class, "status": doc.status,
        "status_detail": doc.status_detail, "size_bytes": doc.size_bytes,
        "extracted_fields": n_fields,
        "run_status": run.status if run else None,
        "application_id": str(doc.application_id) if doc.application_id else None,
        "institution_id": str(doc.institution_id),
    }

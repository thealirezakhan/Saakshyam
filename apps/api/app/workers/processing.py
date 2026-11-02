import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import utcnow
from ..core.storage import storage
from ..models import (
    Document,
    DocumentProcessingRun,
    DocumentVersion,
    ExtractedField,
    EvidenceReference,
)

MAX_TEXT_CHARS = 200_000

# keyword classifiers: (doc_class, keywords) - order matters on ties
CLASSIFIERS = [
    ("previous_eoa", ["extension of approval", "eoa no", "eoa number", "approved intake"]),
    ("application_form", ["application form", "application no", "proposed intake"]),
    ("affidavit", ["affidavit", "deponent"]),
    ("payment_receipt", ["payment receipt", "receipt no", "ter charges", "amount:"]),
    ("trust_registration", ["trust registration", "registration no", "society"]),
    ("compliance_response", ["compliance response", "response reference"]),
    ("scrutiny_report", ["scrutiny deficiency", "deficiency report", "scrutiny report"]),
    ("compliance_declaration", ["compliance declaration", "institutional compliance"]),
    ("occupancy_certificate", ["occupancy certificate", "occupancy"]),
    ("fire_noc", ["fire", "noc", "safety", "fire service", "fire department"]),
    ("floor_plan", ["floor plan", "built-up area", "floors"]),
    ("faculty_declaration", ["faculty information declaration", "faculty information"]),
    ("faculty_statement", ["faculty", "professor", "assistant professor", "cadre",
                           "ph.d", "doctorate", "teaching staff"]),
    ("land_deed", ["land", "deed", "khasra", "bhulekh", "acre", "parcel", "survey"]),
    ("building_stability", ["stability", "structural", "building", "pwd", "civil"]),
    ("audited_accounts", ["audited", "accounts", "balance sheet", "expenditure",
                          "income", "auditor"]),
    ("infrastructure_photo", ["infrastructure evidence", "laboratory", "library",
                              "photograph", "photo"]),
    ("institution_profile", ["institution", "institute", "college", "profile",
                             "establishment", "registered"]),
]


def classify(text: str) -> str:
    t = text.lower()
    scores = {}
    for cls, kws in CLASSIFIERS:
        scores[cls] = sum(1 for k in kws if k in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unclassified"


def _find(page, text, pattern, flags=0):
    m = re.search(pattern, text, flags)
    if not m:
        return None
    return {"value": m.group(1).strip() if m.groups() else m.group(0).strip(),
            "span": m.group(0).strip(), "page": page}


EXTRACTORS = {
    "land_deed": [
        ("land_area_acres", r"(\d+(?:\.\d+)?)\s*(?:Acres?|acre|ac\.?)\b", re.I),
        ("land_area_acres_alt", r"(?:Land|Area|Parcel)[^\d]{0,30}(\d+(?:\.\d+)?)\s*(?:Acres?|acre|ac\.?)\b", re.I),
        ("plot_no", r"(?:Plot|Khasra|Survey)[\s:.#No-]*([\w/\-.]+)", re.I),
    ],
    "previous_eoa": [
        ("eoa_number", r"EoA\s*No[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("approved_intake", r"Approved\s+Intake[:\s]+(\d+)", re.I),
        ("academic_year", r"Academic\s+Year[:\s]+(\d{4}-\d{2})", re.I),
    ],
    "application_form": [
        ("application_number", r"Application\s*No[:\s]+([A-Z0-9][A-Z0-9\-]+)", re.I),
        ("proposed_intake", r"Proposed\s+Intake[:\s]+(\d+)", re.I),
        ("category", r"Category[:\s]+([A-Za-z /]+)", re.I),
    ],
    "faculty_declaration": [
        ("total_faculty", r"(?:Total|Verified)?\s*Faculty\s*[:\-\.=]?\s*(\d+)", re.I),
        ("faculty_phd_count", r"(?:Ph\.?D|Doctorate)[^\d]{0,20}(\d+)", re.I),
    ],
    "faculty_statement": [
        ("total_faculty", r"(?:Total|Verified)?\s*Faculty\s*[:\-\.=]?\s*(\d+)", re.I),
        ("total_faculty_alt", r"(\d+)\s*(?:faculty|teaching staff)", re.I),
        ("sanctioned_intake", r"(?:Sanctioned\s+)?Intake\s*[:\-\.=]?\s*([\d,]+)", re.I),
        ("faculty_phd_count", r"(?:Ph\.?D|Doctorate)[^\d]{0,20}(\d+)", re.I),
    ],
    "fire_noc": [
        ("fire_noc_expiry", r"(?:valid\s+till|valid\s+until|expiry|expires)[^\d]{0,20}(\d{1,2}\s+\w{3,10}\s+\d{4}|\d{4}-\d{2}-\d{2})", re.I),
        ("noc_number", r"(?:NOC|Certificate)\s*(?:No\.?|Number|#)?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9\-/]+)", re.I),
    ],
    "trust_registration": [
        ("registration_number", r"Registration\s*No[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("registration_date", r"Registration\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "affidavit": [
        ("affidavit_city", r"City[:\s]+([A-Za-z ]+)", re.I),
        ("affidavit_date", r"Affidavit\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "payment_receipt": [
        ("receipt_number", r"Receipt\s*No[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("amount", r"Amount[:\s]+(\d+)", re.I),
        ("payment_date", r"Payment\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "compliance_declaration": [
        ("declaration_date", r"Declaration\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "occupancy_certificate": [
        ("certificate_number", r"Certificate\s*No[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("valid_until", r"Valid\s+Until[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "floor_plan": [
        ("built_up_sqm", r"Built-up\s+Area[:\s]+(\d+)", re.I),
        ("floors", r"Floors[:\s]+(\d+)", re.I),
    ],
    "scrutiny_report": [
        ("eoa_reference", r"EoA\s+Reference[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("report_date", r"Report\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "compliance_response": [
        ("response_reference", r"Response\s+Reference[:\s]+([A-Z0-9][A-Z0-9/\-]+)", re.I),
        ("response_date", r"Response\s+Date[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    ],
    "infrastructure_photo": [
        ("label", r"(CSE Laboratory|Library)", re.I),
    ],
    "institution_profile": [
        ("contact_email", r"[\w.+-]+@[\w-]+\.[\w.]+", re.I),
        ("establishment_year", r"(?:established|establishment)[^\d]{0,20}(\d{4})", re.I),
    ],
    "building_stability": [
        ("certificate_no", r"(?:Certificate|Report)\s*(?:No\.?|#)?\s*([A-Z0-9\-/]+)", re.I),
    ],
    "audited_accounts": [
        ("financial_year", r"(?:FY|Financial Year|Year)[^\d]{0,10}(\d{4}-\d{2,4})", re.I),
    ],
}


def process_document(db: Session, doc_id: uuid.UUID | str) -> None:
    doc = db.get(Document, doc_id if isinstance(doc_id, uuid.UUID) else uuid.UUID(str(doc_id)))
    if doc is None:
        return
    run = DocumentProcessingRun(document_id=doc.id, status="RUNNING",
                                started_at=utcnow())
    db.add(run)
    doc.status = "processing"
    db.commit()

    try:
        version = db.scalar(select(DocumentVersion).where(
            DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.version_no.desc()).limit(1))
        data = storage.get(version.storage_path)
        pages, error = _extract_pages(data, doc.mime_type)
        if error:
            run.status = "NEEDS_REVIEW"
            doc.status = "needs_review"
            doc.status_detail = error
        else:
            full_text = "\n".join(pages)
            doc.doc_class = classify(full_text)
            if doc.doc_class == "unclassified":
                run.status = "NEEDS_REVIEW"
                doc.status = "needs_review"
                doc.status_detail = "Document type could not be classified; manual review required."
            else:
                extracted = _extract_fields(doc.doc_class, pages)
                if not extracted:
                    run.status = "NEEDS_REVIEW"
                    doc.status = "needs_review"
                    doc.status_detail = "No structured fields could be extracted; manual review required."
                else:
                    for field in extracted:
                        ef = ExtractedField(
                            document_id=doc.id, field_name=field["field_name"],
                            value=field["value"], confidence=field.get("confidence", 1.0),
                            page=field["page"], text_span=field["span"],
                            extraction_method="regex")
                        db.add(ef)
                        db.flush()
                        db.add(EvidenceReference(
                            document_id=doc.id, page=field["page"],
                            text_span=field["span"], extracted_field_id=ef.id,
                            checksum=doc.checksum))
                    run.status = "SUCCEEDED"
                    doc.status = "succeeded"
    except Exception as exc:  # noqa: BLE001
        run.status = "FAILED"
        doc.status = "failed"
        doc.status_detail = str(exc)[:500]
        run.error = str(exc)[:500]
    run.finished_at = utcnow()
    db.commit()


def _extract_pages(data: bytes, mime: str) -> tuple[list[str], str | None]:
    if mime == "application/pdf":
        import fitz  # PyMuPDF
        try:
            with fitz.open(stream=data, filetype="pdf") as pdf:
                pages = [p.get_text() for p in pdf]
            if any(p.strip() for p in pages):
                return [p[:MAX_TEXT_CHARS] for p in pages], None
            return _ocr_pdf_pages(data)
        except Exception as e:  # noqa: BLE001
            return [], f"PDF parsing failed: {e}"
    if mime in ("image/png", "image/jpeg"):
        return _ocr_image(data)
    return [], "Unsupported content type."


def _ocr_pdf_pages(data: bytes) -> tuple[list[str], str | None]:
    """Rasterise text-less PDF pages and OCR them (PaddleOCR). Abstains if unavailable."""
    try:
        import fitz
        with fitz.open(stream=data, filetype="pdf") as pdf:
            images = [p.get_pixmap(dpi=150).tobytes("png") for p in pdf]
    except Exception as e:  # noqa: BLE001
        return [], f"PDF rasterization failed: {e}"
    return _ocr_images(images)


def _ocr_image(data: bytes) -> tuple[list[str], str | None]:
    return _ocr_images([data])


def _ocr_images(images: list[bytes]) -> tuple[list[str], str | None]:
    kind, engine = _ocr_engine()
    if engine is None:
        return [], "No extractable text and OCR engine unavailable; manual review required."
    try:
        texts = []
        for img in images:
            texts.append(_run_ocr(kind, engine, img))
        if not any(t.strip() for t in texts):
            return [], "OCR produced no readable text; manual review required."
        return [t[:MAX_TEXT_CHARS] for t in texts], None
    except Exception as e:  # noqa: BLE001
        return [], f"OCR failed: {e}"


def _ocr_engine():
    """Prefer RapidOCR (ONNX, light, offline). Fall back to PaddleOCR if present."""
    try:
        from rapidocr_onnxruntime import RapidOCR
        return "rapid", RapidOCR()
    except Exception:  # noqa: BLE001
        pass
    try:
        from paddleocr import PaddleOCR
        try:
            return "paddle", PaddleOCR(use_textline_orientation=True, lang="en")
        except TypeError:
            return "paddle", PaddleOCR()
    except Exception:  # noqa: BLE001
        return None, None


def _run_ocr(kind: str, engine, image_bytes: bytes) -> str:
    if kind == "rapid":
        import io
        import numpy as np
        from PIL import Image
        arr = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        result, _ = engine(arr)
        return "\n".join(str(r[1]) for r in result if len(r) > 1) if result else ""
    result = engine(image_bytes)
    return _flatten_ocr(result)


def _flatten_ocr(result) -> str:
    """Flatten PaddleOCR 3.x result (list of dicts with 'rec_texts') to text."""
    if not result:
        return ""
    parts = []
    for item in result:
        if isinstance(item, dict):
            texts = item.get("rec_texts") or item.get("texts") or []
            parts.extend(texts)
        elif isinstance(item, str):
            parts.append(item)
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            parts.append(item[1])
    return "\n".join(str(t) for t in parts if t)


def _extract_fields(doc_class: str, pages: list[str]) -> list[dict]:
    patterns = EXTRACTORS.get(doc_class, [])
    found: dict[str, dict] = {}
    for page_no, text in enumerate(pages, start=1):
        for field_name, pattern, flags in patterns:
            if field_name.endswith("_alt") and field_name[:-4] in found:
                continue
            hit = _find(page_no, text, pattern, flags)
            if hit:
                canonical = field_name[:-4] if field_name.endswith("_alt") else field_name
                if canonical not in found:
                    hit["field_name"] = canonical
                    found[canonical] = hit
    return list(found.values())

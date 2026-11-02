import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from .core.db import Base, utcnow


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[str] = mapped_column(default=utcnow)


# --- Identity ---

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))


class AuthToken(Base, TimestampMixin):
    __tablename__ = "auth_tokens"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column()


class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(64), unique=True)


class InstitutionMembership(Base, TimestampMixin):
    __tablename__ = "institution_memberships"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # admin | preparer | compliance | reviewer | evc
    __table_args__ = (UniqueConstraint("user_id", "institution_id", "role"),)


class InstitutionalReferenceRecord(Base, TimestampMixin):
    """Simulated historical/authoritative value used for comparison (MVP only)."""
    __tablename__ = "institutional_reference_records"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    key: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[str] = mapped_column(Text)
    source_label: Mapped[str] = mapped_column(String(128), default="Simulated institutional record")
    as_of: Mapped[str | None] = mapped_column(String(32), nullable=True)


# --- Application domain ---

class Application(Base, TimestampMixin):
    __tablename__ = "applications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    reference_no: Mapped[str] = mapped_column(String(64), unique=True)
    application_type: Mapped[str] = mapped_column(String(128))
    academic_year: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(64), default="eoa_self_disclosure")
    workflow_stage: Mapped[str] = mapped_column(String(64), default="initial_validation")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    updated_at: Mapped[str] = mapped_column(default=utcnow, onupdate=utcnow)
    sections: Mapped[list["ApplicationSection"]] = relationship(
        back_populates="application", cascade="all, delete-orphan",
        order_by="ApplicationSection.order",
    )


class ApplicationSection(Base, TimestampMixin):
    __tablename__ = "application_sections"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    key: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer)
    fields: Mapped[list["ApplicationField"]] = relationship(
        back_populates="section", cascade="all, delete-orphan",
        order_by="ApplicationField.order",
    )
    application: Mapped[Application] = relationship(back_populates="sections")


class ApplicationField(Base, TimestampMixin):
    __tablename__ = "application_fields"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("application_sections.id"), index=True)
    key: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(16), default="text")  # text | number | date
    required: Mapped[bool] = mapped_column(default=True)
    locked: Mapped[bool] = mapped_column(default=False)
    order: Mapped[int] = mapped_column(Integer)
    section: Mapped[ApplicationSection] = relationship(back_populates="fields")
    values: Mapped[list["ApplicationFieldValue"]] = relationship(
        back_populates="field", cascade="all, delete-orphan",
        order_by="ApplicationFieldValue.created_at",
    )


class ApplicationFieldValue(Base, TimestampMixin):
    __tablename__ = "application_field_values"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("application_fields.id"), index=True)
    value: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True)
    source_extracted_field_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_fields.id"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    field: Mapped[ApplicationField] = relationship(back_populates="values")


# --- Document intelligence ---

class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id"), index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    doc_class: Mapped[str] = mapped_column(String(64), default="unclassified")
    status: Mapped[str] = mapped_column(String(32), default="uploaded")  # uploaded|processing|succeeded|needs_review|failed
    status_detail: Mapped[str] = mapped_column(Text, default="")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    checksum: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str] = mapped_column(String(512))
    document: Mapped[Document] = relationship(back_populates="versions")


class DocumentProcessingRun(Base, TimestampMixin):
    __tablename__ = "document_processing_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")  # QUEUED|RUNNING|SUCCEEDED|FAILED|NEEDS_REVIEW
    error: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[str | None] = mapped_column(nullable=True)
    finished_at: Mapped[str | None] = mapped_column(nullable=True)


class ExtractedField(Base, TimestampMixin):
    __tablename__ = "extracted_fields"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    page: Mapped[int] = mapped_column(Integer, default=1)
    text_span: Mapped[str] = mapped_column(Text, default="")
    extraction_method: Mapped[str] = mapped_column(String(64), default="regex")


class EvidenceReference(Base, TimestampMixin):
    __tablename__ = "evidence_references"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    page: Mapped[int] = mapped_column(Integer, default=1)
    text_span: Mapped[str] = mapped_column(Text, default="")
    extracted_field_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extracted_fields.id"), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64))


class VerificationRecord(Base, TimestampMixin):
    __tablename__ = "verification_records"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    method: Mapped[str] = mapped_column(String(64), default="simulated")
    outcome: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    request_id: Mapped[str] = mapped_column(String(64), default="")
    source: Mapped[str] = mapped_column(String(128), default="")
    reference_number: Mapped[str] = mapped_column(String(128), default="")
    submitted_value: Mapped[str] = mapped_column(Text, default="")
    returned_value: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(String(32), default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    manual_review_required: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[str | None] = mapped_column(nullable=True)


class EvcRecord(Base, TimestampMixin):
    __tablename__ = "evc_records"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id"), index=True, unique=True)
    status: Mapped[str] = mapped_column(String(32), default="recommended")
    reason: Mapped[str] = mapped_column(Text, default="")
    visit_mode: Mapped[str] = mapped_column(String(16), default="online")
    checklist: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[str] = mapped_column(default=utcnow, onupdate=utcnow)


class ReviewAction(Base, TimestampMixin):
    __tablename__ = "review_actions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("validation_findings.id"), nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    note: Mapped[str] = mapped_column(Text, default="")


# --- Regulatory knowledge ---

class RegulatorySource(Base, TimestampMixin):
    __tablename__ = "regulatory_sources"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255))
    authority: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(512), default="")
    version: Mapped[str] = mapped_column(String(32))
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")


class RegulatoryRule(Base, TimestampMixin):
    __tablename__ = "regulatory_rules"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    rule_id: Mapped[str] = mapped_column(String(64), unique=True)  # e.g. APH-7.2.1
    title: Mapped[str] = mapped_column(String(255))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulatory_sources.id"))
    source_section: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(16), default="1.0")
    check_kind: Mapped[str] = mapped_column(String(32))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    field_keys: Mapped[list] = mapped_column(JSON, default=list)  # application field keys consumed
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    explanation: Mapped[str] = mapped_column(Text, default="")
    remediation: Mapped[str] = mapped_column(Text, default="")
    applicability: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(default=True)
    academic_year: Mapped[str] = mapped_column(String(16), default="2026-27")
    application_categories: Mapped[list] = mapped_column(JSON, default=list)
    official: Mapped[bool] = mapped_column(default=False)
    needs_confirmation: Mapped[bool] = mapped_column(default=False)
    source_document: Mapped[str] = mapped_column(String(255), default="")


# --- Validation ---

class ValidationRun(Base, TimestampMixin):
    __tablename__ = "validation_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING")
    rule_set_version: Mapped[str] = mapped_column(String(32))
    trigger: Mapped[str] = mapped_column(String(32), default="manual")  # manual|revalidation|copilot
    rule_ids: Mapped[list] = mapped_column(JSON, default=list)
    finished_at: Mapped[str | None] = mapped_column(nullable=True)


class ValidationFinding(Base, TimestampMixin):
    __tablename__ = "validation_findings"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("validation_runs.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(64))
    rule_version: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))  # PASS|FAIL|NEEDS_REVIEW|NOT_APPLICABLE|NOT_EVALUATED
    severity: Mapped[str] = mapped_column(String(16))
    field_key: Mapped[str] = mapped_column(String(64), default="")
    application_value: Mapped[str] = mapped_column(Text, default="")
    evidence_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence_references.id"), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    remediation: Mapped[str] = mapped_column(Text, default="")
    superseded: Mapped[bool] = mapped_column(default=False)
    finding_type: Mapped[str] = mapped_column(String(64), default="")
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="Open")
    human_review_required: Mapped[bool] = mapped_column(default=False)
    clarification: Mapped[str] = mapped_column(Text, default="")
    correction_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(nullable=True)
    rule_official: Mapped[bool] = mapped_column(default=False)
    reference_value: Mapped[str] = mapped_column(Text, default="")
    institutional_record: Mapped[str] = mapped_column(Text, default="")


# --- Copilot ---

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)


class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    events: Mapped[list] = mapped_column(JSON, default=list)


class ToolExecution(Base, TimestampMixin):
    __tablename__ = "tool_executions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"), index=True, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    input: Mapped[dict] = mapped_column(JSON, default=dict)
    output: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="SUCCEEDED")
    error: Mapped[str] = mapped_column(Text, default="")


class DraftProposal(Base, TimestampMixin):
    __tablename__ = "draft_proposals"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="staged")  # staged|applied|discarded
    changes: Mapped[list] = mapped_column(JSON, default=list)
    reason: Mapped[str] = mapped_column(Text, default="")


# --- Audit ---

class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True, index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(128), default="")
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)

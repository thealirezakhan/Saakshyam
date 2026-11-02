export interface Institution {
  institution_id: string;
  name: string;
  role: string;
  permissions: string[];
}

export interface LoginResponse {
  token: string;
  user_id: string;
  name: string;
  email: string;
  institutions: Institution[];
}

export interface Field {
  field_id: string;
  key: string;
  label: string;
  type: string;
  required: boolean;
  locked: boolean;
  value: string;
  version: number;
  source_document_id: string | null;
}

export interface Section {
  section_id: string;
  key: string;
  title: string;
  completion: number;
  fields: Field[];
}

export interface ApplicationSummary {
  application_id: string;
  institution_id: string;
  reference_no: string;
  application_type: string;
  academic_year: string;
  category: string;
  category_title: string;
  workflow_stage: string;
  stages: Array<{ key: string; title: string }>;
  status: string;
  completion_pct: number;
  required_fields: { total: number; filled: number };
  sections: Section[];
}

export interface ChecklistItem {
  key: string;
  state: string;
  document_id: string | null;
  filename: string | null;
  status_detail: string | null;
}

export interface Checklist {
  application_id: string;
  category: string;
  category_title: string;
  items: ChecklistItem[];
  missing: number;
}

export interface WorkflowSummary {
  key: string;
  title: string;
  purpose: string;
  documents: string[];
  stages: string[];
  evc: string;
  needs_confirmation: boolean;
}

export interface Finding {
  finding_id: string;
  rule_id: string;
  rule_version: string;
  status: string;
  severity: string;
  field_key: string;
  application_value: string;
  explanation: string;
  remediation: string;
  superseded: boolean;
  finding_type?: string;
  lifecycle_status?: string;
  human_review_required?: boolean;
  clarification?: string;
  correction_document_id?: string | null;
  resolved_at?: string | null;
  rule_official?: boolean;
  reference_value?: string;
  institutional_record?: string;
  evidence?: {
    document_id: string;
    filename: string;
    page: number;
    text_span: string;
    extracted_value: string;
  };
}

export interface Report {
  application: { reference_no: string; application_type: string; academic_year: string };
  completion_pct: number;
  statuses: Record<string, number>;
  findings: Finding[];
  generated_at: string;
}

export interface DocumentItem {
  document_id: string;
  application_id: string | null;
  filename: string;
  mime_type: string;
  size_bytes: number;
  doc_class: string;
  status: string;
  status_detail: string | null;
  extracted_fields: number;
  created_at: string;
}

export interface ExtractedField {
  field_name: string;
  value: string;
  confidence: number;
  page: number;
  text_span: string;
  method: string;
}

export interface VerificationRecord {
  verification_id: string;
  request_id: string;
  document_id: string;
  method: string;
  source: string;
  reference_number: string;
  submitted_value: string;
  returned_value: string;
  result: string;
  timestamp: string;
  explanation: string;
  manual_review_required: boolean;
  banner: string;
}

export interface InfrastructureAnalysis {
  application_id: string;
  category: string;
  category_title: string;
  evidence: Array<{ document_id: string; filename: string; doc_class: string; status: string }>;
  duplicate_groups: Array<{ checksum: string; documents: Array<{ document_id: string; filename: string }> }>;
  missing_evidence: string[];
  declared: { built_up_sqm: string };
  evidence_values: { built_up_sqm: string };
  observations: string[];
  evc_recommended: boolean;
  disclaimer: string;
  simulated: boolean;
}

export interface EvcRecord {
  evc_id: string;
  status: string;
  reason: string;
  visit_mode: string;
  checklist: Array<{ item: string; status: string }>;
  notes: Array<{ author: string; note: string; at: string }>;
  updated_at: string;
  simulated: boolean;
}

export interface ReviewQueueItem {
  application_id: string;
  reference_no: string;
  category: string;
  workflow_stage: string;
  status: string;
  open_findings: number;
  human_review: number;
}

export interface ReviewAction {
  action: string;
  note: string;
  at: string;
  reviewer_id: string | null;
  finding_id: string | null;
}

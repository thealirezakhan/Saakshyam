# Validation Rules and Evidence Model

## 1. Principles

1. Deterministic rules decide pass/fail; the LLM only explains and orchestrates.
2. Every finding is traceable to a rule version and evidence (document, page, span,
   extracted value).
3. An anomaly is a signal for human review — never proof of forgery or misconduct.
4. The system never approves, rejects, penalises or makes a statutory decision.
5. Prototype-only rules are labelled and never presented as official regulation.

## 2. Finding schema (target)

| Field | Type | Notes |
|---|---|---|
| `finding_id` | UUID | Stable identifier |
| `application_id` | UUID | Owning application |
| `institution_id` | UUID | Owning institution |
| `application_category` | string | e.g. `increase_intake` |
| `academic_year` | string | e.g. `2026-27` |
| `severity` | enum | Critical, High, Medium, Low, Informational |
| `finding_type` | string | e.g. `faculty_inconsistency`, `expired_document`, `duplicate_evidence`, `anomaly_review` |
| `description` | text | Human-readable statement |
| `rule_id` | string | e.g. `DEMO-FAC-001` |
| `rule_source` | string | Document + clause/annexure |
| `rule_official` | bool | False = prototype demo rule |
| `document_id`, `page`, `text_span` | refs | Evidence location |
| `extracted_value` | string | What was read |
| `expected_value` / `comparison_value` | string | Rule expectation or reference value |
| `institutional_record_ref` | string | Which historical record was compared |
| `explanation` | text | Why it matters |
| `recommended_action` | text | Corrective step |
| `status` | enum | See lifecycle |
| `human_review_required` | bool | Always true for Critical/High anomalies |
| `created_at`, `updated_at` | timestamps | Audit |

## 3. Rule schema (target)

| Field | Notes |
|---|---|
| `rule_id` | Unique, stable |
| `title` | Short name |
| `academic_year` | Rules are AY-specific |
| `application_categories` | Which categories the rule applies to |
| `source_document` | APH / public notice / addendum / prototype |
| `clause_ref` | Handbook clause or annexure |
| `effective_date` | Where known |
| `validation_logic` | Typed evaluator key + params |
| `severity` | Default severity |
| `explanation` | Applicant-facing explanation |
| `remediation` | Recommended action |
| `official` | true only when verified against current official source |
| `needs_confirmation` | true when an addendum may have changed it |
| `active` | Enable/disable |

## 4. Finding lifecycle

```
Open
  → Awaiting Institution Response
  → Correction Submitted
  → Revalidation Pending
  → Resolved            (rule now passes, evidenced)
  → Unresolved          (still failing after response)
  → Escalated for Human Review
```

Rules:
- Findings are never deleted. A new validation run supersedes but the old row remains
  (existing `superseded` flag + run history).
- A correction must reference the uploaded document and its evidence.
- Resolution requires a passing revalidation of the affected rule(s).
- Escalation is a human action (reviewer), not automatic adverse action.

## 5. Evidence model

| Layer | Purpose |
|---|---|
| `Document` + `DocumentVersion` | File identity, checksum, storage |
| `ExtractedField` | Value + page + span + method + confidence |
| `EvidenceReference` | Links extracted field to document/page/span/checksum |
| `InstitutionalReferenceRecord` (new) | Historical/authoritative value (simulated) |
| `VerificationRecord` (exists, extend) | Mock authority verification attempt + outcome |
| `ValidationFinding` | Rule + values + evidence ref + lifecycle |
| `AuditEvent` | Who did what, when |

Comparison matrix used by rules:

| Source A | Source B | Rule type | Finding when mismatch |
|---|---|---|---|
| Application declaration | Uploaded document | cross_doc_match | `inconsistency` |
| Application declaration | Institutional reference | reference_match | `reference_mismatch` |
| Document | Institutional reference | reference_match | `reference_mismatch` |
| Uploaded image | Other uploaded image | image_reuse | `duplicate_evidence` (human review) |
| Document metadata | Stated metadata | metadata_consistency | `anomaly_review` (human review) |

## 6. Rule catalogue (demo)

Official/verified rules are marked `official=true`; illustrative rules are
`official=false` and rendered as "Prototype demo rule".

| Rule ID | Title | Category | Logic | Severity | Official |
|---|---|---|---|---|---|
| APH-4.1 | Institution name required | all | required_field | High | yes (concept) |
| APH-4.2 | Registered address required | all | required_field | High | yes (concept) |
| APH-7.2.1 | Faculty ratio (1:20) | increase_intake, eoa | ratio_min | High | yes (concept) |
| APH-9.1 | Fire NOC valid | all | expiry_within | High | yes (concept) |
| APH-8.1 | Land area minimum | all | min_value | High | yes (concept) |
| DEMO-FAC-001 | Faculty count consistency | increase_intake | cross_doc_match | High | no |
| DEMO-FAC-002 | Faculty vs institutional record | increase_intake | reference_match | High | no |
| DEMO-DOC-001 | Duplicate/reused photo | increase_intake | image_reuse | Medium | no |
| DEMO-DOC-002 | Document reference continuity | increase_intake | metadata_consistency | Medium | no |
| DEMO-NOC-001 | NOC expired | all | expiry_within | High | concept |
| DEMO-INF-001 | Declared labs vs evidence | increase_intake | reference_match | Medium | no |
| DEMO-VER-001 | Source verification pending | all | verification_status | Informational | no |

> "yes (concept)" means the requirement concept exists in the APH but the exact clause,
> parameters and addendum state must be confirmed before production. The MVP labels
> these as sample rules.

## 7. Severity and human-review policy

| Severity | Meaning | Human review |
|---|---|---|
| Critical | Blocks readiness; safety/statutory | Mandatory |
| High | Material deficiency | Mandatory before EVC/adverse note |
| Medium | Needs clarification | Recommended |
| Low | Minor/format | Reviewer discretion |
| Informational | Pending verification/notice | No |

Anomaly-type findings (duplicate image, metadata inconsistency, visual alteration signal)
are **always** worded as "potential anomaly requiring human review", severity Medium/High,
and never "forged" or "fraudulent".

## 8. Safeguards in code and UI

- Rule evaluators return `status` only; no evaluator calls an LLM.
- The copilot cannot invent findings; it can only explain persisted findings.
- No tool exists to approve/reject or alter committee outcomes.
- UI shows `rule_official` and "Prototype demo rule" where applicable.
- Mock verification always renders the SIMULATED banner.

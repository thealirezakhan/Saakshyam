# AICTE COPILOT
## Product Requirements Document (PRD)

**Product:** AICTE Copilot  
**Category:** Agentic AI / Regulatory Technology / Document Intelligence  
**Target platform:** Web application  
**Primary users:** Higher education institutions, application preparers, compliance teams, and authorized regulatory reviewers  
**Product direction:** Conversational, agentic application preparation, validation, and scrutiny workspace  
**Status:** Initial product specification — Version 1.0

---

# 1. Product Vision

AICTE Copilot is an AI-powered regulatory application workspace that helps educational institutions prepare, validate, organize, and review applications for AICTE approval.

Instead of navigating complex forms, manually checking regulatory requirements, and repeatedly searching through documents, users interact with an intelligent conversational copilot.

The copilot understands the institution's application, processes uploaded documents, identifies missing or inconsistent information, checks applicable regulatory requirements, and performs permitted application operations through integrated tools.

It maintains a live understanding of the application and its supporting evidence throughout the workflow.

**Core vision: Make regulatory application preparation conversational, intelligent, transparent, and significantly easier to manage.**

AICTE Copilot is not intended to replace statutory scrutiny or official approval authority. It provides application assistance, preliminary validation, evidence organization, and decision support while keeping authorized officials in control of regulatory decisions.

---

# 2. Problem Statement

Preparing an AICTE approval application involves multiple interconnected activities:

- Understanding applicable approval requirements and guidelines.
- Collecting institutional, faculty, infrastructure, financial, and other supporting information.
- Preparing and uploading multiple supporting documents.
- Ensuring consistency between application fields and submitted evidence.
- Identifying missing, expired, incomplete, or potentially inconsistent documents.
- Understanding regulatory requirements and their applicability.
- Responding to observations and correcting application deficiencies.
- Tracking application progress and maintaining supporting records.

These activities can create substantial administrative effort and increase the possibility of errors.

Existing form-centric workflows do not necessarily provide users with a unified intelligent assistant that understands the complete application context and can help them perform tasks across documents, forms, validation, and review.

## 2.1 Proposed Solution

AICTE Copilot introduces a conversational agent that operates across the entire application workspace.

Users can ask:

- "Check whether my application is ready for submission."
- "Find all missing documents."
- "Compare the faculty information in my application with the uploaded faculty records."
- "Show me the requirements applicable to this programme."
- "Why is this infrastructure requirement marked incomplete?"
- "Update the application using the information extracted from this document."
- "Revalidate the application after my corrections."
- "Prepare a summary of unresolved compliance issues."

The copilot responds with explanations and, when authorized, executes the relevant operations.

---

# 3. Product Goals

## 3.1 Primary Goals

1. Build a conversational-first interface for AICTE application preparation and scrutiny.
2. Reduce repetitive manual data entry through intelligent document extraction.
3. Detect missing information and inconsistencies across application fields and supporting documents.
4. Translate regulatory requirements into understandable, traceable validation checks.
5. Enable users to perform application operations through natural language.
6. Maintain a live, synchronized view of application progress and validation status.
7. Provide explainable findings with links to supporting documents and applicable rules.
8. Support different user roles with appropriate permissions and workflows.

## 3.2 Non-Goals

The initial product will not:

- Autonomously grant or reject AICTE approval.
- Claim that a document is genuine without an authorized verification source.
- Bypass official portals, access controls, or institutional authorization.
- Treat an LLM-generated response as a statutory regulatory decision.
- Submit applications or modify official records without the required authorization and confirmation.
- Guarantee integration with AICTE or third-party government systems unless supported by approved APIs or access arrangements.

---

# 4. Target Users and Roles

## 4.1 Institution Administrator

Responsible for managing the institution's workspace, application, team members, and submissions.

**Capabilities:**
- Create and manage institution profiles.
- Start and manage applications.
- Upload and organize institutional documents.
- Invite application preparers.
- Review application completeness.
- Approve internal changes.
- Monitor application progress.

## 4.2 Application Preparer

Responsible for filling application information and preparing supporting documentation.

**Capabilities:**
- Interact with the copilot.
- Upload documents.
- Extract and review document information.
- Fill application fields.
- Resolve missing information.
- Run validation checks.
- Track corrections and outstanding tasks.

## 4.3 Compliance Officer

Responsible for ensuring application information is consistent with applicable requirements.

**Capabilities:**
- Review regulatory findings.
- Inspect evidence references.
- Review discrepancies.
- Verify corrections.
- Generate compliance reports.
- Maintain internal review notes.

## 4.4 Authorized Regulatory Reviewer

A separate role intended for an authorized regulatory review workflow, where access and integration are available.

**Capabilities:**
- View assigned applications.
- Inspect application information and evidence.
- Review system-generated observations.
- Record official observations.
- Request clarification or additional information.
- Maintain an official review record.
- Perform decisions only through authorized regulatory procedures.

**Important:** The institution-facing prototype must not imply that it has access to restricted AICTE reviewer systems. A reviewer dashboard can be demonstrated independently with role-based access and sample data.

---

# 5. Core Product Experience: The Conversational Copilot

This is the most important part of AICTE Copilot.

The copilot should not behave like a generic chatbot that only answers questions. It should function as an application-aware agent capable of understanding context, planning tasks, using tools, updating application state, and verifying outcomes.

## 5.1 Conversational-First Workspace

The main workspace should contain three connected areas:

### A. Left Sidebar — Navigation and Context

Contains:

- Institution profile.
- Current application.
- Application history.
- Documents and evidence.
- Compliance and scrutiny.
- Verification records.
- Reports.
- Team and role management.
- Settings.

The sidebar should allow users to switch between applications without losing the current conversational context.

### B. Centre — AI Copilot Conversation

The conversation is the primary interaction area.

It should support:

- Natural-language instructions.
- Follow-up questions.
- File and document uploads.
- Contextual suggestions.
- AI processing indicators.
- Tool execution status.
- Structured results.
- Interactive confirmation cards.
- Validation summaries.
- Evidence citations.
- Action history.
- Conversation history.

The conversation must understand which institution and application are currently active.

### C. Right Panel — Live Application Workspace

A persistent application context panel that updates as the copilot works.

It should display:

- Application identity.
- Current application status.
- Completion percentage.
- Current workflow stage.
- Section-wise completion.
- Missing information.
- Document status.
- Validation status.
- Outstanding observations.
- Recent changes.

The panel must remain synchronized with application data. When the copilot updates a permitted field, the corresponding application information should update in the panel.

## 5.2 Context-Aware Agent

The copilot should understand the current application context without requiring the user to repeatedly explain it.

It should have access to authorized contextual information such as:

- Institution profile.
- Application type.
- Academic year.
- Programme information.
- Uploaded documents.
- Extracted document fields.
- Current application values.
- Validation findings.
- Previous corrections.
- Pending tasks.
- Applicable rule versions.

Example:

User: "Check the faculty details."

The copilot should understand that this refers to the faculty information in the active application, identify relevant uploaded records, compare them with application data, and return specific findings.

It should not respond with a generic explanation of faculty requirements.

## 5.3 Agentic Task Execution

The copilot must follow a controlled execution cycle:

1. **Understand:** Interpret the user's request and identify the active application context.
2. **Plan:** Break the request into smaller operations.
3. **Retrieve:** Fetch relevant application data, documents, and regulatory rules.
4. **Select tools:** Choose the required document-processing, validation, or application-management tools.
5. **Execute:** Perform authorized operations.
6. **Verify:** Confirm whether the operations succeeded and inspect the resulting application state.
7. **Explain:** Present the result, evidence, and any remaining limitations.

The agent must never claim an action succeeded unless the underlying operation confirms success.

## 5.4 Tool-Using Copilot

The copilot should have access to a controlled collection of tools.

**Document tools**
- Upload document.
- List documents.
- Read document metadata.
- Extract text and structured fields.
- Compare documents.
- Identify missing pages or unreadable content.
- Classify document types.

**Application tools**
- Read application.
- Read application sections.
- Update permitted draft fields.
- Retrieve section completion.
- Create internal tasks.
- Save application changes.
- Generate application summaries.

**Compliance tools**
- Retrieve applicable requirements.
- Run validation rules.
- Compare application values against evidence.
- Identify missing requirements.
- Generate evidence-linked observations.
- Rerun affected validations.

**Verification tools**
- Check available QR codes or digital signatures.
- Validate document metadata and consistency.
- Connect to authorized verification services when available.
- Record verification attempts and their outcomes.
- Route unsupported verification cases for manual review.

**Reporting tools**
- Generate compliance reports.
- Generate missing-document reports.
- Export evidence indexes.
- Prepare internal review summaries.

Each tool must have a defined input schema, permission requirement, output schema, error handling, and audit record.

## 5.5 Permission-Aware Execution

Not every instruction should execute automatically.

Classify actions into three levels:

**Level 1 — Read-only actions**

Examples:
- Explain a regulation.
- Show missing documents.
- Summarize application progress.
- Compare existing records.

These can execute without additional confirmation when the user has permission.

**Level 2 — Reversible draft actions**

Examples:
- Populate an empty draft field.
- Update a draft using extracted information.
- Organize documents into categories.
- Create an internal correction task.

The copilot should display a preview or change summary and follow the institution's configured confirmation policy.

**Level 3 — High-impact actions**

Examples:
- Final submission.
- Official declarations.
- Irreversible changes.
- External verification requests that require authorization.
- Official review decisions.

These require explicit authorization and must never be performed solely on the basis of an ambiguous conversational instruction.

## 5.6 Action Preview and Confirmation

Before making important changes, the copilot should show:

- Requested operation.
- Affected application section.
- Existing value.
- Proposed value.
- Source document or evidence.
- Reason for the change.
- Expected consequence.

Actions should have clear controls:

- Confirm changes.
- Edit proposal.
- Cancel.

After execution, the copilot must display the actual result and updated application state.

## 5.7 Conversational Memory and Application Memory

Maintain two distinct types of context:

**Conversation context**
- Current discussion.
- User preferences for the session.
- Previous questions and clarifications.
- Pending conversational tasks.

**Application context**
- Persisted institution and application data.
- Documents and extracted fields.
- Validation results.
- Rule versions.
- Approved changes.
- Audit history.

Application context must be retrieved from the backend rather than relying on the LLM's conversation history as the source of truth.

---

# 6. Novelty Features and Product Differentiators

These features should define the product's innovation. They should be prioritized over generic chatbot functionality.

## 6.1 Application-Aware Agentic Copilot

**Concept:** One conversational interface that can operate across the entire application lifecycle.

Instead of navigating separate screens for documents, forms, validation, and reports, users can issue natural-language instructions.

Example:

"Review the application, identify the five most important issues, and prepare the corrections."

The copilot can:
- Retrieve application information.
- Run applicable checks.
- Prioritize findings.
- Identify the source of each issue.
- Prepare suggested corrections.
- Request confirmation for draft updates.
- Rerun validation after changes.

**Novelty:** The AI is an action-oriented application agent, not merely a question-answering assistant.

## 6.2 Cross-Document Intelligence and Consistency Graph

**Concept:** Understand relationships between documents, application fields, and regulatory requirements.

For example, a faculty member's details may appear in:
- Faculty information form.
- Qualification certificate.
- Appointment letter.
- Experience certificate.
- Other supporting records.

The system creates relationships between extracted entities and corresponding application fields.

It can identify:
- Different spellings of a person's name.
- Conflicting qualification details.
- Inconsistent dates.
- Different faculty counts across records.
- Missing supporting evidence.
- Documents that do not support a claimed application value.

**Novelty:** Validation occurs across the entire evidence set rather than checking each document independently.

## 6.3 Evidence-Linked Regulatory Reasoning

**Concept:** Every compliance finding should be traceable to both the applicable regulatory requirement and the evidence used to evaluate it.

Each finding should contain:

- Requirement ID.
- Rule version.
- Applicability conditions.
- Application value.
- Supporting document.
- Extracted evidence.
- Validation result.
- Explanation.
- Confidence or uncertainty indicator.

Example:

"Faculty information requires further review because the faculty count entered in the application differs from the count extracted from the uploaded faculty statement."

The user can click the finding to open the relevant document and inspect the supporting text.

**Novelty:** Explainable compliance checks with evidence provenance instead of unexplained AI-generated warnings.

## 6.4 Live Application Synchronization

**Concept:** The application workspace behaves like a live document that the copilot can read, update, and validate.

Example:

User: "Use the uploaded institutional profile to fill the institution details."

Copilot:
1. Reads the uploaded document.
2. Extracts relevant fields.
3. Identifies missing or ambiguous values.
4. Shows a proposed update.
5. Applies confirmed changes.
6. Updates the live application panel.
7. Reruns affected checks.

**Novelty:** The conversation and application are two views of the same underlying state.

## 6.5 Regulatory Change Impact Analysis

**Concept:** Regulatory requirements can change between approval cycles.

Maintain versioned regulatory rules and identify which applications or findings may be affected when a rule changes.

Capabilities:
- Store rule versions.
- Track effective dates.
- Compare rule versions.
- Identify changed requirements.
- Identify affected application sections.
- Flag applications requiring revalidation.
- Preserve the rule version used for earlier assessments.

**Novelty:** Moves beyond static checklist validation toward version-aware regulatory compliance.

This feature requires reliable source documents and a controlled process for updating and approving rule configurations.

## 6.6 Intelligent Document Authentication and Risk Screening

**Concept:** Use document intelligence and available verification mechanisms to identify records requiring additional scrutiny.

Possible checks:
- QR code presence and readability.
- Digital-signature verification where supported.
- Metadata inconsistencies.
- Duplicate document detection.
- Text and field consistency.
- Unexpected changes in formatting or structure.
- Cross-document discrepancies.
- Missing pages or suspicious alterations.

Results must be classified carefully:

- Verified through an authorized source.
- Verification unsuccessful.
- Unable to verify.
- Potential inconsistency detected.
- Manual review required.

**Novelty:** A multi-signal document risk-screening workflow with transparent evidence.

A visual anomaly or metadata mismatch is not proof of forgery. The system must not label a document fraudulent without an appropriate verification basis.

## 6.7 Intelligent Missing-Evidence Detection

**Concept:** Identify not only missing documents, but also missing evidence needed to substantiate a particular application claim.

Example:

"The application states that a faculty member has the required qualification, but the uploaded documents do not contain sufficient evidence to support that claim."

The system should distinguish:
- Document missing.
- Document uploaded but unreadable.
- Document present but incomplete.
- Evidence does not support the entered value.
- Evidence requires manual verification.

**Novelty:** Moves from simple document checklists to evidence sufficiency analysis.

## 6.8 Autonomous Revalidation After Corrections

**Concept:** When a user corrects an issue, the system automatically identifies the affected checks and reruns them.

Example:

1. A faculty qualification mismatch is detected.
2. The user uploads a corrected certificate.
3. The copilot extracts the updated information.
4. The evidence relationship is refreshed.
5. Related validation checks are rerun.
6. The finding changes to resolved, unresolved, or manual review required.

The system should not rerun unrelated expensive operations unnecessarily.

**Novelty:** A closed-loop correction workflow rather than a one-time validation report.

## 6.9 Application Readiness Intelligence

**Concept:** Provide a dynamic readiness assessment based on actual application completeness and validation outcomes.

The dashboard should show:
- Required information completed.
- Required documents available.
- Unresolved validation findings.
- Pending manual verification.
- Incomplete application sections.
- Critical blockers.
- Last validation time.

The system can classify an application as:
- Not started.
- In progress.
- Needs attention.
- Ready for internal review.
- Ready for authorized submission review.

Avoid presenting a readiness score as an AICTE approval probability.

## 6.10 Interactive Regulatory Analysis

**Concept:** Allow users to investigate why a requirement applies and how it relates to their application.

Example:

"Why is this requirement applicable to our institution?"

The copilot should:
- Identify the applicable institution/application attributes.
- Retrieve the relevant rule.
- Explain applicability.
- Show the supporting source.
- Identify missing information needed for a definitive assessment.

The user can ask follow-up questions directly from the finding.

---

# 7. Core User Workflows

## 7.1 Workflow A — Start an Application

1. User logs in.
2. Selects or creates an institution profile.
3. Starts a new application.
4. Selects the applicable application category and academic cycle.
5. System initializes the application structure.
6. Copilot introduces the workflow and identifies required information.
7. User begins entering details or uploading documents.

**Expected result:** An application workspace with an initialized checklist and conversational context.

## 7.2 Workflow B — Upload and Process Documents

1. User uploads one or multiple documents.
2. System stores the originals securely.
3. Document classification identifies document types.
4. OCR extracts text.
5. Structured extraction identifies relevant fields.
6. System records page-level evidence references.
7. User reviews extracted values.
8. Confirmed values become available for application mapping.
9. The copilot summarizes processing results.

**Expected result:** A searchable document repository with extracted fields and evidence references.

## 7.3 Workflow C — Conversational Application Filling

User:

"Fill the institution profile using the documents I uploaded."

Copilot:
1. Identifies the requested application section.
2. Retrieves relevant documents.
3. Extracts candidate values.
4. Maps values to application fields.
5. Identifies conflicting or missing values.
6. Presents a proposed change summary.
7. Applies approved changes.
8. Updates the live application workspace.

**Expected result:** Reduced manual data entry with reviewable field-level provenance.

## 7.4 Workflow D — Full Application Scrutiny

User:

"Run a complete scrutiny of my application."

Copilot:
1. Retrieves the current application.
2. Determines the applicable validation checklist.
3. Checks required fields.
4. Checks document completeness.
5. Compares application data against supporting evidence.
6. Executes applicable deterministic rules.
7. Flags potential inconsistencies.
8. Identifies verification requirements.
9. Generates a prioritized findings report.
10. Updates the application readiness view.

**Expected result:** A structured scrutiny report with evidence-linked findings.

## 7.5 Workflow E — Resolve a Finding

1. User opens a finding.
2. Copilot explains why it was raised.
3. User opens the supporting evidence.
4. Copilot suggests possible corrections.
5. User provides updated information or a document.
6. Copilot previews any application change.
7. User confirms the change.
8. System updates the draft.
9. Affected rules are rerun.
10. Finding status is updated.

**Expected result:** A traceable correction cycle.

## 7.6 Workflow F — Document Verification

1. User selects a document for verification.
2. System determines available verification methods.
3. QR, signature, metadata, and consistency checks are performed where supported.
4. System records the verification source and timestamp.
5. Unverifiable cases are routed for manual review.
6. Copilot explains the outcome and its limitations.

**Expected result:** A transparent verification record rather than an unsupported genuine/fake label.

## 7.7 Workflow G — Generate a Compliance Report

User:

"Prepare a compliance report for internal review."

Copilot:
1. Retrieves the latest application state.
2. Retrieves current validation findings.
3. Organizes findings by category and severity.
4. Includes applicable rule references.
5. Links supporting documents and evidence.
6. Summarizes unresolved issues.
7. Generates a downloadable report.

**Expected result:** An auditable internal compliance report.

---

# 8. Functional Requirements

## 8.1 Authentication and Access Control

- Secure login and session management.
- Role-based access control.
- Institution-level data isolation.
- User invitation and access management.
- Permission checks for every agent tool.
- Audit logging for sensitive operations.

## 8.2 Institution and Application Management

- Create and edit institution profiles.
- Support multiple applications per institution.
- Track application type and academic cycle.
- Maintain application sections and field metadata.
- Save draft progress.
- Track application status.
- Maintain application history.

## 8.3 Document Management

- Upload PDF and common image formats.
- Support multiple-file uploads.
- Store original files.
- Generate document previews.
- Classify document types.
- Extract text using OCR.
- Extract structured fields.
- Record page-level evidence.
- Track processing status.
- Detect duplicate files.
- Maintain document versions.

## 8.4 AI Copilot

- Natural-language interaction.
- Application-aware context retrieval.
- Multi-turn conversations.
- Tool calling.
- Task planning.
- Structured responses.
- Action previews.
- Confirmation workflows.
- Execution status.
- Error reporting.
- Evidence citations.
- Conversation history.

## 8.5 Compliance Engine

- Store regulatory rules in structured form.
- Support rule versioning.
- Define rule applicability.
- Execute deterministic validations.
- Support cross-field checks.
- Support cross-document checks.
- Generate findings.
- Record evidence references.
- Revalidate affected rules.
- Preserve historical results.

## 8.6 Reporting

- Application completeness report.
- Missing-document report.
- Compliance findings report.
- Document verification report.
- Internal review summary.
- Downloadable PDF export.
- Evidence index export.

---

# 9. UI/UX Requirements — Stitch Design Fidelity

**Design source of truth:** Google Stitch project `AICTE Copilot Workspace`

**Project ID:** `15677314180217415042`

The implementation must use the five supplied Stitch screens as the visual and interaction reference.

Do not reinterpret these designs into a generic SaaS dashboard. Do not replace the conversational workspace with a conventional sidebar-and-form application.

The supplied Stitch screens should be treated as the primary UI specification.

## 9.1 Screen 1 — AICTE Copilot: Scrutiny & Validation

**Screen ID:** `01608c80c5304b46b343abf5be6d186a`

Purpose:
- Main application scrutiny workspace.
- Display the AI copilot conversation.
- Show validation progress and findings.
- Allow users to investigate and resolve issues.

Required interactions:
- Start scrutiny.
- Ask follow-up questions.
- Open a finding.
- Navigate to supporting evidence.
- Preview a proposed correction.
- Confirm a draft update.
- Rerun validation.

## 9.2 Screen 2 — AICTE Copilot: Documents & Evidence

**Screen ID:** `53e074c59c0e43f89e4595f519bcc756`

Purpose:
- Manage uploaded application documents.
- Display extracted information.
- Link documents to application fields and regulatory findings.

Required interactions:
- Upload documents.
- Preview documents.
- Inspect extracted fields.
- View page-level evidence.
- Compare records.
- View verification status.
- Open related compliance findings.

## 9.3 Screen 3 — AICTE Copilot: Live Application Workspace

**Screen ID:** `9ec9a01ca3084d4fadd7557ec73abaf6`

Purpose:
- Show the live application alongside the copilot.
- Maintain a synchronized view of application data.
- Display application completion and current status.

Required interactions:
- Navigate application sections.
- Edit permitted draft fields.
- View field sources.
- Review proposed changes.
- Save updates.
- See completion status update.

## 9.4 Screen 4 — AICTE Copilot: Interactive Analysis

**Screen ID:** `bb940c586a634ca08df59c466dd86490`

Purpose:
- Investigate regulatory requirements and application findings.
- Provide interactive, explainable compliance analysis.

Required interactions:
- Open a regulatory requirement.
- View applicability conditions.
- Inspect supporting evidence.
- Ask the copilot why a finding was generated.
- Compare application values with extracted evidence.
- View related findings.

## 9.5 Screen 5 — AICTE Copilot: Ray AI Workspace

**Screen ID:** `f1b5f1fbf731414280ed9679d2d32c1f`

Purpose:
- Primary conversational agent workspace.
- Demonstrate the product's central agentic experience.

Required interactions:
- Natural-language task requests.
- File uploads.
- Suggested prompts.
- AI processing states.
- Tool execution progress.
- Interactive result cards.
- Action confirmations.
- Live application updates.
- Follow-up conversations.

## 9.6 Design Implementation Rules

- Match the supplied Stitch screens as closely as possible.
- Preserve layout, spacing, typography, visual hierarchy, colors, cards, borders, and component placement.
- Reuse exported screen assets and generated code wherever possible.
- Maintain a shared design system across all five screens.
- Preserve responsive behavior without changing the desktop design unnecessarily.
- Implement functional controls rather than static visual mockups.
- Ensure navigation between all five screens is connected.
- Keep the right-side live application context synchronized with backend state.
- Keep the central copilot visually dominant.

**Visual fidelity is a product requirement, not an optional styling preference.**

---

# 10. Technical Architecture

## 10.1 Recommended Architecture

**Frontend**
- React / Next.js.
- TypeScript.
- Tailwind CSS.
- Reusable component system.
- Streaming chat interface.
- PDF/document preview.
- Live application state panel.

**Backend**
- Python FastAPI.
- REST APIs.
- WebSocket or server-sent events for streaming updates.
- Background task processing.
- Role-based authorization.

**Database and Storage**
- PostgreSQL for structured application data.
- Object storage for original documents.
- Redis for caching and task coordination where needed.
- Vector search for semantic retrieval over regulatory and document content.

**AI and Document Intelligence**
- LLM for conversational understanding, planning, explanations, and tool selection.
- OCR for document text extraction.
- Structured extraction for field identification.
- Embeddings and retrieval for regulatory/document context.
- Deterministic rules engine for compliance decisions.

The exact models and providers should be selected after evaluating accuracy, cost, deployment constraints, and data privacy requirements.

## 10.2 Agent Architecture

The LLM must not have unrestricted direct database access.

Use a controlled tool-execution architecture:

1. User message.
2. Intent and context resolution.
3. Task planning.
4. Tool selection.
5. Permission validation.
6. Tool execution.
7. Result validation.
8. Application-state update.
9. User-facing explanation.

Every write operation should be executed through a backend service that enforces permissions and validates input.

## 10.3 Regulatory Rules Engine

Do not rely on the LLM alone to determine whether an application satisfies a regulatory requirement.

Represent rules as structured records containing:

- Rule ID.
- Rule title.
- Source document.
- Source section/page.
- Rule version.
- Effective date.
- Applicability conditions.
- Required input fields.
- Validation logic.
- Severity.
- Explanation.
- Evidence requirements.

The LLM can explain rules and help interpret user requests, but deterministic checks should evaluate clearly defined conditions.

Ambiguous regulatory interpretations should be marked for human review.

## 10.4 High-Level Data Flow

User → Copilot → Context Retrieval → Task Planner → Permission Check → Tool Execution → Document/Rules Services → Result Verification → Application Update → Copilot Explanation

Supporting services:
- Document storage.
- OCR and extraction.
- Application database.
- Regulatory knowledge base.
- Rules engine.
- Verification adapters.
- Audit service.

---

# 11. Data Model

The initial system should support the following core entities:

| Entity | Purpose |
|---|---|
| User | Login and identity |
| Role | Permissions |
| Institution | Institution profile |
| Application | Application instance |
| ApplicationSection | Logical application sections |
| ApplicationField | Individual application fields |
| Document | Uploaded document metadata |
| DocumentVersion | Document revision history |
| ExtractedField | Structured extracted information |
| EvidenceReference | Document/page/text evidence |
| RegulatorySource | Official regulatory source |
| RegulatoryRule | Structured compliance requirement |
| RuleVersion | Historical rule configuration |
| ValidationRun | Individual validation execution |
| ValidationFinding | Generated issue or observation |
| VerificationRecord | Document verification attempt and outcome |
| Conversation | Copilot conversation |
| AgentTask | Planned agent operation |
| ToolExecution | Tool input, result, and execution status |
| AuditEvent | Record of important user and system actions |

Maintain clear relationships between application fields, documents, extracted fields, regulatory rules, and validation findings.

---

# 12. Security, Privacy and Governance

Security must be built into the application from the beginning.

Requirements:

- Role-based access control.
- Institution-level data isolation.
- Secure file storage.
- Encryption in transit and at rest.
- Restricted document access.
- Secure session management.
- Input validation.
- Malware scanning for uploaded files.
- Audit logs for important operations.
- Retention and deletion policies.
- Protection against prompt injection in uploaded documents.
- Protection against unauthorized tool invocation.
- Explicit authorization for high-impact actions.

Uploaded document content must be treated as untrusted input. Instructions contained inside uploaded files must never override system policies or tool permissions.

The system should record:
- Who performed an action.
- Which application was affected.
- What changed.
- When it changed.
- Which evidence was used.
- Which rule version was evaluated.
- Whether human confirmation was obtained.

---

# 13. MVP Scope

The first version should focus on proving the core conversational workflow rather than implementing every possible government integration.

## Phase 1 — Core Prototype

**Must-have:**
- Authentication and role selection.
- Institution profile.
- Application creation.
- Document upload.
- OCR and structured extraction.
- Conversational copilot.
- Application-aware context retrieval.
- Tool-calling agent.
- Application field mapping.
- Configurable validation rules.
- Cross-document consistency checks.
- Evidence-linked findings.
- Live application workspace.
- Confirmation before draft updates.
- Basic audit logging.

**Demo outcome:**

A user uploads supporting documents, asks the copilot to fill the application, reviews proposed changes, runs scrutiny, receives evidence-linked findings, corrects an issue, and sees validation rerun.

This should be the primary end-to-end demonstration.

## Phase 2 — Advanced Intelligence

- Regulatory change impact analysis.
- More advanced cross-document entity matching.
- QR and digital-signature verification where supported.
- Document anomaly screening.
- Advanced application readiness analysis.
- Compliance report generation.
- Reviewer dashboard.
- Advanced analytics.

## Phase 3 — Integration and Deployment

- Approved external verification integrations.
- Official portal integration where APIs and authorization are available.
- Institution-wide workflows.
- Advanced reviewer collaboration.
- Production monitoring.
- Scalability and security hardening.

---

# 14. Acceptance Criteria

The MVP is considered functionally successful when the following scenarios work end to end.

### AC-01: Document Upload
A user can upload a supported document, view its processing status, and inspect the resulting extracted fields.

### AC-02: Field Extraction
Extracted values include a reference to their source document and page wherever available.

### AC-03: Conversational Context
The copilot can answer a question about the active application without requiring the user to restate the application details.

### AC-04: Tool Execution
The copilot can select and execute an authorized tool based on a natural-language request.

### AC-05: Draft Updates
The copilot can prepare a proposed application update, obtain the required confirmation, and persist the update.

### AC-06: Compliance Validation
The system can run configured rules and generate structured findings.

### AC-07: Evidence Traceability
Every generated finding contains the applicable rule reference and available supporting evidence.

### AC-08: Correction Workflow
A user can correct an issue and trigger revalidation of affected rules.

### AC-09: Permission Enforcement
A user cannot execute an operation outside their assigned permissions, even if the LLM attempts to invoke it.

### AC-10: Auditability
Important application changes and tool executions are recorded with user, timestamp, and operation details.

### AC-11: UI Synchronization
The live application panel reflects persisted backend changes rather than displaying only temporary chatbot output.

### AC-12: Human Authority
The copilot cannot autonomously issue an official approval or rejection.

---

# 15. Success Metrics

All figures below are proposed evaluation targets, not existing performance claims.

| Metric | Proposed target |
|---|---:|
| Selected-field extraction accuracy | ≥90% |
| Evidence-reference coverage for generated findings | 100% |
| Tool execution success on supported test scenarios | ≥95% |
| Unauthorized tool operations successfully blocked | 100% |
| Test applications processed in pilot | 100 |
| Validation findings with rule references | 100% |
| Critical workflow acceptance tests passed | 100% |

Additional measurements:
- Median application pre-screening time.
- Precision and recall of discrepancy detection.
- False-positive rate for document anomaly screening.
- Average time to resolve a finding.
- Cost per application processed.
- Copilot task completion rate.
- User correction rate for extracted fields.

Do not present an extraction accuracy target as equivalent to regulatory correctness.

---

# 16. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Poor scan quality | Image preprocessing, OCR confidence, manual correction |
| Incorrect extraction | Field-level review and source evidence |
| LLM hallucination | Retrieval-grounded responses and deterministic validation |
| Incorrect rule interpretation | Versioned rule configurations and human review |
| False document-fraud flags | Multi-signal checks and cautious result classifications |
| Unauthorized actions | Backend permission checks and confirmation gates |
| Regulatory changes | Source tracking, rule versioning, impact analysis |
| External API unavailability | Adapter architecture and manual verification fallback |
| Sensitive document exposure | Encryption, access controls, isolation, and audit logs |
| Stale application context | Backend retrieval and state synchronization |

---

# 17. Demo Scenario — The Product's Main Selling Point

The demo should tell one continuous story rather than showcase disconnected screens.

**Scenario: An institution wants to prepare an AICTE application.**

**Step 1 — Start**

User:
"Help me prepare my institution's application."

Copilot:
"I can help organize your application, process supporting documents, and run preliminary compliance checks. Let's begin with your institution profile."

**Step 2 — Upload**

User uploads institution profile, faculty records, and infrastructure documents.

Copilot:
"I've processed the uploaded files. I identified the institution profile, faculty records, and infrastructure information. Two documents require your review because some extracted fields are unclear."

**Step 3 — Populate**

User:
"Use these documents to fill the application."

Copilot:
"I found information for 18 application fields. Fifteen have clear supporting evidence. Three need clarification. Review the proposed changes before I update the draft."

**Step 4 — Scrutiny**

User:
"Run a complete scrutiny."

Copilot:
"Preliminary scrutiny is complete. I found four issues: one missing document, two data inconsistencies, and one item requiring manual verification."

**Step 5 — Investigate**

User:
"Why is the faculty information inconsistent?"

Copilot:
"The faculty count entered in the application differs from the count extracted from the uploaded faculty statement. I have linked the relevant document and extracted evidence."

**Step 6 — Correct**

User uploads a corrected statement.

Copilot:
"I've processed the new document. Would you like me to update the faculty section using the extracted information?"

**Step 7 — Revalidate**

User confirms.

Copilot:
"The draft has been updated. I've rerun the affected checks. The faculty discrepancy is now resolved. Two other findings remain open."

**Step 8 — Report**

User:
"Prepare a compliance summary."

Copilot generates a report with:
- Application completion.
- Resolved findings.
- Outstanding findings.
- Supporting evidence.
- Applicable rule references.
- Manual verification requirements.

**Final message:** The application is better prepared for internal review. This is not an official AICTE approval decision.

---

# 18. Product Positioning

AICTE Copilot should be positioned as:

**An agentic AI workspace for AICTE application preparation, document intelligence, evidence-backed compliance validation, and regulatory scrutiny assistance.**

Its defining difference is the combination of:

1. Conversational application management.
2. Tool-using agentic execution.
3. Cross-document intelligence.
4. Evidence-linked regulatory reasoning.
5. Live application synchronization.
6. Autonomous revalidation after user-approved corrections.
7. Human-controlled regulatory governance.

The primary product principle:

**One conversation. One live application. Multiple intelligent capabilities.**

The user should not need to understand the internal system architecture to get work done. They should be able to describe the task, review what the copilot proposes, authorize permitted actions, and understand the result.

---

# 19. Initial Development Priorities

Recommended implementation order:

1. Establish the application data model and role permissions.
2. Build the Stitch-matched five-screen frontend.
3. Implement document upload, storage, and preview.
4. Implement OCR and structured extraction.
5. Build the application-aware conversational interface.
6. Implement the agent orchestration and controlled tool layer.
7. Build the configurable regulatory rules engine.
8. Implement evidence-linked validation findings.
9. Implement draft updates with confirmation.
10. Implement correction and revalidation workflows.
11. Add audit logs and reporting.
12. Run end-to-end tests using synthetic institution applications.

**Do not begin by building a generic chatbot. Build the application state, document pipeline, and tool layer that make the copilot genuinely capable of doing work.**
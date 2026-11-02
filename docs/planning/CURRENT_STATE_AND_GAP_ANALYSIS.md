# Current State and Gap Analysis

Audit date: 2026-11-01. Based on a direct inspection of `apps/api`, `apps/web`,
`apps/api/tests`, `design/stitch`, and the project docs.

## 1. What exists today

| Layer | Implementation |
|---|---|
| Frontend | Next.js 15 + TypeScript + Tailwind at `apps/web`, port 3100. One Copilot (`/copilot`) + Overview, Applications, Documents, Validation, Analysis. Stitch HTML preserved in `design/stitch`. |
| Backend | FastAPI at `apps/api`, SQLite by default. Modules: identity, applications, documents, validation, copilot, reporting; workers/processing. |
| Agent | LangGraph `StateGraph` (`modules/agent.py`) against Groq `openai/gpt-oss-20b` when `LLM_API_KEY` is set; deterministic fallback otherwise. Tool registry + permission gate reused. |
| Documents | Upload (PDF/PNG/JPEG), magic-byte sniff, checksum dedupe, PyMuPDF text, RapidOCR (ONNX) for images/text-less PDFs, keyword classification, regex extraction. |
| Validation | Deterministic evaluators: required_field, format_email, min_value, ratio_min, expiry_within, cross_doc_match. Findings persisted with rule version. |
| Copilot | One conversation per user+application, persisted; SSE events incl. tool results; contextual `AskCopilot` from workspaces. |
| Auth/roles | Bearer tokens; roles admin, preparer, compliance, reviewer; permission map in `core/security.py`. |
| Audit | `audit_events` written for login, uploads, field changes, validation, report, proposals. |
| Seed | Northstar Institute of Technology, app `NIT-DEL-2026-0142`, 6 documents with evidence, 12 sample rules. |
| Tests | 38 pytest tests passing. |

## 2. Requirement-by-requirement gap

Legend: **Implemented** · **Partial** · **Missing** · **Future** · **Simulated in MVP**

| # | Requirement | Status | What exists | Gap / change needed |
|---|---|---|---|---|
| 1 | Identify application category | **Missing** | All apps treated the same | Add category to application; category selector in UI; category-based workflow routing |
| 2 | Apply academic-year-specific checklist | **Missing** | Single sample rule set (version "1.0") | Version rules/checklists by AY; add AY field to rules; addendum-aware "needs confirmation" flag |
| 3 | Check application against institutional records | **Partial** | Cross-doc checks against extracted uploaded fields | Add a synthetic institutional reference record (approved programmes, intake, faculty, land) and compare against it |
| 4 | Read/classify/extract documents | **Implemented** | PDF text + RapidOCR + classifiers + regex | Broaden document classes; add office-document formats (xlsx/docx) or declare PDF/image-only |
| 5 | Missing/incomplete/expired/inconsistent docs | **Partial** | required_field, expiry_within, cross_doc_match; doc status | Add category document checklist with uploaded/missing/expired/unverified states |
| 6 | Manipulation/duplication/anomaly detection | **Missing** | Upload checksum dedupe only | Add duplicate-image hash detection, reused-image flag, metadata inconsistency, "potential anomaly — human review" (never fraud) |
| 7 | Verification via issuing authority | **Missing** | None | Mock verification adapter with deterministic outcomes + labelled "SIMULATED" |
| 8 | Regulatory & infrastructure evidence | **Partial** | land/built-up/fire rules | Add infrastructure evidence inventory and simulated analysis (duplicates, gaps, declared-vs-evidence) |
| 9 | Additional evidence / physical inspection | **Missing** | None | Add EVC recommendation workflow and evidence-request records |
| 10 | Evidence-linked validation reports | **Implemented** | Findings carry rule, value, evidence ref; `/report` | Extend finding schema (category, AY, status, human-review flag, institutional record) |
| 11 | Audit trail | **Implemented** | `audit_events` | Ensure all new actions (verification, EVC, rectification, review) are audited |
| 12 | Support authorized human scrutiny/decision | **Partial** | Roles + read-only reviewer; no reviewer UI | Add reviewer workspace (observations, clarification requests, manual-verification flag) |
| 13 | Never declare fraud / make decisions | **Implemented** | No approve/reject tools; validation is deterministic | Enforce wording guardrails; never expose "fraud" labels |
| 14 | Category-based workflow architecture | **Missing** | None | Add `app/workflows/categories.py` config + routing; UI shows stages |
| 15 | Evidence + verification model | **Partial** | Findings + evidence refs | Add verification records, institutional reference records, finding lifecycle/status |
| 16 | Deficiency → rectification lifecycle | **Partial** | Findings + staged proposals; no status lifecycle | Add finding statuses (Open → Awaiting Response → Correction Submitted → Revalidation Pending → Resolved/Unresolved/Escalated), correction upload, revalidation, history |
| 17 | Reviewer workflow | **Partial** | reviewer role (read-only) | Reviewer observations, request evidence, mark manual verification, recommend EVC |
| 18 | EVC workflow | **Missing** | None | EVC recommendation → planning → checklist → observations → final human note (synthetic) |
| 19 | Role workspaces (admin/scrutiny/EVC/system) | **Partial** | 4 roles; no EVC role, no role switching | Add EVC reviewer role; demo role switch; reviewer/admin dashboards |
| 20 | Contextual copilot | **Implemented** | Single conversation + structured context + tools | Feed category/checklist/verification/EVC context; deterministic conversation scripts |
| 21 | Dashboard metrics | **Partial** | Single-app overview | Add multi-application aggregate metrics derived from the same dataset |
| 22 | Synthetic institution + documents | **Missing** | Northstar seed, no files | Add Aarohan dataset, 15+ real PDFs/images, metadata, historical records |
| 23 | Mock verification environment | **Missing** | None | Add deterministic verification service + UI (6 outcomes) |
| 24 | Infrastructure evidence analysis | **Missing** | None | Add synthetic photos/floor plans/equipment; simulated analysis |
| 25 | Judge runbook / expected results | **Missing** | None | Add `docs/demo/*` (this planning phase) |
| 26 | Reset to known demo state | **Partial** | Delete SQLite DB | Add explicit reset script + fixture-based reseed |
| 27 | No dead buttons / consistent data | **Partial** | Core flows work | Audit every workspace after new features; single dataset source |
| 28 | Preserve Stitch design | **Implemented** | Design tokens + layouts preserved | Extend within the same visual language |

## 3. Architectural observations

1. **Rules are data, not code** — good. Extend `RegulatoryRule` with `academic_year`,
   `application_categories`, `official` (bool), `source_document`, `effective_date`,
   and `needs_confirmation`.
2. **Findings already persist rule version and evidence** — extend with category, AY,
   lifecycle status, human-review flag, institutional-record reference.
3. **Conversation is persisted per user+application** — good for the "one assistant"
   model. Pass category/stage/verification context as structured JSON.
4. **Document processing is synchronous (inline) when Redis is absent** — fine for the
   demo; keep it.
5. **Seed is identity-centric** — needs a demo-tenant seed module separated from the
   production seed, with a reset switch.
6. **No category/workflow module exists** — add a pure-config module so the chat layer
   never hardcodes rules.

## 4. Reuse plan (do not rewrite)

- Keep Next.js App Router, Tailwind tokens, Stitch layouts, `TopNav`/`AskCopilot`,
  `Badge`, `PetalIcon`, `Copilot` SSE client.
- Keep FastAPI modules and `_execute_tool` gate; extend rather than replace.
- Keep SQLite + local storage; no Redis/Celery/S3 in the MVP.
- Extend the existing seed/tests rather than creating a parallel app.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Mixing Northstar and Aarohan demo data | One demo dataset module; reset script; catalogue of expected results |
| Over-claiming verification | UI label `SIMULATED VERIFICATION — no live authority connection` |
| Presenting sample rules as official | `official=false` flag rendered as "Prototype demo rule" |
| Scope creep into production integrations | Phases 4–10 are local simulators; no external calls |
| Broken screens after refactor | End-to-end runbook + expected-results checklist executed before judging |

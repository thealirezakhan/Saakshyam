# MVP Implementation Plan

Goal: a polished, repeatable SIH demonstration of AICTE Copilot assisting an institution
and an authorised reviewer through a realistic approval-scrutiny process. Not a
production system.

## Guiding constraints

- Prototype-only infrastructure: SQLite, local storage, in-process processing, mock
  verification. No Redis/Celery/S3/external integrations.
- Preserve the existing Next.js + FastAPI app and Stitch design language.
- Deterministic demo data and repeatable reset.
- No simulated result presented as an official AICTE/authority response.
- AI never approves, rejects, or declares fraud.

## Phase overview

| Phase | Name | MVP? |
|---|---|---|
| 1 | Research and current-state audit | MVP |
| 2 | Categories, rules, workflow config | MVP |
| 3 | Synthetic institution, application, documents | MVP |
| 4 | Document upload, extraction, validation simulation | MVP |
| 5 | Cross-document and institutional-record comparison | MVP |
| 6 | Mock issuing-authority verification | MVP |
| 7 | Infrastructure evidence + EVC workflow | MVP |
| 8 | Copilot conversations and context | MVP |
| 9 | Deficiency rectification and revalidation | MVP |
| 10 | Reviewer workspace, audit, reporting | MVP |
| 11 | Judge runbook and end-to-end testing | MVP |
| F1 | Real portal/DigiLocker integrations, Postgres/pgvector, Celery, S3, auth hardening | Future |

---

## Phase 1 — Research and current-state audit
- **Objective:** Ground the MVP in the official process and the real codebase.
- **Screens:** none.
- **Backend:** none.
- **Data:** official sources registry.
- **Files:** `docs/research/AICTE_OFFICIAL_PROCESS_RESEARCH.md`,
  `docs/planning/CURRENT_STATE_AND_GAP_ANALYSIS.md`.
- **Acceptance:** sources cited with URL/clause; gaps classified; uncertainties explicit.
- **Depends on:** none. **Status: done.**

## Phase 2 — Categories, rules, workflow config
- **Objective:** Select checklist/stages by application category; version rules by AY.
- **Screens:** category selector on new-application; workflow stage strip on application.
- **Backend:** `app/workflows/categories.py`; extend `Application` (category, workflow
  stage), `RegulatoryRule` (academic_year, categories, official, source, needs_confirmation);
  `GET /api/v1/workflows` and `GET /api/v1/workflows/{key}`.
- **Data:** 8 category workflows; demo rule catalogue.
- **Files:** `app/workflows/categories.py`, `app/models.py`, `app/modules/applications.py`,
  `app/seed.py`, `apps/web/app/application/page.tsx`.
- **Acceptance:** creating an application picks a category and shows its document
  checklist and stages; no generic path.
- **Depends on:** Phase 1.

## Phase 3 — Synthetic institution, application, documents
- **Objective:** One canonical demo tenant + real files.
- **Screens:** institution/application display already exists; add demo dataset.
- **Backend:** `demo-data` fixtures + `scripts/seed_demo.py`; reset command.
- **Data:** Aarohan Institute of Technology (Pune), app `DEMO-EVENT-2026-001`,
  category `increase_intake`, 15+ PDFs/images, historical records, users, findings,
  verification cases, audit events.
- **Files:** `demo-data/documents/*`, `demo-data/dataset.json`,
  `demo-data/document_metadata.json`, `scripts/generate_demo_data.py`,
  `scripts/seed_demo.py`.
- **Acceptance:** reset yields Aarohan + one primary app + documents; every document
  carries the synthetic watermark; facts consistent except intended discrepancies.
- **Depends on:** Phase 2.

## Phase 4 — Upload, extraction, validation simulation
- **Objective:** Upload the real files and surface processing/extraction/findings.
- **Screens:** Documents (upload, status, inspector); Validation (findings).
- **Backend:** extend processing for document classes; category checklist evaluation;
  missing/expired/unverified states; new finding fields.
- **Data:** document metadata → expected extraction.
- **Files:** `app/workers/processing.py`, `app/modules/documents.py`,
  `app/modules/validation.py`, `apps/web/app/documents/page.tsx`,
  `apps/web/app/validation/page.tsx`.
- **Acceptance:** each demo document reaches the expected classification/extraction;
  checklist shows uploaded/missing/expired.
- **Depends on:** Phase 3.

## Phase 5 — Cross-document and institutional-record comparison
- **Objective:** Demonstrate multi-source comparison (the core value).
- **Screens:** Validation finding detail; Analysis comparison.
- **Backend:** `InstitutionalReferenceRecord`; `reference_match` evaluator; extend
  `cross_doc_match`; anomaly/duplicate-image checks.
- **Data:** historical faculty/land/intake records; intentionally inconsistent values.
- **Files:** `app/models.py`, `app/modules/validation.py`, `app/seed.py`,
  `apps/web/app/validation/page.tsx`, `apps/web/app/analysis/page.tsx`.
- **Acceptance:** faculty declaration vs faculty list vs institutional record produces a
  finding with all three values; anomalies flagged for human review, not fraud.
- **Depends on:** Phase 4.

## Phase 6 — Mock issuing-authority verification
- **Objective:** Deterministic verification workflow with 6 outcomes.
- **Screens:** document verification panel; verification records list.
- **Backend:** `MockVerificationAdapter` interface + deterministic implementation;
  `POST /api/v1/documents/{id}/verify`, `GET /api/v1/verifications/{id}`.
- **Data:** cases: verified, mismatch, expired, pending, unavailable, manual review.
- **Files:** `app/modules/verification.py`, `app/core/verification.py` (adapter),
  `app/models.py`, `apps/web/app/documents/page.tsx`.
- **Acceptance:** each case returns the documented outcome; banner
  `SIMULATED VERIFICATION — NO LIVE GOVERNMENT OR ISSUING-AUTHORITY CONNECTION`.
- **Depends on:** Phase 4.

## Phase 7 — Infrastructure evidence + EVC workflow
- **Objective:** Evidence review and EVC recommendation.
- **Screens:** Infrastructure section; EVC workspace.
- **Backend:** evidence inventory; simulated analysis (duplicates, gaps, declared-vs-
  evidence); EVC recommendation + visit plan + checklist + observations;
  `POST /api/v1/applications/{id}/evc/recommend`, `.../evc/notes`.
- **Data:** building/lab/library photos, floor plan, equipment list; one duplicate image.
- **Files:** `app/modules/infrastructure.py`, `app/modules/evc.py`, `app/models.py`,
  `apps/web/app/application/page.tsx` (infrastructure), `apps/web/app/evc/page.tsx`.
- **Acceptance:** analysis lists evidence, flags duplicate/missing, recommends EVC as a
  human-confirmed recommendation; no claim that a photo proves readiness.
- **Depends on:** Phase 5.

## Phase 8 — Copilot conversations and context
- **Objective:** Nine deterministic conversations tied to the active application.
- **Screens:** `/copilot` with structured result cards.
- **Backend:** extend agent context (category, stage, verification, EVC); deterministic
  fallback intents for the 9 scripts; tool results rendered as cards.
- **Data:** seeded findings/documents/verifications.
- **Files:** `app/modules/copilot.py`, `app/modules/agent.py`,
  `apps/web/app/copilot/page.tsx`, `apps/web/lib/agent.ts`.
- **Acceptance:** A–I produce the expected grounded responses; no random answers.
- **Depends on:** Phases 4–7.

## Phase 9 — Deficiency rectification and revalidation
- **Objective:** Full lifecycle with retained history.
- **Screens:** finding detail → upload correction → clarification → revalidate → status.
- **Backend:** status transitions; correction submission endpoint; revalidate affected
  rules; supersede but retain; audit.
- **Data:** corrected faculty statement (consistent values).
- **Files:** `app/modules/validation.py`, `app/modules/documents.py`, `app/models.py`,
  `apps/web/app/validation/page.tsx`.
- **Acceptance:** finding moves Open → … → Resolved; previous finding remains in history;
  application status updates.
- **Depends on:** Phases 5–6.

## Phase 10 — Reviewer workspace, audit, reporting
- **Objective:** Human scrutiny support.
- **Screens:** reviewer queue; finding review; observations; request evidence; EVC
  recommendation; report.
- **Backend:** reviewer endpoints (observations, clarification request, manual-verification
  flag, recommend EVC); report includes verification + rectification history + audit.
- **Data:** synthetic reviewer observations and committee notes.
- **Files:** `app/modules/review.py`, `app/modules/reporting.py`,
  `apps/web/app/review/page.tsx`, `apps/web/app/reports/page.tsx`.
- **Acceptance:** reviewer can add observations and request evidence; report is
  evidence-linked; AI cannot change outcomes.
- **Depends on:** Phases 6–9.

## Phase 11 — Judge runbook and end-to-end testing
- **Objective:** Repeatable demonstration.
- **Screens:** all.
- **Backend:** reset script.
- **Data:** expected-results checklist.
- **Files:** `docs/demo/JUDGE_DEMONSTRATION_RUNBOOK.md`,
  `docs/demo/SYNTHETIC_DATA_CATALOG.md`, `docs/demo/EXPECTED_DEMO_RESULTS.md`,
  `scripts/reset_demo.py`.
- **Acceptance:** a judge follows the runbook start→finish with no dead ends; reset
  restores the initial state; every expected result matches.
- **Depends on:** all.

---

## Future production tasks (do not start)

- Authorised portal/DigiLocker integrations; real source verification.
- Postgres + pgvector, Celery/Redis, S3, Alembic migrations.
- Full RBAC/SSO, rate limiting, encryption at rest, retention policy.
- Verified APH appendix document lists and addendum-aware rule corpus.
- Legal/compliance review of anomaly wording and human-in-the-loop policy.

## Execution order

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11, with Phase 11 executed continuously from
Phase 3 onward (reset + expected results kept current).

# AICTE Copilot — Implementation Plan

Source of truth: `prd.md` (v1.0), `systemdesign.md` (v1.0), Stitch project `15677314180217415042` (5 exported screens in `apps/web/screens/`).

Scope: PRD §13 **Phase 1 — Core Prototype** (MVP). Phase 2/3 items are out of scope unless trivially included.

## Architecture Summary

Modular monolith per systemdesign §3/§15, adapted for a local-first MVP:

- **apps/api** — FastAPI + SQLAlchemy 2 + Pydantic. One deployable API process; background document processing via FastAPI BackgroundTasks (design ADR-005 async pipeline; worker pool deferred).
- **apps/web** — The five Stitch-exported screens (HTML + Tailwind CDN + Material Symbols), wired to the API with vanilla JS (`app.js`). Multi-page app served statically by FastAPI at `/` (same origin — no CORS in dev).
- **DB** — SQLite by default (`DATABASE_URL=sqlite:///./data/aicte.db`); PostgreSQL-compatible via URL switch. Schema per systemdesign §7.1.
- **LLM** — Provider abstraction (`core/llm.py`). If `LLM_BASE_URL`/`LLM_API_KEY`/LLM_MODEL env configured → OpenAI-compatible tool-calling agent loop. Otherwise a **deterministic fallback router** (intent rules → typed tools → templated grounded responses). Satisfies design §11 graceful degradation and keeps the E2E demo reproducible without a provider.
- **Validation** — Deterministic rules engine (design ADR-004): rules as structured DB records (versioned), evaluators as typed Python functions. LLM never decides compliance.

### Deviations from system design (documented, with upgrade path)

| Deviation | Justification | Upgrade path |
|---|---|---|
| SQLite default instead of PostgreSQL | No guaranteed local Postgres; SQLAlchemy keeps DDL portable | Set `DATABASE_URL` to Postgres; add Alembic when schema churns |
| `create_all` + seed script instead of Alembic | Greenfield MVP, single developer | Introduce Alembic at first production migration |
| BackgroundTasks instead of Celery/Dramatiq workers | No Redis/RabbitMQ locally; design says async is the requirement, not the queue tech | Swap enqueue function to Celery; handlers already idempotent |
| Local filesystem object storage instead of S3 | MVP | Swap `core/storage.py` for S3 client |
| Roles/permissions as code constants instead of DB tables | 4 fixed roles in PRD §4 | Migrate to tables when custom roles needed |
| Static Stitch HTML frontend instead of Next.js | PRD §9.6: "Reuse exported screen assets and generated code wherever possible" — exports are plain HTML; re-implimenting in Next would risk fidelity loss | Port components to Next.js when app grows |
| No pgvector/embeddings | Deterministic keyword retrieval sufficient for MVP rule/doc corpus | Add pgvector per design §7.4 |
| PDF export via printable HTML (browser print) | Reportlab/PDF libs add weight; PRD asks "downloadable PDF export" | Add weasyprint/reportlab if strict .pdf needed |

## Modules (apps/api/app/)

| Module | Responsibility |
|---|---|
| `core/config.py` | Env settings |
| `core/db.py` | Engine/session, base |
| `core/security.py` | Password hashing, tokens, current-user dependency, permission gate |
| `core/audit.py` | Append-only audit events |
| `core/llm.py` | LLM provider abstraction + fallback router |
| `core/storage.py` | Object storage (local dir), checksums |
| `models.py` | All ORM tables |
| `modules/identity.py` | Auth endpoints, memberships, permissions |
| `modules/institutions.py` | Institution CRUD |
| `modules/applications.py` | Applications, sections, fields, values, completion |
| `modules/documents.py` | Upload, versions, processing runs, extracted fields, evidence refs |
| `workers/processing.py` | Text extraction (PyMuPDF), classification, field extraction, duplicate detection |
| `modules/regulations.py` | Regulatory sources + rules + versions |
| `modules/validation.py` | Deterministic engine, runs, findings, incremental revalidation |
| `modules/copilot.py` | Conversations, SSE streaming, orchestrator, tool registry + permission gate |
| `modules/reporting.py` | Compliance report generation + HTML export |
| `seed.py` | Demo institution, users, application, rules, sample docs |

## Phases

### Phase 1 — Foundation (config, DB models, auth, seed) ✅
- Tasks: scaffolding; `models.py` all tables; auth (login, bearer tokens, membership scoping, permission gate); role→permission map; seed script; tests.
- Files: `apps/api/**` core + identity + seed; `requirements.txt`; `pytest.ini`.
- Acceptance: login works for 4 roles; cross-institution request → 403; pytest green.

### Phase 2 — Application domain ✅
- Tasks: institution + application CRUD; sections/fields/values with optimistic version; completion %; section endpoints.
- Acceptance: create application, patch field value, completion recalculates; version conflict rejected.

### Phase 3 — Document intelligence ✅
- Tasks: upload (multi-file, checksum dedupe, MIME sniff, quarantine dir), processing run lifecycle (QUEUED→RUNNING→SUCCEEDED/FAILED/NEEDS_REVIEW), PyMuPDF text extraction, keyword classification, regex structured extraction with page + text span, evidence references, status polling endpoint.
- Acceptance: AC-01, AC-02.

### Phase 4 — Regulations + validation engine ✅
- Tasks: regulatory sources + versioned rules seed (APH 2025-26 sample: faculty ratio 1:20, land area norms, NOC expiry, required docs, cross-doc faculty match); deterministic evaluators returning PASS/FAIL/NEEDS_REVIEW/NOT_APPLICABLE; validation runs + findings with rule ref + evidence ref; incremental revalidation on field change (only dependent rules).
- Acceptance: AC-06, AC-07, AC-08 (engine level).

### Phase 5 — Copilot (agentic core) ✅
- Tasks: conversations + messages API; SSE event stream (message.delta, tool.started/completed, application.updated); typed tool registry (10 tools per design §6.1) with JSON schemas, permissions, risk tiers; permission gate enforced server-side (AC-09); orchestrator plan-execute-observe loop w/ max tool calls; LLM provider + deterministic fallback; tool execution audit.
- Tools: get_application_summary, get_application_section, list_documents, extract_document_fields, run_validation, get_findings, compare_application_evidence, propose_field_updates, apply_draft_updates, generate_compliance_report.
- Acceptance: AC-03, AC-04, AC-05, AC-09, AC-10, AC-12 (no submit/approve tool exists at all).

### Phase 6 — Reporting ✅
- Tasks: compliance report from persisted data (not LLM narrative); HTML download; audit view endpoint.
- Acceptance: report contains findings w/ rule refs + evidence links (AC-07, AC-10).

### Phase 7 — Frontend wiring (Stitch fidelity) ✅
- Tasks: `app.js` shared client (auth redirect, API client, SSE consumption); login page (design-system-matched — auth is a PRD requirement not covered by the 5 screens); wire all 5 screens: nav routing, live application panel (Screen 3), document upload + cards (Screen 2), validation findings (Screen 1), analysis view from findings (Screen 4), Ray conversation (Screen 5); confirmation cards for draft updates (PRD §5.6).
- Acceptance: AC-11 (panel reflects persisted state); demo scenario §17 flows end to end in browser.

### Phase 8 — Verification & hardening ✅
- Tasks: full pytest suite; py_compile; ruff; prompt-injection guard test (uploaded doc containing "ignore instructions" must not change tool behavior); Playwright E2E smoke of demo flow; README; docker-compose (postgres profile); final verification report.
- Acceptance: all AC-01..AC-12 verified; verification report all-PASS.

## Key API surface (systemdesign §8.1)

```
POST /api/v1/auth/login
GET  /api/v1/institutions / POST
GET  /api/v1/applications / POST
GET  /api/v1/applications/{id}
GET  /api/v1/applications/{id}/sections
PATCH /api/v1/applications/{id}/fields/{field_id}
POST /api/v1/documents/upload
GET  /api/v1/documents/{id}/status
GET  /api/v1/documents/{id}/fields
POST /api/v1/applications/{id}/validations
GET  /api/v1/validations/{run_id}/findings
GET  /api/v1/findings/{id}
POST /api/v1/copilot/conversations
POST /api/v1/copilot/conversations/{id}/messages   (SSE)
POST /api/v1/copilot/proposals/{id}/apply
GET  /api/v1/applications/{id}/report
GET  /api/v1/applications/{id}/audit
```

## Risks / Blockers

- **No OCR for image-only scans** — PyMuPDF extracts embedded text; scanned images → NEEDS_REVIEW (design-compliant abstention). Tesseract optional upgrade.
- **LLM availability** — fallback router covers the demo; LLM path tested via mocked provider.
- **Sample regulatory rules are illustrative** (real APH corpus is an open decision, systemdesign §19) — seeded rules are explicit and versioned, clearly marked sample.
- **Tailwind CDN** — fine for prototype; compile statically for production.

## Status

Backend phases 1–6 complete (37 tests). Frontend delivered as a Next.js app (see pivot below).

---

## MVP Prototype Pivot (2026-11-01)

Development priority changed: ship a **polished, demonstrable MVP** first. Long-term
production infrastructure is **paused, not removed** — all prior code, plans and
architecture decisions above remain valid and are preserved for resumption.

### In scope now
- Next.js 15 + TypeScript + Tailwind app (`apps/web`) porting the 5 Stitch screens with
  high visual fidelity (Overview, Live Application, Documents, Validation, Analysis).
- FastAPI MVP backend (`apps/api`, SQLite) providing consistent demo data + real API
  contracts: auth, application fields, document upload + extraction, deterministic
  validation, copilot SSE with staged proposals, report/audit.
- Believable end-to-end journey: login → dashboard → copilot → upload → inspect evidence
  → run validation → accept staged change → draft/validation update.

### Paused (preserved for later)
- PostgreSQL + pgvector, Redis + Celery workers, S3 storage, PaddleOCR, LangGraph agent,
  Docker Compose production topology, Alembic, rate limiting, PDF export.
- Code for Celery/S3/pgvector/LangGraph exists in `apps/api` behind config flags and
  defaults (SQLite + local storage + inline processing) so the MVP runs with zero infra.

### Frontend stack (supersedes the "static HTML" deviation)
- `apps/web` = Next.js App Router, TypeScript, Tailwind (Stitch design tokens), Lucide-free
  (Material Symbols font as in the Stitch exports).
- Original Stitch HTML retained as design reference in `design/stitch/`.
- Next dev/start runs on **port 3100** (port 3000 is used by an unrelated local project).
- `/api/*` is proxied to the FastAPI backend via `next.config.mjs` rewrites (no CORS).

### Demo data
- Institution: Northstar Institute of Technology (`NIT-DEL`), application
  `NIT-DEL-2026-0142` (Extension of Approval, 2026-27).
- 6 indexed documents (land deed, faculty statement, fire NOC, audited accounts,
  building stability, unclassified scan) with extracted evidence.
- 12 seeded rules → mixed PASS/FAIL/NOT_APPLICABLE findings (faculty 48/51, expired fire
  NOC, missing address/building-stability).
- Demo accounts: `admin@`, `preparer@`, `compliance@northstar.edu.in`,
  `reviewer@aicte.gov.in` — password `demo1234`.

---

## Unified Agentic Workspace (2026-11-01)

Interaction model (inspired by Razorpay Ray, not copied): **one assistant, one
conversation, one application context, multiple capabilities.**

### Frontend structure
- `/copilot` — the only conversational surface. Landing state (welcome, active
  application metrics, suggested tasks), persisted conversation history, structured
  result cards (findings, documents, application summary, compliance report, extracted
  fields, staged proposals), file upload, single composer pinned below a scrollable
  transcript.
- Workspaces (no chat inputs): `/` Overview command centre + proactive insights,
  `/application` autosave editor + new draft, `/documents` library + evidence inspector,
  `/validation` findings + explain/compare actions, `/analysis` distribution and
  consistency insights.
- Global "Ask Copilot" in the header; contextual `AskCopilot` buttons pass structured
  context `{kind, id, label, data}` to the same conversation (never hidden instructions).

### Backend
- `modules/agent.py` — LangGraph `StateGraph` (agent ↔ tools loop) with
  `ChatOpenAI` bound to the OpenAI-compatible Groq endpoint; model
  `openai/gpt-oss-20b` by default. Tool registry, permission gate and audit are reused
  from `modules/copilot.py`. Falls back to the deterministic router when no key is set.
- `GET /api/v1/copilot/conversations/active?application_id=` returns (or creates) the
  single conversation per user+application; messages are persisted, so navigating
  between workspaces keeps the conversation.
- `POST .../messages` accepts `{content, context}`; SSE events: `conversation`,
  `tool.started`, `tool.completed` (with structured `result`), `proposal.staged`,
  `message.delta`, `message.complete`, `application.updated`.
- OCR: `workers/processing.py` uses RapidOCR (ONNX) for images and text-less PDFs,
  PyMuPDF for text layers, then keyword classification + regex extraction.
- Reporting split: `GET .../report` (view, `application.read`) and
  `GET .../report/export` (`report.export`). Preparers can export; reviewers view only.

### Enabling the LLM (free)
Set `LLM_API_KEY` in `apps/api/.env` (Groq free key). `LLM_BASE_URL` and
`LLM_MODEL=openai/gpt-oss-20b` are preconfigured. Without a key the product still works
end-to-end via the deterministic router.

## Implementation status (2026-11-02)

- Phases 1-11: implemented and verified.
- Backend: 51 tests passing; E2E script scripts/e2e_demo.py prints E2E DEMO: PASS.
- Frontend: production build passes with 11 routes (Copilot, Overview, Applications, Documents, Validation, Analysis, EVC, Review, Login).
- Demo tenant: Aarohan Institute of Technology (DEMO_MODE=aarohan), reset via scripts/reset_demo.py.
- Live LangGraph agent: openai/gpt-oss-20b via Groq (key in apps/api/.env); deterministic fallback when unset.
- Simulated verification and institutional records are clearly labelled; no live government connection.

Future production tasks remain as listed under 'Future production tasks (do not start)'.

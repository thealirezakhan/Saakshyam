# AICTE Official Process Research

Research date: 2026-11-01. Primary sources are AICTE's own website/PDFs. Where the
official position is unclear (scanned calendars, category-specific annexures), this
document says so rather than guessing.

## 1. Method and scope

- Read the AICTE homepage "Approval Process 2026-2027" section (effective 28 Nov 2025)
  and its linked public notice, addendum, handbook, FAQ, support portal and calendar.
- Read Chapter I (process/committees) and Chapter II (existing-institution EoA
  categories) of the Approval Process Handbook (APH) text as published/summarised on
  official or government-mirrored URLs.
- Cross-checked against the 2026-27 corrigendum/addendum notice.
- Scope: what a decision-support system may reasonably do, and what must be simulated.

> The APH available at `/sites/default/files/approval/APH Final.pdf` (and the
> `/sites/default/files/APH%20Final.pdf` variant referenced in the brief) is marked
> **2024-25 to 2026-27**. The homepage separately publishes a 2026-27 public notice,
> a corrigendum/addendum and a revised academic calendar. Treat the latest notice as
> authoritative when it differs.

## 2. Official sources

| # | Source | URL | Section / clause | What it establishes | Implied AICTE Copilot feature | Access | Uncertainty |
|---|--------|-----|------------------|--------------------|-------------------------------|--------|-------------|
| S1 | AICTE — Approval Process 2026-2027 | https://aicte.gov.in/ | "Approval Process 2026-2027 (w.e.f 28 Nov 2025)" | Current process hub; links to public notice, addendum, APH, FAQs, CSS, unapproved-institution report, revised academic calendar | A "regulatory sources" registry browsable in-app; academic-year selector | Public | Page is current as fetched; verify annually |
| S2 | Public Notice for Approval Process 2026-27 | https://aicte.gov.in/sites/default/files/Public%20notice%20for%20approval%20process%202026-27.pdf | Public notice | Notifies application window, categories, cut-off dates and processing schedule | Deadline/calendar model; per-category windows | Public (scanned PDF) | Text is an image scan; exact dates must be read from the PDF before implementation |
| S3 | Corrigendum / Addendum 2026-27 (V2) | https://aicte.gov.in/downloads/aph/Final%20Addendum%202026-27_V2.pdf | Addendum | Amendments to the APH (e.g., application-category/processing tables) | Rule versioning: academic year + addendum version; "needs confirmation" flag | Public | Must be read clause-by-clause; not all changes captured here |
| S4 | Approval Process Handbook (APH) | https://www.aicte.gov.in/sites/default/files/approval/APH%20Final.pdf | Chapter I (1.8–1.12), Chapter II (2.1–2.7) | Scrutiny/Re-Scrutiny, EVC, SHC/SAC definitions, appeals, EoA categories, self-disclosure, increase in intake | Category workflow config; rule sources; scrutiny-stage model | Public | 2024-25 to 2026-27 edition; addendum may supersede specific clauses |
| S5 | APH — Scrutiny/Re-Scrutiny and EVC process | Government-mirrored APH text (e.g. https://cdnbbsr.s3waas.gov.in/.../2025031399.pdf) | 1.12 / 1.12.1 | Scrutiny committee verifies documents; deficiencies communicated via web portal; in-order cases proceed to EVC; EVC verifies infrastructure/faculty | Deficiency lifecycle; evidence checklist; EVC recommendation workflow | Public | Mirrored copies; confirm against S4 |
| S6 | APH — committees and appeals | APH text (S4/S5) | Definitions; 1.11 Appeal Procedure | SHC reviews EVC reports / replies to show-cause; SAC hears one appeal within 7 days of LoD/LoR; Council decision final | Reviewer/committee workspace; appeal timeline; "human decision only" | Public | Committee composition in appendices not reproduced here |
| S7 | AICTE approved institutions directory | https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved | Directory | Public list of approved institutions | Institutional identity/reference lookup (read-only, simulated in MVP) | Public | No documented public API; scraping is not an authorised integration |
| S8 | AICTE faculty dashboard | https://facilities.aicte-india.org/dashboard/pages/faculties.php | Faculty | Public aggregate faculty information | Faculty reference comparison (simulated) | Public | Aggregate, not a per-institution verification API |
| S9 | Closed courses / closed institutes | https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/closedcourse ; `#!/closedinstitute` | Directories | Public closure status | History/closure checks (simulated) | Public | Same caveat as S7 |
| S10 | Unapproved institution report | https://facilities.aicte-india.org/report/ | Report | Public unapproved-institution lookup | Institution status check (simulated) | Public | Not an API |
| S11 | FAQs | https://aicte.gov.in/sites/default/files/FAQ%20Updated.pdf | FAQ | Clarifications on process/queries | Copilot "how does this work" answers with citations | Public | FAQ may lag the addendum |
| S12 | Centralized Support System (CSS) | https://css.aicte.gov.in | Support portal | Query/grievance support channel | Link-out only; do not simulate as a verification source | Public portal (login for queries) | No public API documented |
| S13 | Revised Academic Calendar 2026-27 | https://aicte.gov.in/sites/default/files/Revised%20Academic%20Calendar%202026-27.pdf | Calendar | Processing/decision deadlines | Deadline model and overdue flags | Public (scanned PDF) | Dates must be transcribed from the PDF; not extracted here |
| S14 | Web Portal (institutional login) | https://portal.aicte.gov.in/ | Portal | Where institutions submit applications, documents, payments and compliance | Requires authorised integration; otherwise simulate | Authenticated | Private data; no public API documented |

## 3. Findings by research question

### 3.1 What application types can an institution submit?
Chapter II lists the EoA categories for existing institutions (S4):
1. EoA based on Self-Disclosure
2. Increase in Intake / Additional Course(s)
3. Start a New Programme / Level in existing institution
4. Introduction/continuation of NRI seats
5. Introduction/continuation of supernumerary seats (FN/OCI/CIWG)
6. Introduction of Integrated/Dual Degree course
7. Introduction/continuation of Fellow Programme in Management
8. Merger of institutions under the same Trust/Society/Company
9. Conversion Diploma ↔ Degree level
10. Conversion Women's ↔ Co-ed institution
11. EoA after a break / Restoration of Intake
12. Change of Site / Location
13. Change of course name / merger / reduction in intake / closure of programme
14. Change in institution name / affiliating university / type
15. Change in Trust/Society/Company name or address
16. Closure of institution

The MVP models the 8 representative categories requested in the brief; the remaining
categories are configuration entries in a future phase.

### 3.2 EoA self-disclosure vs other changes
- Self-disclosure EoA is granted on the institution's online self-disclosure of
  facilities/infrastructure, with documents per Appendix 17.1 (S4). It is not routed
  through Scrutiny/EVC by default.
- Other categories are processed through Scrutiny/Re-Scrutiny and EVC **as applicable**
  (S4/S5). The APH explicitly states Scrutiny and EVC for any increase in intake or new
  course (S4, 2.6(i)). Not every category goes through every committee.
- Implication: the product must select the checklist and stage path by category, not
  apply one generic validation.

### 3.3 Which categories require scrutiny/re-scrutiny?
All categories other than self-disclosure EoA are processed by Scrutiny, with
Re-Scrutiny available for communicated deficiencies or absence (S5). The exact mapping
is in the APH processing tables and the 2026-27 addendum; the MVP encodes a conservative
default and marks it configurable. **Uncertainty:** the processing table is amended by
the addendum; confirm per category before production.

### 3.4 Which categories may require an EVC?
EVC verifies infrastructure/faculty physically or online (S5, 1.12.1). It follows a
Scrutiny/Re-Scrutiny that finds the application in order, and may also be required for
increase in intake/new courses (S4, 2.6(i)). The MVP treats "EVC recommended" as a
human recommendation, never as a completed inspection.

### 3.5 What happens when deficiencies are identified?
Deficiencies are communicated to the applicant through the AICTE web portal. The
applicant may be eligible for Re-Scrutiny, which verifies **only** the deficiencies
pointed out by the Scrutiny committee (S5, 1.12 f–h).

### 3.6 How does an institution submit compliance/rectification?
Through the portal, with attested documents; offline applications are not valid
(S5/S14). The MVP simulates upload + clarification + revalidation, preserving history.
**Requires authorised integration** for the real portal.

### 3.7 Standing Hearing Committee (SHC)
Constituted by the Chairman to review EVC reports and replies to show-cause notices
(S6). Implication: a reviewer workspace stage that records observations and whether
the case is recommended for further review.

### 3.8 Standing Appellate Committee (SAC)
Hears an institution's appeal once, within 7 days of the Letter of Deficiency/Rejection;
may recommend/not recommend or refer back to scrutiny/EVC; the Council's decision is
final (S6, 1.11). Implication: appeal timeline and "human decision" gates; the AI never
decides.

### 3.9 Institutional information relevant to scrutiny
Identity/trust details; approved programmes and intake; faculty and cadre; land,
built-up area and infrastructure; statutory NOCs (fire, occupancy, building stability);
financial/audit records; previous approvals, deficiencies and compliance; affiliation.
These map to the application sections, document classes and historical records.

### 3.10 Publicly accessible reference resources
Approved-institution directory, faculty dashboard, closed-course/institute and
unapproved lists, public notices, APH, FAQs, calendar (S7–S11, S13). These are public
web pages, not documented APIs. The MVP uses **simulated reference snapshots**, clearly
labelled, not live scraping.

### 3.11 Information requiring authenticated access
Application data, uploaded originals, payment/TER records, internal scrutiny/EVC
reports, show-cause replies and source verification (S14). **Not available publicly.**
The MVP simulates these through a "mock institutional record" and "mock verification
adapter"; real use needs an authorised integration.

### 3.12 Deadlines and calendar
The public notice and revised academic calendar define windows and decision dates
(S2/S13). Appeals are within 7 days (S6). **Uncertainty:** both PDFs are image scans; the
exact 2026-27 dates must be transcribed before hard-coding. The prototype uses clearly
labelled illustrative dates in the demo dataset.

### 3.13 Documents and evidence by category
The APH references appendices (e.g., Appendix 16/17.1/17.3) for document sets, but the
appendix contents are not reproduced in the text used here. The MVP therefore ships a
**synthetic, illustrative checklist per category**, explicitly marked prototype-only,
to be replaced by the verified appendix list.

### 3.14 Safeguards for AI-identified anomalies
- An anomaly is a **signal for human review**, never proof of forgery or misconduct.
- Every finding shows source document, page/span, extracted value, comparison value,
  rule and academic year.
- The AI cannot approve, reject, penalise, or alter statutory outcomes.
- A human reviewer must confirm before any adverse action.
- Mock verification must display "SIMULATED — no live authority connection".

## 4. What must be simulated (and labelled)

| Capability | Real status | MVP approach |
|---|---|---|
| Portal application submission/payments | Authenticated portal (S14) | In-app synthetic application + payment receipt |
| Issuing-authority verification | No public API documented | Deterministic mock adapter, labelled simulated |
| Scrutiny/EVC/SHC/SAC records | Internal/committee | Synthetic notes and stage records, labelled |
| Approved-institution/faculty lookup | Public web pages (S7/S8) | Static reference snapshots in demo data |
| Academic calendar dates | Public scanned PDF (S13) | Illustrative dates marked synthetic |

## 5. Explicit non-claims

- No undocumented AICTE API is used or assumed.
- No live government/issuing-authority verification is performed.
- No prototype-only rule is presented as official regulation.
- No automated approval, rejection or adverse regulatory decision is made.

## 6. Open questions to confirm before production

1. Exact 2026-27 processing table per category after the addendum (S3).
2. Appendix 16/17.x document lists per category.
3. Which categories mandate EVC vs "as applicable".
4. Current academic-calendar dates and their effect on late submission.
5. Whether any authorised verification integration (e.g., DigiLocker) is sanctioned.

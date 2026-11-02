# Judge Demonstration Runbook

> **Status:** implemented and end-to-end verified (Phases 2–11). Run
> `python scripts/e2e_demo.py` to see `E2E DEMO: PASS`. If a label differs slightly,
> trust the button text shown in the app.

## 0. The story in one line

Aarohan Institute of Technology applies to increase intake. AICTE Copilot checks the
application against its own declaration, uploaded evidence and institutional history,
flags inconsistencies for human review, simulates source verification, supports
rectification, and prepares an evidence-linked scrutiny pack. It never approves or
rejects.

## A. Start the application

Requirements: Python 3.11+, Node 24.

```powershell
# Terminal 1 — backend
cd apps/api
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd apps/web
npm install
npm run dev
```

Optional LLM (free): set `LLM_API_KEY` in `apps/api/.env` (Groq, model
`openai/gpt-oss-20b`). Without it the Copilot uses deterministic responses — the demo
still works.

Reset to the initial demo state before every presentation:

```powershell
python scripts/reset_demo.py
```

Automated end-to-end verification (in-memory; no server needed):

```powershell
python scripts/e2e_demo.py
# expected final line: E2E DEMO: PASS
```

Open `http://localhost:3100/login`.

| Role | Email | Password |
|---|---|---|
| Institution Administrator | `inst.admin@aarohan.demo` | `demo1234` |
| AICTE Scrutiny Reviewer | `scrutiny@aicte.demo` | `demo1234` |
| EVC Reviewer | `evc@aicte.demo` | `demo1234` |
| System Administrator | `sysadmin@aicte.demo` | `demo1234` |

Expected landing page: **Your AICTE Copilot** with the active application
`DEMO-EVENT-2026-001` (Aarohan Institute of Technology, Increase in Intake, AY 2026-27).

## B. Institution workflow (click-by-click)

1. Log in as `inst.admin@aarohan.demo`.
2. Open **Overview**. Expect: institution Aarohan Institute of Technology; one active
   application; completion %, open findings, documents indexed.
3. Click **Applications** → open `DEMO-EVENT-2026-001`.
4. Review application details. Expect sections: Institution Profile, Programme Details,
   Faculty Cadre, Land & Infrastructure, Statutory Approvals, Finance. Note the category
   badge **Increase in Intake** and the workflow stage strip.
5. Open the **Document checklist** panel on the application page (or Documents workspace).
   Expect required documents with states: uploaded / missing / expired / unverified.
6. Click **Upload document** and upload these files from `demo-data/documents/` in order:
   1. `01_Previous_EOA_Letter_2025-26.pdf`
   2. `02_Application_Form_AY2026-27.pdf`
   3. `03_Faculty_Information_Declaration.pdf`
   4. `04_Faculty_Appointment_Qualification_Summary.pdf`
   5. `05_Trust_Registration_Certificate.pdf`
   6. `06_Affidavit_Increase_Intake.pdf`
   7. `07_Payment_Receipt_TER_2026.pdf`
   8. `08_Institutional_Compliance_Declaration.pdf`
   9. `09_Building_Occupancy_Certificate.pdf`
   10. `10_Fire_Safety_Certificate.pdf`
   11. `11_Building_Floor_Plan.pdf`
   12. `12_Laboratory_Photograph_CSE.png`
   13. `13_Library_Equipment_Evidence.png`
   14. `14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf`
   15. `15_Compliance_Response_2025-26.pdf`
   16. `16_Fire_Safety_Certificate_Altered.png`
   Expect each to show Processing → Extracted/Needs review.
7. Click **Run validation** (Validation workspace). Wait for completion.
8. Expect findings (see `EXPECTED_DEMO_RESULTS.md`), including:
   - Faculty inconsistency (48 declared / 45 list / 42 institutional record)
   - Fire NOC expired (old NOC valid till 2025-12-31; application claims 2027-03-31)
   - Duplicate/reused laboratory & library image
   - Inconsistent reference number (EoA 0142 vs scrutiny 0143)
   - Institution name/city inconsistency (affidavit says Nagpur)
   - Trust certificate verification pending
9. Click a finding → inspect evidence. Expect document name, page, text span, extracted
   value, comparison value.
10. Click **Explain with Copilot**. Expect a grounded explanation naming the three values
    and the rule; it must not say "fraud".
11. Return to Documents → **Upload a corrected document**:
    `corrected/17_Faculty_Appointment_Summary_CORRECTED.pdf`.
12. Add a clarification (finding detail → **Add clarification**) referencing the
    corrected faculty summary.
13. Click **Revalidate** (or **Submit for revalidation**).
14. Expect the faculty findings to become **Resolved**; the fire NOC finding remains
    open unless `corrected/18_Fire_Safety_Certificate_RENEWED.pdf` is also uploaded.
15. Open **Audit history** (finding or application). Expect the earlier finding and the
    correction event to remain visible — nothing is erased.

## C. Source verification workflow

1. Open **Documents** → select `10_Fire_Safety_Certificate.pdf`.
2. Click **Verify with issuing authority (simulated)**.
3. Expect the banner:
   `SIMULATED VERIFICATION — NO LIVE GOVERNMENT OR ISSUING-AUTHORITY CONNECTION`.
4. Inspect the result card: request ID, document type, simulated source, reference number,
   submitted value, returned value, result, timestamp, explanation, manual-review flag.
5. Demonstrated outcomes (select the matching document):
   - Verified → `01_Previous_EOA_Letter_2025-26.pdf`
   - Mismatch → `03_Faculty_Information_Declaration.pdf`
   - Expired → `10_Fire_Safety_Certificate.pdf`
   - Pending → `05_Trust_Registration_Certificate.pdf`
   - Source unavailable → `09_Building_Occupancy_Certificate.pdf`
   - Manual review → `08_Institutional_Compliance_Declaration.pdf`

## D. Infrastructure / EVC workflow

1. Open **Applications** → **Land & Infrastructure** (or the Infrastructure workspace).
2. Review evidence: building photo, lab photo, library photo, floor plan, equipment list.
3. Click **Analyze infrastructure evidence (simulated)**.
4. Expect: evidence inventory, duplicate flag (12 and 13 are the same image), missing
   library photograph/equipment list gap, declared-vs-evidence summary.
5. Click **Recommend / record visit** (sign in as `scrutiny@aicte.demo` or `evc@aicte.demo`;
   the institution role cannot recommend EVC). Expect stage `evc_recommended` (a
   recommendation, not a completed visit).
6. Open **EVC** in the navigation. Record an observation and click **Add note**.
   Expect stage `evc_notes_recorded` and the note in the timeline.
7. Expect the application stage to show **EVC notes recorded — human review pending**.

## E. Scrutiny reviewer workflow

1. Sign out, log in as `scrutiny@aicte.demo`.
2. Open **Review** in the navigation → select `DEMO-EVENT-2026-001`.
3. Inspect findings and evidence (read-only source documents).
4. Review the institution's correction and clarification.
5. Add an observation (e.g., "Faculty declaration reconciled after correction; verify
   renewed Fire NOC").
6. Mark the fire NOC finding **Requires manual verification**.
7. Request additional evidence (renewed Fire NOC) — creates a task for the institution.
8. Recommend further scrutiny / EVC as appropriate.
9. Confirm the UI never offers an "Approve" or "Reject" action.

## F. Copilot conversation script

Type these in `/copilot` (same conversation; context follows the active application):

| # | User message | Expected copilot behaviour |
|---|---|---|
| A | "I want to apply for an increase in intake for the upcoming academic year." | Identifies institution and AY, asks for programme/proposed intake, shows the Increase-in-Intake workflow |
| B | "What documents do I need for this application?" | Lists the category checklist with uploaded/missing/expired states |
| C | "Check this entire application and tell me what is wrong." | Runs validation, returns evidence-linked findings with severity |
| D | "Why are you flagging the faculty information?" | Shows declared 48 / list 45 / record 42 and explains the inconsistency |
| E | "Verify this certificate." | Runs simulated verification and shows source, timestamp, result, SIMULATED banner |
| F | "I have uploaded the corrected document. Check it again." | Revalidates affected rules and updates the finding, retaining history |
| G | "Prepare a scrutiny summary for this application." | Produces resolved/unresolved/pending-verification/human-review summary |
| H | "Check whether the infrastructure evidence is sufficient." | Summarises evidence, gaps, duplicate image, and whether EVC may be needed |
| I | "Why does this application need further scrutiny?" | Explains the configured workflow stage, rule source, AY and clause |

## G. Final result / report

Open **Reports** (or `Export annexure`). The validation report includes:

- Application summary (institution, application, category, AY, status).
- Document checklist with states.
- Findings with severity, rule, evidence, comparison values, status.
- Verification statuses (with SIMULATED label).
- Compliance/infrastructure observations.
- Rectification history (before/after).
- Pending human-review items.
- Audit history.

## H. Reset for the next presentation

```powershell
python scripts/reset_demo.py
```

Then sign in again as `inst.admin@aarohan.demo`. The dataset returns to the documented
initial state (findings open, verifications pending/expired as designed, no corrections
applied).

## I. What to say (and not say)

- Say: "Copilot flags a potential inconsistency for human review."
- Do not say: "Copilot detected fraud/forgery."
- Say: "Simulated verification for demonstration."
- Do not say: "Verified with the government."
- Say: "Recommendation for EVC."
- Do not say: "EVC approved."
- Say: "Human reviewer decides."
- Do not say: "System approved/rejected the application."

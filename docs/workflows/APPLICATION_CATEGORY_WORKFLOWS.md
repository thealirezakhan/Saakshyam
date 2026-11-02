# Application Category Workflows

The product must not run one generic validation for every application. Each category
selects: required information, document checklist, applicable rules, processing stages,
whether an EVC may be recommended, and the expected outputs.

> All stages and document lists below are **prototype configuration**. They encode the
> official distinctions where verified (see research doc) and are explicitly marked
> where the APH appendix/addendum must be confirmed. The config lives in
> `apps/api/app/workflows/categories.py`; the chat layer never hardcodes rules.

## Stage model (not interchangeable)

| Stage key | Meaning | AI role |
|---|---|---|
| `initial_validation` | Automated checks on submitted data/documents | Run deterministic checks, produce evidence-linked findings |
| `institution_response` | Deficiencies communicated; institution clarifies/corrects | Explain findings, accept corrections, trigger revalidation |
| `re_scrutiny` | Re-checks **only** previously flagged deficiencies | Re-run affected rules; retain history |
| `scrutiny_committee` | Human committee review | Prepare evidence pack and summary; no decision |
| `evc` | Expert Visit Committee (infrastructure/faculty) | Recommend, plan, collect evidence, record observations |
| `standing_hearing` | Reviews EVC reports / show-cause replies | Organise records for human reviewers |
| `standing_appellate` | Appeal (one, within 7 days of LoD/LoR) | Present timeline and evidence; no decision |
| `competent_authority` | Final statutory decision | Never automated |

Rules:
- Only activate stages configured for the category.
- "EVC recommended" is a recommendation, not a completed inspection.
- AI never marks an official outcome; every decision is human-authored.

## Categories

### 1. Extension of Approval based on Self-Disclosure (`eoa_self_disclosure`)
- **Purpose:** Annual continuation by self-disclosure of facilities/infrastructure.
- **Required info:** Institution identity/trust, programmes, intake, faculty, land,
  built-up area, statutory NOCs.
- **Checklist:** institution profile, faculty cadre, land/building, fire/occupancy, trust
  registration, prior EoA, self-disclosure declaration (Appendix 17.1 — *confirm*).
- **Historical records:** prior EoA letter, approved programmes/intake, last observations.
- **Rules:** identity match, required fields, faculty ratio, land/built-up minimum,
  NOC validity, evidence consistency.
- **Validation steps:** completeness → document presence → rule checks → cross-document
  consistency → summary.
- **Stages:** `initial_validation`, `institution_response`; **no Scrutiny/EVC by default**.
- **EVC:** not required by default (self-disclosure path).
- **Outputs:** completeness report, open findings, self-disclosure evidence pack.
- **Deficiency types:** missing field, expired NOC, unverifiable claim, inconsistency.
- **Rectification:** upload corrected document → revalidate → history retained.
- **Human review:** required for any unresolved high-severity finding.

### 2. Increase in Intake / Additional Course (`increase_intake`)
- **Purpose:** Increase sanctioned intake or add a course in an existing programme.
- **Required info:** existing approved intake, proposed intake, programme, faculty,
  infrastructure (labs, classrooms, library), financials.
- **Checklist:** application form, faculty list/declaration, land/building, fire/occupancy,
  building plan, lab/library evidence, payment receipt, affidavit, prior EoA.
- **Historical records:** prior approved intake and programmes, previous scrutiny
  observations, prior compliance responses.
- **Rules:** intake vs infrastructure capacity, faculty ratio for proposed intake, NOC
  validity, declared-vs-evidence faculty/land, duplicate evidence, reference continuity.
- **Validation steps:** category detection → historical baseline → document extraction →
  capacity/ratio checks → cross-source comparison → anomaly screen → EVC recommendation.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny` (if deficiencies), `evc` (required per APH for intake increases —
  *confirm addendum*), `standing_hearing` (if EVC report requires), `competent_authority`.
- **EVC:** **may be required**; recommend through human confirmation.
- **Outputs:** deficiency list, evidence comparison, EVC recommendation, scrutiny summary.
- **Deficiency types:** faculty shortfall/inconsistency, capacity shortfall, expired NOC,
  missing lab evidence, duplicate photograph, reference mismatch.
- **Rectification:** corrected faculty statement/certificate → revalidate → EVC packet.
- **Human review:** mandatory before EVC and before any adverse note.

### 3. Start New Programme / Level (`new_programme`)
- **Required info:** proposed programme/level, curriculum, faculty, labs, library,
  affiliation, financial viability.
- **Checklist:** application, programme details, faculty, infrastructure, lab equipment,
  library, affiliation, trust docs, affidavits.
- **Historical records:** existing programmes, available faculty, infrastructure baseline.
- **Rules:** faculty sufficiency, lab/equipment norms, library norms, affiliation validity.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny`, `evc`, `competent_authority`.
- **EVC:** may be required.
- **Outputs:** readiness report, gap list, EVC recommendation.

### 4. Change of Site / Location (`change_of_site`)
- **Required info:** old/new site, land ownership/lease, built-up area, NOCs, building
  plan, affiliation/state NOC.
- **Checklist:** land deed/lease, building plan/occupancy, fire NOC, state/affiliation
  NOCs, site photographs, prior approvals.
- **Historical records:** old site approval, relocation notices, compliance history.
- **Rules:** land area/ownership, lease duration vs course duration, NOC validity,
  address consistency across documents.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny`, `evc` (site verification), `competent_authority`.
- **EVC:** likely required for site verification (*confirm*).
- **Outputs:** site evidence pack, address-consistency findings, EVC checklist.

### 5. Restoration of Intake / After Break in EoA (`restoration`)
- **Required info:** last approved year/intake, reason for break, current readiness,
  compliance with prior conditions.
- **Checklist:** prior EoA, closure/break records, current faculty/infrastructure,
  NOCs, compliance response.
- **Historical records:** last approval, break period, prior deficiencies.
- **Rules:** continuity of approvals, readiness vs last approved intake, NOC validity.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny`, `evc` (may be recommended), `competent_authority`.
- **Outputs:** restoration readiness, historical comparison, evidence requests.

### 6. Merger of Institutions (`merger`)
- **Required info:** merging entities, trust/society, campuses, programmes, faculty,
  land, financials.
- **Checklist:** trust docs, approvals of both entities, land/building, faculty,
  programme mapping, NOCs, amalgamation resolution.
- **Historical records:** both institutions' approvals and observations.
- **Rules:** same trust check, campus/city rule, programme continuity, faculty/land
  adequacy post-merger.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny`, `evc`, `competent_authority`.
- **EVC:** may be required.

### 7. Closure of Institution / Programme (`closure`)
- **Required info:** programmes to close, student redistribution, faculty settlement,
  no-dues, state/university NOC.
- **Checklist:** closure application, student-redistribution plan, university/state NOC,
  faculty/student records, affidavits.
- **Historical records:** approvals, enrolled students, prior closure notices.
- **Rules:** student protection plan present, NOC validity, programme mapping.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `competent_authority`; EVC not typical for closure (*confirm*).
- **Outputs:** closure checklist, student-protection findings.

### 8. Change in Institution / Affiliating University Details (`identity_change`)
- **Required info:** old/new name, university/board, type, trust name/address, evidence.
- **Checklist:** trust resolution, gazette/registration proof, affiliation letter,
  updated certificates, prior approvals.
- **Historical records:** prior names, affiliation history.
- **Rules:** name consistency across documents, affiliation validity, trust identity.
- **Stages:** `initial_validation`, `institution_response`, `scrutiny_committee`,
  `re_scrutiny`, `competent_authority`; EVC usually not required.
- **Outputs:** identity-consistency findings, updated record.

## Category summary

| Category | Scrutiny | Re-Scrutiny | EVC | Typical deficiencies |
|---|---|---|---|---|
| eoa_self_disclosure | No (default) | Only if flagged | No | missing/expired evidence |
| increase_intake | Yes | Yes | Yes (confirm) | faculty/capacity/NOC/anomaly |
| new_programme | Yes | Yes | May be | faculty/lab/library |
| change_of_site | Yes | Yes | Likely | land/lease/address/NOC |
| restoration | Yes | Yes | May be | continuity/readiness |
| merger | Yes | Yes | May be | trust/programme/land |
| closure | Yes | Yes | No (typical) | student protection/NOC |
| identity_change | Yes | Yes | No | name/affiliation consistency |

All rows are **prototype configuration** and flagged where the addendum must be checked.

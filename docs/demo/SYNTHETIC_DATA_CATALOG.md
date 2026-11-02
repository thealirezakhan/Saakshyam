# Synthetic Data Catalog

All files are fictional. Every document carries the watermark
`SYNTHETIC DEMO DATA — NOT AN OFFICIAL AICTE DOCUMENT`.

## Tenant

| Field | Value |
|---|---|
| Institution | Aarohan Institute of Technology (AIT) |
| Institution ID | DEMO-AICTE-0001 |
| Location | Pune, Maharashtra |
| Trust | Aarohan Education Society |
| Application | DEMO-EVENT-2026-001 |
| Academic year | 2026–27 |
| Category | Increase in Intake / Additional Course |
| Existing approved intake | 240 (CSE 120, ECE 60, Mechanical 60) |
| Proposed intake | 330 (CSE 180, ECE 90, Mechanical 60) |

## Primary documents (`demo-data/documents/`)

| # | File | Purpose | Status | Expected extraction | Detects | Expected finding | Demo step |
|---|---|---|---|---|---|---|---|
| 01 | `01_Previous_EOA_Letter_2025-26.pdf` | Prior approval | Valid | EoA no. `DEMO/EOA/2025-26/0142`, AY 2025-26, approved intake 240 | reference baseline | none (VERIFIED on request) | B6, C |
| 02 | `02_Application_Form_AY2026-27.pdf` | Current application | Valid | Application `DEMO-EVENT-2026-001`, proposed intake 330, category | completeness | none | B6 |
| 03 | `03_Faculty_Information_Declaration.pdf` | Declared faculty | Intentionally inconsistent | total 48, PhD 30 | DEMO-FAC-001 | Faculty count inconsistency | B8, D |
| 04 | `04_Faculty_Appointment_Qualification_Summary.pdf` | Actual faculty list | Intentionally inconsistent | total 45, PhD 27 | DEMO-FAC-001/002 | Faculty count inconsistency | B8, D |
| 05 | `05_Trust_Registration_Certificate.pdf` | Trust registration | Valid, verification pending | reg no. `MAH/1234/2008`, dated 2008-06-14 | DEMO-VER-001 | Verification pending | B6, C |
| 06 | `06_Affidavit_Increase_Intake.pdf` | Affidavit | Intentionally inconsistent (city) | deponent, date 2026-01-10, city "Nagpur" | DEMO-ID-001 | Institution detail inconsistency | B8 |
| 07 | `07_Payment_Receipt_TER_2026.pdf` | TER payment | Valid | receipt `TER/2026/000981`, ₹3,50,000, 2026-01-12 | completeness | none | B6 |
| 08 | `08_Institutional_Compliance_Declaration.pdf` | Compliance declaration | Missing field (signature) | declaration text, no signature | checklist | Incomplete document | B6, C |
| 09 | `09_Building_Occupancy_Certificate.pdf` | Occupancy | Valid | cert `OC/PUN/2024/7781`, valid until 2029-03-31 | completeness | none | B6 |
| 10 | `10_Fire_Safety_Certificate.pdf` | Fire NOC | Expired | valid till 2025-12-31 | DEMO-NOC-001 | Fire NOC expired | B8, C, D |
| 11 | `11_Building_Floor_Plan.pdf` | Floor plan | Valid | built-up 14,280 sqm, 4 floors | DEMO-INF-001 | none (evidence present) | D |
| 12 | `12_Laboratory_Photograph_CSE.png` | Lab photo | Duplicated | image label "CSE Laboratory" | DEMO-DOC-001 | Duplicate/reused image | B8, D |
| 13 | `13_Library_Equipment_Evidence.png` | Library photo | Duplicated (same bytes as 12) | image label "Library" | DEMO-DOC-001 | Duplicate/reused image | B8, D |
| 14 | `14_Previous_Scrutiny_Deficiency_Report_2025-26.pdf` | Prior scrutiny | Valid, inconsistent ref | ref `DEMO/EOA/2025-26/0143`, 2025-08-20 | DEMO-DOC-002 | Inconsistent reference number | B8 |
| 15 | `15_Compliance_Response_2025-26.pdf` | Prior response | Valid | `AIT/COMP/2025-26/07`, 2025-09-10 | history | none | B6 |
| 16 | `16_Fire_Safety_Certificate_Altered.png` | Altered fire cert | Potential anomaly | visible patch over expiry date | DEMO-ANOM-001 | Potential anomaly — human review | D |

## Corrected documents (`demo-data/documents/corrected/`)

| # | File | Purpose | Expected extraction | Resolves |
|---|---|---|---|---|
| 17 | `17_Faculty_Appointment_Summary_CORRECTED.pdf` | Reconciled faculty list | total 42, PhD 24 (matches institutional record) | DEMO-FAC-001, DEMO-FAC-002 |
| 18 | `18_Fire_Safety_Certificate_RENEWED.pdf` | Renewed fire NOC | valid till 2027-03-31 | DEMO-NOC-001 |

## Institutional reference records (simulated, not files)

| Record | Value | Source label |
|---|---|---|
| Approved programmes | CSE, ECE, Mechanical | Simulated AICTE archive |
| Approved intake | 240 | Simulated AICTE archive |
| Faculty on record | 42 (24 PhD) | Simulated institutional record |
| Land on record | 5.20 acres | Simulated institutional record |
| Previous EoA | `DEMO/EOA/2025-26/0142` | Simulated AICTE archive |
| Previous observation | Faculty shortfall 42 vs 45 | Synthetic scrutiny report |

## Deliberate anomalies (for demonstration only)

| Anomaly | Where | Wording rule |
|---|---|---|
| Faculty count differs across 3 sources | docs 03, 04, reference record | "Potential inconsistency requiring clarification" |
| Expired NOC vs claimed date | docs 02, 10 | "Document appears expired" |
| Duplicate/reused image | docs 12 and 13 (same bytes) | "Potential duplicate evidence requiring human review" |
| Reference number mismatch | docs 01 and 14 | "Reference inconsistency" |
| City/name inconsistency | doc 06 | "Institution detail inconsistency" |
| Visual alteration signal | doc 16 | "Potential anomaly — human review required" |
| Verification pending | doc 05 | "Verification pending" |

None of these may be described as fraud, forgery or a statutory finding.

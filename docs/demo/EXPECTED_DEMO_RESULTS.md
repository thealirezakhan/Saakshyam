# Expected Demo Results

Reference for verifying the prototype. Values match `SYNTHETIC_DATA_CATALOG.md`.
All findings are decision-support signals, not statutory conclusions.

Automated check: `python scripts/e2e_demo.py` → `E2E DEMO: PASS`.

## 1. Expected extraction

| Document | Expected fields |
|---|---|
| 01 Previous EoA | `eoa_number=DEMO/EOA/2025-26/0142`, `academic_year=2025-26`, `approved_intake=240` |
| 02 Application form | `application_number=DEMO-EVENT-2026-001`, `proposed_intake=330`, `category=increase_intake` |
| 03 Faculty declaration | `total_faculty=48`, `faculty_phd_count=30` |
| 04 Faculty summary | `total_faculty=45`, `faculty_phd_count=27` |
| 05 Trust certificate | `registration_number=MAH/1234/2008`, `registration_date=2008-06-14` |
| 06 Affidavit | `deponent=Aarohan Education Society`, `affidavit_date=2026-01-10`, `city=Nagpur` |
| 07 Payment receipt | `receipt_number=TER/2026/000981`, `amount=350000`, `payment_date=2026-01-12` |
| 08 Compliance declaration | `declaration_date=2026-01-11`, signature **missing** |
| 09 Occupancy certificate | `certificate_number=OC/PUN/2024/7781`, `valid_until=2029-03-31` |
| 10 Fire NOC | `noc_number=FS/PUN/2024/5567`, `valid_until=2025-12-31` |
| 11 Floor plan | `built_up_sqm=14280`, `floors=4` |
| 12 / 13 images | identical SHA-256 (duplicate evidence) |
| 14 Scrutiny report | `eoa_reference=DEMO/EOA/2025-26/0143`, `report_date=2025-08-20` |
| 15 Compliance response | `response_reference=AIT/COMP/2025-26/07`, `response_date=2025-09-10` |
| 16 Altered fire cert | `valid_until=2027-03-31` with visible alteration marker |
| 17 Corrected faculty | `total_faculty=42`, `faculty_phd_count=24` |
| 18 Renewed fire NOC | `valid_until=2027-03-31` |

## 2. Expected validation findings (initial run)

| Finding | Rule | Severity | Status | Values / evidence |
|---|---|---|---|---|
| F1 Faculty count inconsistency | DEMO-FAC-001 | High | Open | declared 48 (doc 03) vs list 45 (doc 04) |
| F2 Faculty vs institutional record | DEMO-FAC-002 | High | Open | list 45 vs record 42 |
| F3 Fire NOC expired | DEMO-NOC-001 | High | Open | valid till 2025-12-31 (doc 10); application claims 2027-03-31 |
| F4 Duplicate/reused evidence | DEMO-DOC-001 | Medium | Open (human review) | docs 12 and 13 share SHA-256 |
| F5 Inconsistent reference number | DEMO-DOC-002 | Medium | Open | EoA 0142 (doc 01) vs 0143 (doc 14) |
| F6 Institution detail inconsistency | DEMO-ID-001 | Medium | Open | affidavit city "Nagpur" vs Pune |
| F7 Infrastructure evidence gap | DEMO-INF-001 | Medium | Open | declared labs vs lab/library evidence |
| F8 Verification pending | DEMO-VER-001 | Informational | Open | trust certificate pending |
| F9 Incomplete declaration | DEMO-CHK-001 | Medium | Open | doc 08 signature missing |

Passing checks expected: institution legal name present; land 5.20 acres meets minimum;
occupancy valid; built-up 14,280 sqm meets minimum; PhD count above minimum (declared).

No finding may use the words "fraud", "forged", "fake" or "guilty".

## 3. Expected verification responses (simulated)

| Document | Simulated source | Result | Returned value | Manual review |
|---|---|---|---|---|
| 01 Previous EoA | Simulated AICTE archive | VERIFIED | `DEMO/EOA/2025-26/0142`, intake 240 | No |
| 03 Faculty declaration | Simulated institutional registry | MISMATCH | 45 (submitted 48) | Yes |
| 05 Trust certificate | Simulated registrar | PENDING | — | No |
| 08 Compliance declaration | Simulated AICTE archive | MANUAL_REVIEW | — | Yes |
| 09 Occupancy certificate | Simulated municipal source | SOURCE_UNAVAILABLE | — | Yes |
| 10 Fire NOC | Simulated fire service | EXPIRED | valid till 2025-12-31 | Yes |

Every result shows: request ID, document type, simulated source, reference number,
submitted value, returned value, result, timestamp, explanation, and the banner
`SIMULATED VERIFICATION — NO LIVE GOVERNMENT OR ISSUING-AUTHORITY CONNECTION`.

## 4. Expected anomaly flags (no fraud claim)

| Flag | Evidence | Wording |
|---|---|---|
| Duplicate evidence | identical SHA-256 for docs 12/13 | "Potential duplicate evidence requiring human review" |
| Visual alteration signal | doc 16 patch over expiry | "Potential anomaly — human review required" |
| Reference discontinuity | docs 01 vs 14 | "Reference inconsistency requiring clarification" |

## 5. Expected infrastructure analysis

- Evidence inventory: building photo (metadata), lab photo (12), library photo (13),
  floor plan (11), equipment list (metadata).
- Duplicate flag: 12 and 13 are the same file.
- Gap: library equipment list not provided as a separate document.
- Declared vs evidence: built-up 14,280 sqm matches floor plan; lab count needs
  verification.
- Recommendation: "Additional evidence or EVC may be required" (human-confirmed).

## 6. Expected rectification outcomes

| Action | Finding(s) | Result |
|---|---|---|
| Upload `17_Faculty_Appointment_Summary_CORRECTED.pdf` + clarification | F2 | **Resolved** (faculty list 42 = institutional record 42) |
| Correct application `total_faculty` to 42 + revalidate | F1 | **Resolved** (declaration = list) |
| Upload `18_Fire_Safety_Certificate_RENEWED.pdf` | F3 | **Resolved** (valid till 2027-03-31) |
| Upload corrected compliance declaration (future fixture) | F9 | Resolved |
| Duplicate image replacement (future fixture) | F4 | Resolved or Escalated |
| Reference clarification | F5 | Escalated for human review if unresolved |

History rule: the original finding, correction event and new result all remain visible.

## 7. Expected application status progression

```
draft
 → submitted
 → validation_completed (open findings)
 → awaiting_institution_response
 → correction_submitted
 → revalidation_pending
 → partially_resolved (faculty resolved; NOC pending)
 → resolved (after renewed NOC)
 → scrutiny_review
 → evc_recommended
 → evc_notes_recorded
 → human_review_pending
```

No status is `approved` or `rejected` in the prototype; those are human/competent-authority
outcomes and are out of scope.

## 8. Expected audit events

- `auth.login` for each role.
- `application.create` / `application.view`.
- `document.upload` for each of the 16 files and the corrections.
- `validation.run` for the initial and revalidation runs.
- `verification.request` and `verification.result` (simulated).
- `finding.status.changed` for each lifecycle transition.
- `institution.response.submitted`.
- `review.observation.added`, `review.evidence.requested`.
- `evc.recommended`, `evc.note.added`.
- `report.generated`.

## 9. Acceptance checklist

- [ ] All 16 documents upload and classify as expected.
- [ ] Findings F1–F9 appear with evidence and correct severities.
- [ ] No fraud wording anywhere.
- [ ] Verification shows all six outcomes and the SIMULATED banner.
- [ ] Duplicate image is flagged.
- [ ] Infrastructure analysis flags duplicate and gap; EVC recommendation is human-confirmed.
- [ ] Correction resolves F1/F2; renewed NOC resolves F3.
- [ ] History retains the earlier findings.
- [ ] Reviewer can add observations and request evidence; cannot approve/reject.
- [ ] Report contains application, checklist, findings, verifications, rectifications, audit.
- [ ] Reset restores the initial state exactly.

"""Application-category workflow configuration.

Regulatory distinctions live here, not in the chat layer. Categories select the
document checklist, rule set, scrutiny stages and whether an EVC may be recommended.
Prototype-only entries are flagged with `needs_confirmation` where the current APH
addendum must be checked before production use.
"""

from dataclasses import dataclass

EVC_NOT_REQUIRED = "not_required"
EVC_MAY_BE_REQUIRED = "may_be_required"
EVC_REQUIRED = "required"


@dataclass(frozen=True)
class CategoryWorkflow:
    key: str
    title: str
    purpose: str
    required_sections: tuple[str, ...]
    documents: tuple[str, ...]
    historical_records: tuple[str, ...]
    rule_ids: tuple[str, ...]
    stages: tuple[str, ...]
    evc: str
    outputs: tuple[str, ...]
    deficiency_types: tuple[str, ...]
    needs_confirmation: bool = False


STAGES: dict[str, str] = {
    "initial_validation": "Automated checks on submitted data and documents",
    "institution_response": "Institution clarifies or corrects flagged items",
    "re_scrutiny": "Re-checks only previously flagged deficiencies",
    "scrutiny_committee": "Human scrutiny committee review",
    "evc": "Expert Visit Committee (infrastructure/faculty)",
    "standing_hearing": "Reviews EVC reports and show-cause replies",
    "standing_appellate": "Single appeal against a deficiency/rejection letter",
    "competent_authority": "Final statutory decision (human only)",
}


WORKFLOWS: dict[str, CategoryWorkflow] = {
    "eoa_self_disclosure": CategoryWorkflow(
        key="eoa_self_disclosure",
        title="Extension of Approval based on Self-Disclosure",
        purpose="Annual continuation by self-disclosure of facilities and infrastructure.",
        required_sections=("institution_profile", "faculty_cadre",
                           "land_infrastructure", "statutory_approvals"),
        documents=("institution_profile", "faculty_declaration", "land_document",
                   "building_occupancy", "fire_safety", "trust_registration",
                   "previous_eoa", "self_disclosure_declaration"),
        historical_records=("previous_eoa", "approved_programmes", "approved_intake"),
        rule_ids=("APH-4.1", "APH-4.2", "APH-7.2.1", "APH-8.1", "APH-8.2",
                  "APH-9.1", "APH-9.2", "APH-10.1"),
        stages=("initial_validation", "institution_response"),
        evc=EVC_NOT_REQUIRED,
        outputs=("completeness_report", "open_findings", "self_disclosure_pack"),
        deficiency_types=("missing_field", "expired_noc", "unverifiable_claim",
                          "inconsistency"),
        needs_confirmation=True,
    ),
    "increase_intake": CategoryWorkflow(
        key="increase_intake",
        title="Increase in Intake / Additional Course",
        purpose="Increase sanctioned intake or add a course in an existing institution.",
        required_sections=("institution_profile", "programme_details", "faculty_cadre",
                           "land_infrastructure", "statutory_approvals", "finance"),
        documents=("application_form", "faculty_list", "faculty_declaration",
                   "land_document", "building_occupancy", "fire_safety",
                   "building_plan", "laboratory_evidence", "library_evidence",
                   "payment_receipt", "affidavit", "previous_eoa",
                   "compliance_declaration"),
        historical_records=("previous_eoa", "approved_programmes", "approved_intake",
                            "previous_scrutiny_report", "previous_compliance_response"),
        rule_ids=("APH-4.1", "APH-4.2", "APH-7.2.1", "APH-8.1", "APH-8.2",
                  "APH-9.1", "DEMO-FAC-001", "DEMO-FAC-002", "DEMO-DOC-001",
                  "DEMO-DOC-002", "DEMO-INF-001"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "evc", "standing_hearing", "competent_authority"),
        evc=EVC_REQUIRED,
        outputs=("deficiency_report", "evidence_comparison", "evc_recommendation",
                 "scrutiny_summary"),
        deficiency_types=("faculty_shortfall", "faculty_inconsistency",
                          "capacity_shortfall", "expired_noc", "missing_lab_evidence",
                          "duplicate_evidence", "reference_mismatch"),
        needs_confirmation=True,
    ),
    "new_programme": CategoryWorkflow(
        key="new_programme",
        title="Start New Programme / Level",
        purpose="Start a new programme or level in an existing institution.",
        required_sections=("institution_profile", "programme_details", "faculty_cadre",
                           "land_infrastructure", "affiliation", "finance"),
        documents=("application_form", "programme_details", "faculty_list",
                   "infrastructure_evidence", "laboratory_equipment", "library_evidence",
                   "affiliation_letter", "trust_registration", "affidavit"),
        historical_records=("approved_programmes", "existing_faculty",
                            "existing_infrastructure"),
        rule_ids=("APH-4.1", "APH-7.2.1", "APH-8.1", "APH-8.2", "DEMO-INF-001"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "evc", "competent_authority"),
        evc=EVC_MAY_BE_REQUIRED,
        outputs=("readiness_report", "gap_list", "evc_recommendation"),
        deficiency_types=("faculty_shortfall", "missing_lab_equipment",
                          "library_shortfall", "affiliation_invalid"),
        needs_confirmation=True,
    ),
    "change_of_site": CategoryWorkflow(
        key="change_of_site",
        title="Change of Site / Location",
        purpose="Relocate an existing institution to a new site.",
        required_sections=("institution_profile", "land_infrastructure",
                           "statutory_approvals", "affiliation"),
        documents=("land_document", "lease_deed", "building_plan", "building_occupancy",
                   "fire_safety", "state_noc", "affiliation_letter",
                   "site_photographs", "previous_eoa"),
        historical_records=("previous_eoa", "old_site_approval", "relocation_notices"),
        rule_ids=("APH-4.2", "APH-8.1", "APH-8.2", "APH-9.1", "DEMO-DOC-002"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "evc", "competent_authority"),
        evc=EVC_MAY_BE_REQUIRED,
        outputs=("site_evidence_pack", "address_findings", "evc_checklist"),
        deficiency_types=("land_shortfall", "lease_shortfall", "address_mismatch",
                          "expired_noc"),
        needs_confirmation=True,
    ),
    "restoration": CategoryWorkflow(
        key="restoration",
        title="Restoration of Intake / After Break in EoA",
        purpose="Restore intake after a break in the preceding academic year(s).",
        required_sections=("institution_profile", "faculty_cadre", "land_infrastructure",
                           "statutory_approvals"),
        documents=("previous_eoa", "break_records", "faculty_list", "infrastructure_evidence",
                   "fire_safety", "compliance_response"),
        historical_records=("last_approval", "break_period", "previous_deficiencies"),
        rule_ids=("APH-4.1", "APH-7.2.1", "APH-8.1", "APH-9.1", "DEMO-FAC-002"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "evc", "competent_authority"),
        evc=EVC_MAY_BE_REQUIRED,
        outputs=("restoration_readiness", "historical_comparison", "evidence_requests"),
        deficiency_types=("continuity_gap", "readiness_shortfall", "expired_noc"),
        needs_confirmation=True,
    ),
    "merger": CategoryWorkflow(
        key="merger",
        title="Merger of Institutions",
        purpose="Merge institutions under the same trust/society/company.",
        required_sections=("institution_profile", "trust_details", "programme_details",
                           "faculty_cadre", "land_infrastructure", "finance"),
        documents=("trust_registration", "approvals_both_entities", "land_document",
                   "faculty_list", "programme_mapping", "noc", "amalgamation_resolution"),
        historical_records=("approvals_both_entities", "observations_both_entities"),
        rule_ids=("APH-4.1", "APH-7.2.1", "APH-8.1", "DEMO-FAC-002"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "evc", "competent_authority"),
        evc=EVC_MAY_BE_REQUIRED,
        outputs=("merger_readiness", "programme_continuity", "evidence_pack"),
        deficiency_types=("trust_mismatch", "programme_continuity_gap",
                          "faculty_shortfall", "land_shortfall"),
        needs_confirmation=True,
    ),
    "closure": CategoryWorkflow(
        key="closure",
        title="Closure of Institution / Programme",
        purpose="Close an institution or programme with student protection.",
        required_sections=("institution_profile", "programme_details", "student_records"),
        documents=("closure_application", "student_redistribution_plan", "university_noc",
                   "state_noc", "faculty_student_records", "affidavit"),
        historical_records=("approved_programmes", "enrolled_students", "closure_notices"),
        rule_ids=("APH-4.1", "DEMO-CLO-001"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "competent_authority"),
        evc=EVC_NOT_REQUIRED,
        outputs=("closure_checklist", "student_protection_findings"),
        deficiency_types=("missing_redistribution_plan", "invalid_noc",
                          "programme_closure_gap"),
        needs_confirmation=True,
    ),
    "identity_change": CategoryWorkflow(
        key="identity_change",
        title="Change in Institution / Affiliating University Details",
        purpose="Change institution name, affiliating university/board, or type.",
        required_sections=("institution_profile", "trust_details", "affiliation"),
        documents=("trust_resolution", "registration_proof", "affiliation_letter",
                   "updated_certificates", "previous_eoa"),
        historical_records=("prior_names", "affiliation_history"),
        rule_ids=("APH-4.1", "DEMO-ID-001"),
        stages=("initial_validation", "institution_response", "scrutiny_committee",
                "re_scrutiny", "competent_authority"),
        evc=EVC_NOT_REQUIRED,
        outputs=("identity_consistency_findings", "updated_record"),
        deficiency_types=("name_mismatch", "affiliation_invalid", "trust_mismatch"),
        needs_confirmation=True,
    ),
}


def get_workflow(key: str) -> CategoryWorkflow:
    try:
        return WORKFLOWS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown application category: {key}") from exc


def category_catalog() -> list[dict]:
    return [
        {
            "key": w.key,
            "title": w.title,
            "purpose": w.purpose,
            "documents": list(w.documents),
            "stages": list(w.stages),
            "evc": w.evc,
            "needs_confirmation": w.needs_confirmation,
        }
        for w in WORKFLOWS.values()
    ]

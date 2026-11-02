"""Mock issuing-authority verification adapter.

Deterministic outcomes for the demo. This is NOT a live government or
issuing-authority connection; the UI must display the SIMULATED banner.
Replace this adapter with an authorised integration later.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class VerificationResult:
    result: str
    source: str
    reference_number: str
    submitted_value: str
    returned_value: str
    explanation: str
    manual_review_required: bool


class MockVerificationAdapter:
    name = "simulated"

    def verify(self, document, fields: dict[str, str]) -> VerificationResult:
        cls = document.doc_class
        if cls == "previous_eoa":
            value = fields.get("eoa_number", "")
            return VerificationResult(
                "verified", "Simulated AICTE archive", value, value, value,
                "Record matched the simulated AICTE archive.", False)
        if cls in ("faculty_statement", "faculty_declaration"):
            submitted = fields.get("total_faculty", "")
            return VerificationResult(
                "mismatch", "Simulated institutional registry", submitted, submitted, "45",
                f"Submitted value {submitted} differs from the simulated registry value 45.",
                True)
        if cls == "trust_registration":
            return VerificationResult(
                "pending", "Simulated registrar", fields.get("registration_number", ""),
                fields.get("registration_number", ""), "",
                "Verification request queued with the simulated registrar.", False)
        if cls == "compliance_declaration":
            return VerificationResult(
                "manual_review", "Simulated AICTE archive", "", "", "",
                "Insufficient structured data for automated verification; manual review required.",
                True)
        if cls == "occupancy_certificate":
            return VerificationResult(
                "source_unavailable", "Simulated municipal source",
                fields.get("certificate_number", ""), fields.get("certificate_number", ""), "",
                "The simulated municipal source did not respond.", True)
        if cls == "fire_noc":
            expiry = fields.get("fire_noc_expiry", "")
            expired = bool(expiry) and expiry < str(date.today())
            return VerificationResult(
                "expired" if expired else "verified", "Simulated fire service",
                fields.get("noc_number", ""), expiry, expiry,
                ("The simulated NOC record is expired." if expired
                 else "NOC valid in the simulated source."), expired)
        return VerificationResult(
            "manual_review", "Simulated source", "", "", "",
            "No automated verification adapter for this document type; manual review required.",
            True)

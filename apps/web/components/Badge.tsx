const MAP: Record<string, { cls: string; label: string }> = {
  PASS: { cls: "bg-compliant text-compliant-fg border-compliant-border", label: "COMPLIANT" },
  FAIL: { cls: "bg-rejected text-rejected-fg border-rejected-border", label: "DEFICIENCY" },
  NEEDS_REVIEW: { cls: "bg-pending text-pending-fg border-pending-border", label: "REVIEW" },
  NOT_APPLICABLE: { cls: "bg-surface-container text-on-surface-variant border-outline-variant", label: "N/A" },
  NOT_EVALUATED: { cls: "bg-surface-container text-on-surface-variant border-outline-variant", label: "NOT EVALUATED" },
  succeeded: { cls: "bg-compliant text-compliant-fg border-compliant-border", label: "EXTRACTED" },
  needs_review: { cls: "bg-pending text-pending-fg border-pending-border", label: "NEEDS REVIEW" },
  failed: { cls: "bg-rejected text-rejected-fg border-rejected-border", label: "FAILED" },
  processing: { cls: "bg-surface-container text-on-surface-variant border-outline-variant", label: "PROCESSING" },
  uploaded: { cls: "bg-surface-container text-on-surface-variant border-outline-variant", label: "QUEUED" },
  draft: { cls: "bg-copilot text-copilot-fg border-copilot-border", label: "DRAFT" },
  missing: { cls: "bg-rejected text-rejected-fg border-rejected-border", label: "MISSING" },
  expired: { cls: "bg-rejected text-rejected-fg border-rejected-border", label: "EXPIRED" },
  unverified: { cls: "bg-pending text-pending-fg border-pending-border", label: "UNVERIFIED" },
};

export function Badge({ status, label }: { status: string; label?: string }) {
  const entry = MAP[status] || {
    cls: "bg-surface-container text-on-surface-variant border-outline-variant",
    label: status,
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-semibold uppercase tracking-wide whitespace-nowrap ${entry.cls}`}
    >
      {label || entry.label}
    </span>
  );
}

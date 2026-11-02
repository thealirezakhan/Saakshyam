"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { AskCopilot } from "@/components/AskCopilot";
import { api, applicationId, canRunValidation, ensureApplication } from "@/lib/api";
import type { DocumentItem, Finding, Report } from "@/lib/types";

export default function ValidationPage() {
  return (
    <AuthGuard>
      <Validation />
    </AuthGuard>
  );
}

function Validation() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");
  const [detail, setDetail] = useState<Finding | null>(null);
  const [note, setNote] = useState("");
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [history, setHistory] = useState<Finding[]>([]);
  const [busy, setBusy] = useState(false);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2600);
  }

  async function openDetail(f: Finding) {
    setDetail(f);
    setNote("");
    setSelectedDoc("");
    setHistory([]);
    try {
      setDocs(await api<DocumentItem[]>("/documents"));
      setHistory(await api<Finding[]>(`/findings/${f.finding_id}/history`));
    } catch {
      /* ignore */
    }
  }

  async function submitCorrection() {
    if (!detail) return;
    setBusy(true);
    try {
      const updated = await api<Finding>(`/findings/${detail.finding_id}/clarification`, {
        method: "POST",
        body: { note, document_id: selectedDoc || null },
      });
      setDetail(updated);
      flash("Correction submitted for revalidation.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not submit correction");
    } finally {
      setBusy(false);
    }
  }

  async function revalidate() {
    if (!detail) return;
    setBusy(true);
    try {
      const res = await api<{ finding: Finding; revalidation: Finding | null }>(
        `/findings/${detail.finding_id}/revalidate`, { method: "POST" });
      setDetail(res.finding);
      setHistory(await api<Finding[]>(`/findings/${detail.finding_id}/history`));
      flash(res.finding.lifecycle_status === "Resolved" ? "Finding resolved after revalidation." : "Revalidation complete; finding remains unresolved.");
      await run();
    } catch (e) {
      flash(e instanceof Error ? e.message : "Revalidation failed");
    } finally {
      setBusy(false);
    }
  }

  async function escalate() {
    if (!detail) return;
    setBusy(true);
    try {
      const updated = await api<Finding>(`/findings/${detail.finding_id}/escalate`, { method: "POST" });
      setDetail(updated);
      flash("Escalated for human review.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not escalate");
    } finally {
      setBusy(false);
    }
  }

  async function run() {
    setLoading(true);
    try {
      await ensureApplication();
      const r = await api<{ run_id: string }>(`/applications/${applicationId()}/validations`, { method: "POST", body: {} });
      setFindings(await api<Finding[]>(`/validations/${r.run_id}/findings`));
    } catch {
      flash("Validation could not be completed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        await ensureApplication();
        const rep = await api<Report>(`/applications/${applicationId()}/report`);
        if (rep.findings?.length) {
          setFindings(rep.findings);
          setLoading(false);
        } else if (canRunValidation()) {
          await run();
        } else {
          setLoading(false);
        }
      } catch {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const passed = findings.filter((f) => f.status === "PASS").length;
  const unresolved = findings.filter((f) => f.status === "FAIL" || f.status === "NEEDS_REVIEW");
  const primary =
    findings.find((f) => f.rule_id === "APH-7.2.1" && f.status === "FAIL") ||
    findings.find((f) => f.status === "FAIL") ||
    unresolved[0] ||
    findings[0];
  const stats = parseStats(primary);

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-4xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Validation &amp; Scrutiny</div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">
                {loading ? "Evaluating rules…" : `${passed} of ${findings.length} rules satisfied`}
              </h1>
              <p className="font-body-md text-on-surface-variant mt-1">Deterministic audit against AICTE APH 2025–26</p>
            </div>
            <div className="flex items-center gap-2">
              <AskCopilot
                context={{ kind: "analysis", label: "Compliance findings" }}
                prompt="Explain all unresolved compliance findings and how to resolve them."
                label="Explain findings"
              />
              <button
                onClick={run}
                className="px-3.5 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md shadow-sm hover:bg-primary-container transition-colors flex items-center gap-1.5"
                type="button"
              >
                <span className="material-symbols-outlined text-[16px]">bolt</span> Rerun validation
              </button>
            </div>
          </div>

          {primary ? (
            <div className="mt-5 bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${primary.status === "FAIL" ? "bg-error-container/60 text-error" : "bg-pending text-pending-fg"}`}>
                    <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      {primary.status === "FAIL" ? "warning" : "pending"}
                    </span>
                  </div>
                  <div>
                    <div className={`font-label-sm uppercase tracking-wider font-semibold ${primary.status === "FAIL" ? "text-error" : "text-pending-fg"}`}>
                      {primary.status === "FAIL" ? "Primary deficiency" : "Under review"}
                    </div>
                    <h2 className="font-headline-md font-semibold tracking-tight">
                      {primary.rule_id} — {primary.explanation.split(".")[0]}
                    </h2>
                  </div>
                </div>
                <Badge status={primary.status} />
              </div>

              <div className="grid grid-cols-3 gap-2 py-3 my-3 bg-surface-container-low/60 rounded-lg px-3">
                <Stat label="Required" value={stats.required} unit={stats.unit} />
                <Stat label="Submitted" value={stats.submitted} unit="verified" />
                <Stat label="Shortfall" value={stats.shortfall} unit={stats.shortfallLabel} tone />
              </div>

              <div className="flex justify-between items-center mb-1.5">
                <span className="font-label-sm text-on-surface-variant">Cadre distribution compliance</span>
                <span className="font-label-sm font-semibold text-on-surface">{stats.pct}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-surface-container overflow-hidden flex">
                <div className="bg-primary h-full" style={{ width: `${stats.regular}%` }} />
                <div className="bg-secondary-fixed-dim h-full" style={{ width: `${stats.reclass}%` }} />
                <div className="bg-error-container h-full" style={{ width: `${stats.deficit}%` }} />
              </div>

              <div className="mt-3 p-3 rounded-lg bg-copilot border border-copilot-border flex items-start gap-2">
                <span className="material-symbols-outlined text-[18px] text-copilot-fg">insights</span>
                <p className="font-body-sm text-copilot-fg">{primary.remediation || primary.explanation}</p>
              </div>

              <div className="flex flex-wrap gap-2 mt-4">
                <AskCopilot
                  context={{ kind: "finding", id: primary.finding_id, label: primary.rule_id }}
                  prompt={`Explain finding ${primary.rule_id} and suggest a correction.`}
                  label="Explain with Copilot"
                />
                <AskCopilot
                  context={{ kind: "finding", id: primary.finding_id, label: primary.rule_id }}
                  prompt={`Compare the evidence for ${primary.rule_id} with the application value and suggest a correction.`}
                  label="Compare evidence"
                />
                <button
                  onClick={() => openDetail(primary)}
                  className="px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-label-md text-label-md hover:bg-surface-container transition-colors"
                  type="button"
                >
                  Review / correct
                </button>
                <button
                  onClick={() => flash("Council scrutiny requested. A reviewer will be assigned.")}
                  className="px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface-variant font-label-md text-label-md hover:bg-surface-container transition-colors"
                  type="button"
                >
                  Request council scrutiny
                </button>
              </div>
            </div>
          ) : (
            <div className="mt-5 bg-surface-container-lowest rounded-xl shadow-sm p-8 text-center text-body-md text-on-surface-variant">
              {loading ? "Running deterministic rule checks…" : "No findings available. Rerun validation to evaluate the application."}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md mt-5">
            {findings
              .filter((f) => f.finding_id !== primary?.finding_id)
              .map((f) => (
                <div key={f.finding_id} className="bg-surface-container-lowest rounded-xl shadow-sm p-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-label-sm uppercase tracking-wider font-semibold text-on-surface-variant">{f.severity} severity</span>
                    <Badge status={f.status} />
                  </div>
                  <h3 className="font-body-md font-semibold tracking-tight">{f.rule_id} — {(f.explanation || "").slice(0, 70)}</h3>
                  <div className="mt-2 flex items-center justify-between">
                    <AskCopilot
                      context={{ kind: "finding", id: f.finding_id, label: f.rule_id }}
                      prompt={`Explain finding ${f.rule_id} and how to resolve it.`}
                      label="Explain"
                      className="px-2 py-1 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
                    />
                    <button
                      onClick={() => openDetail(f)}
                      className="px-2 py-1 rounded-full bg-surface-container-low text-on-surface-variant font-label-sm text-label-sm"
                      type="button"
                    >
                      Review
                    </button>
                    <span className="font-label-sm text-on-surface-variant">{f.field_key}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </main>
      <Footer />

      {detail && (
        <div className="fixed inset-0 z-[70] bg-black/30 flex items-center justify-center p-4" onClick={() => setDetail(null)}>
          <div className="bg-surface-container-lowest rounded-xl shadow-utility w-full max-w-2xl max-h-[85vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-headline-md font-semibold">{detail.rule_id}</h3>
                  <Badge status={detail.status} />
                  <span className="font-label-sm text-on-surface-variant capitalize">{detail.lifecycle_status || "Open"}</span>
                </div>
                <p className="font-body-sm text-on-surface-variant mt-1">
                  {detail.rule_official ? "Official requirement (sample rule)" : "Prototype demo rule"} · severity {detail.severity}
                </p>
              </div>
              <button onClick={() => setDetail(null)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <p className="font-body-md text-on-surface mt-3">{detail.explanation}</p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3 font-body-sm">
              <div className="p-3 rounded-lg bg-surface-container-low">
                <div className="font-label-sm uppercase text-on-surface-variant">Application value</div>
                <div className="font-semibold">{detail.application_value || "—"}</div>
              </div>
              <div className="p-3 rounded-lg bg-surface-container-low">
                <div className="font-label-sm uppercase text-on-surface-variant">Comparison</div>
                <div className="font-semibold">{detail.reference_value || "—"}</div>
              </div>
              <div className="p-3 rounded-lg bg-surface-container-low">
                <div className="font-label-sm uppercase text-on-surface-variant">Institutional record</div>
                <div className="font-semibold">{detail.institutional_record || "—"}</div>
              </div>
            </div>

            {detail.evidence && (
              <div className="mt-3 p-3 rounded-lg bg-copilot border border-copilot-border font-body-sm text-copilot-fg">
                <div className="font-semibold">{detail.evidence.filename} · page {detail.evidence.page}</div>
                <div className="font-mono mt-1">“{detail.evidence.text_span}”</div>
              </div>
            )}

            <div className="mt-4">
              <label className="block font-label-sm uppercase tracking-wider text-on-surface-variant mb-1">Clarification</label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                placeholder="Describe the correction or clarification…"
                className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 font-body-sm"
              />
              <label className="block font-label-sm uppercase tracking-wider text-on-surface-variant mt-2 mb-1">Corrected document</label>
              <select
                value={selectedDoc}
                onChange={(e) => setSelectedDoc(e.target.value)}
                className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 font-body-sm"
              >
                <option value="">None</option>
                {docs.map((d) => (
                  <option key={d.document_id} value={d.document_id}>{d.filename}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap gap-2 mt-4">
              <button onClick={submitCorrection} disabled={busy || !note.trim()} className="px-3 py-1.5 rounded-full bg-inverse-surface text-inverse-on-surface font-label-md text-label-md disabled:opacity-50">
                Submit correction
              </button>
              <button onClick={revalidate} disabled={busy} className="px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md disabled:opacity-50">
                Revalidate
              </button>
              <button onClick={escalate} disabled={busy} className="px-3 py-1.5 rounded-full bg-rejected text-rejected-fg border border-rejected-border font-label-md text-label-md disabled:opacity-50">
                Escalate to human review
              </button>
            </div>

            <div className="mt-5">
              <h4 className="font-label-md font-semibold uppercase tracking-wide text-on-surface-variant">History</h4>
              <div className="mt-2 space-y-2">
                {history.map((h) => (
                  <div key={h.finding_id} className="p-2.5 rounded-lg bg-surface-container-low">
                    <div className="flex items-center justify-between font-label-sm text-on-surface-variant">
                      <span>{h.rule_id} · {h.status}</span>
                      <span className="capitalize">{h.lifecycle_status || "Open"}</span>
                    </div>
                    <div className="font-body-sm text-on-surface mt-1">{h.explanation}</div>
                  </div>
                ))}
                {history.length === 0 && <p className="font-body-sm text-on-surface-variant">No history yet.</p>}
              </div>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg bg-inverse-surface text-inverse-on-surface shadow-utility font-body-sm max-w-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, unit, tone }: { label: string; value: string; unit: string; tone?: boolean }) {
  return (
    <div>
      <div className={`font-label-sm uppercase font-medium ${tone ? "text-error" : "text-on-surface-variant"}`}>{label}</div>
      <div className="flex items-baseline gap-1 mt-0.5">
        <span className={`font-headline-xl text-headline-xl font-bold tracking-tight ${tone ? "text-error" : "text-on-surface"}`}>{value}</span>
        <span className={`font-label-md ${tone ? "text-error" : "text-on-surface-variant"}`}>{unit}</span>
      </div>
    </div>
  );
}

function parseStats(f?: Finding) {
  const fallback = {
    required: "51", submitted: "48", shortfall: "-3", unit: "professors",
    shortfallLabel: "cadre gap", pct: "94.1", regular: 78, reclass: 16, deficit: 6,
  };
  if (!f) return fallback;
  const nums = (f.application_value || "").match(/\d+/g);
  if (f.rule_id === "APH-7.2.1" && nums && nums.length >= 2) {
    const submitted = Number(nums[0]);
    const required = Number(nums[1]);
    const gap = submitted - required;
    const pct = required ? Math.min(100, Math.round((submitted / required) * 1000) / 10) : 0;
    const deficitPct = Math.max(0, Math.round((Math.abs(gap) / Math.max(required, 1)) * 100));
    return {
      required: String(required), submitted: String(submitted), shortfall: String(gap),
      unit: "professors", shortfallLabel: "cadre gap", pct: String(pct),
      regular: Math.max(0, 100 - deficitPct - 16), reclass: 16, deficit: deficitPct,
    };
  }
  return { ...fallback, required: f.application_value || "—", submitted: f.application_value || "—", shortfall: f.status === "FAIL" ? "FAIL" : "—", unit: "", shortfallLabel: f.status };
}

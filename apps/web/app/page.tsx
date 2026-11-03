"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { AskCopilot } from "@/components/AskCopilot";
import { api, applicationId, canRunValidation, ensureApplication } from "@/lib/api";
import type { ApplicationSummary, DocumentItem, Report } from "@/lib/types";

interface AuditEvent {
  action: string;
  target: string;
  at: string;
}

export default function OverviewPage() {
  return (
    <AuthGuard>
      <Overview />
    </AuthGuard>
  );
}

function Overview() {
  const router = useRouter();
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const id = await ensureApplication();
        const s = await api<ApplicationSummary>("/applications/" + id);
        setSummary(s);
        let rep = await api<Report>(`/applications/${id}/report`);
        if (!rep.findings?.length && canRunValidation()) {
          await api(`/applications/${id}/validations`, { method: "POST", body: {} });
          rep = await api<Report>(`/applications/${id}/report`);
        }
        setReport(rep);
        setDocs(await api<DocumentItem[]>("/documents"));
        setAudit(await api<AuditEvent[]>(`/applications/${id}/audit`));
      } catch {
        router.replace("/login");
      }
    })();
  }, [router]);

  const findings = report?.findings || [];
  const open = findings.filter((f) => f.status === "FAIL" || f.status === "NEEDS_REVIEW");
  const failed = findings.filter((f) => f.status === "FAIL");
  const passed = report?.statuses?.PASS || 0;
  const processing = docs.filter((d) => d.status === "processing" || d.status === "uploaded").length;
  const needsReview = docs.filter((d) => d.status === "needs_review").length;
  const readiness = findings.length ? Math.round((passed / findings.length) * 100) : 0;

  const insights: Array<{ text: string; action: string; ctx: any }> = [];
  if (open.length) {
    insights.push({
      text: `${open.length} compliance finding(s) require attention (${failed.length} deficiency).`,
      action: "Explain findings",
      ctx: { kind: "analysis", label: "Open compliance findings" },
    });
  }
  if (needsReview) {
    insights.push({
      text: `${needsReview} document(s) need manual verification.`,
      action: "Review evidence",
      ctx: { kind: "document", label: "Documents needing review" },
    });
  }
  if (processing) {
    insights.push({ text: `${processing} document(s) still processing.`, action: "Check documents", ctx: { kind: "document", label: "Processing documents" } });
  }
  const missing = summary
    ? summary.sections.flatMap((s) => s.fields).filter((f) => f.required && !f.value)
    : [];
  if (missing.length) {
    insights.push({
      text: `${missing.length} required field(s) are still empty (e.g. ${missing.slice(0, 2).map((f) => f.label).join(", ")}).`,
      action: "Find missing info",
      ctx: { kind: "section", label: "Incomplete required fields" },
    });
  }

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-6xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                Application command centre
              </div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">
                {summary?.reference_no || "Loading application…"}
              </h1>
              <p className="font-body-md text-on-surface-variant mt-1">
                {summary?.application_type} · AY {summary?.academic_year}
              </p>
            </div>
            <AskCopilot
              context={{ kind: "overview", label: summary?.reference_no }}
              prompt="What needs my attention in my application right now?"
              label="What needs attention?"
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-space-md mt-6">
            <Stat label="Completion" value={`${summary?.completion_pct ?? 0}%`} sub={`${summary?.required_fields.filled ?? 0}/${summary?.required_fields.total ?? 0} required fields`} />
            <Stat label="Readiness" value={`${readiness}%`} sub={`${passed}/${findings.length} checks satisfied`} />
            <Stat label="Documents indexed" value={String(docs.filter((d) => d.status === "succeeded").length)} sub={`${docs.length} total · ${needsReview} need review`} />
            <Stat label="Open issues" value={String(open.length)} sub={`${failed.length} deficiency · ${open.length - failed.length} review`} tone={failed.length ? "error" : undefined} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-md mt-6">
            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-headline-md text-body-lg font-semibold">Critical outstanding issues</h2>
                <a href="/validation" className="font-label-sm text-primary">Open validation →</a>
              </div>
              <div className="mt-3 space-y-2">
                {open.slice(0, 5).map((f) => (
                  <div key={f.finding_id} className="p-3 rounded-lg bg-surface-container-low flex items-start gap-3">
                    <Badge status={f.status} />
                    <div className="min-w-0 flex-1">
                      <div className="font-body-sm font-semibold text-on-surface">
                        {f.rule_id} — {f.explanation.split(". ")[0]}
                      </div>
                      <div className="font-label-sm text-on-surface-variant truncate">{f.remediation || "Review required"}</div>
                    </div>
                    <AskCopilot
                      context={{ kind: "finding", id: f.finding_id, label: f.rule_id }}
                      prompt={`Explain finding ${f.rule_id} and how to resolve it.`}
                      label="Ask"
                      className="shrink-0 px-2 py-1 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
                    />
                  </div>
                ))}
                {open.length === 0 && <p className="font-body-sm text-on-surface-variant">No open findings.</p>}
              </div>
            </section>

            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-headline-md text-body-lg font-semibold">Proactive insights</h2>
                <span className="font-label-sm text-on-surface-variant">Derived from current data</span>
              </div>
              <div className="mt-3 space-y-2">
                {insights.map((ins, i) => (
                  <div key={i} className="p-3 rounded-lg bg-copilot border border-copilot-border flex items-center gap-3">
                    <span className="material-symbols-outlined text-[18px] text-copilot-fg">insights</span>
                    <span className="font-body-sm text-copilot-fg flex-1">{ins.text}</span>
                    <AskCopilot
                      context={ins.ctx}
                      prompt={ins.text}
                      label={ins.action}
                      className="shrink-0 px-2 py-1 rounded-full bg-white/60 text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
                    />
                  </div>
                ))}
                {insights.length === 0 && <p className="font-body-sm text-on-surface-variant">Nothing needs attention right now.</p>}
              </div>
            </section>
          </div>

          <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5 mt-6">
            <div className="flex items-center justify-between">
              <h2 className="font-headline-md text-body-lg font-semibold">Recent activity</h2>
              <span className="font-label-sm text-on-surface-variant">Latest audit events</span>
            </div>
            <div className="mt-3 divide-y divide-surface-container-high/60">
              {audit.slice(0, 8).map((e, i) => (
                <div key={i} className="py-2 flex items-center gap-3">
                  <span className="font-label-sm text-on-surface-variant w-40 truncate">{e.action}</span>
                  <span className="font-mono text-[11px] text-on-surface-variant flex-1 truncate">{e.target}</span>
                  <span className="font-label-sm text-on-surface-variant">{e.at?.slice(0, 19)}</span>
                </div>
              ))}
              {audit.length === 0 && <p className="py-2 font-body-sm text-on-surface-variant">No activity recorded yet.</p>}
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function Stat({ label, value, sub, tone }: { label: string; value: string; sub: string; tone?: "error" }) {
  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-sm p-4">
      <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">{label}</div>
      <div className={`font-headline-xl text-headline-xl font-bold tracking-tight mt-1 ${tone === "error" ? "text-error" : "text-on-surface"}`}>
        {value}
      </div>
      <div className="font-label-sm text-on-surface-variant mt-0.5">{sub}</div>
    </div>
  );
}

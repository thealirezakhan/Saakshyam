"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { AskCopilot } from "@/components/AskCopilot";
import { api, applicationId, canRunValidation, ensureApplication } from "@/lib/api";
import type { ApplicationSummary, Finding, Report } from "@/lib/types";

export default function AnalysisPage() {
  return (
    <AuthGuard>
      <Analysis />
    </AuthGuard>
  );
}

function Analysis() {
  const router = useRouter();
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const id = await ensureApplication();
        setSummary(await api<ApplicationSummary>("/applications/" + id));
        let rep = await api<Report>(`/applications/${id}/report`);
        if (!rep.findings?.length && canRunValidation()) {
          await api(`/applications/${id}/validations`, { method: "POST", body: {} });
          rep = await api<Report>(`/applications/${id}/report`);
        }
        setReport(rep);
      } catch {
        router.replace("/login");
      }
    })();
  }, [router]);

  const findings = report?.findings || [];
  const counts = report?.statuses || {};
  const total = findings.length || 1;
  const crossDoc = findings.filter((f) => ["APH-13.1", "APH-8.3"].includes(f.rule_id));
  const unresolved = findings.filter((f) => f.status === "FAIL" || f.status === "NEEDS_REVIEW");
  const missingFields = summary
    ? summary.sections.flatMap((s) => s.fields).filter((f) => f.required && !f.value)
    : [];

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-5xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Analysis</div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">Application intelligence</h1>
              <p className="font-body-md text-on-surface-variant mt-1">Completeness, consistency and compliance insights</p>
            </div>
            <AskCopilot
              context={{ kind: "analysis", label: "Application intelligence" }}
              prompt="Analyze my application health and explain the key risks."
              label="Analyze with Copilot"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-md mt-6">
            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <h2 className="font-headline-md text-body-lg font-semibold">Finding distribution</h2>
              <div className="mt-3 space-y-2">
                {["PASS", "FAIL", "NEEDS_REVIEW", "NOT_APPLICABLE", "NOT_EVALUATED"].map((k) => {
                  const v = counts[k] || 0;
                  const pct = Math.round((v / total) * 100);
                  return (
                    <div key={k} className="flex items-center gap-2">
                      <span className="font-label-sm text-on-surface-variant w-28">{k.replace(/_/g, " ")}</span>
                      <div className="flex-1 h-2 bg-surface-container rounded-full overflow-hidden">
                        <div
                          className={
                            "h-full " +
                            (k === "PASS" ? "bg-secondary" : k === "FAIL" ? "bg-error" : k === "NEEDS_REVIEW" ? "bg-pending-fg" : "bg-outline")
                          }
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="font-label-sm text-on-surface-variant w-10 text-right">{v}</span>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <h2 className="font-headline-md text-body-lg font-semibold">Section completeness</h2>
              <div className="mt-3 space-y-2">
                {summary?.sections.map((s) => (
                  <div key={s.section_id} className="flex items-center gap-2">
                    <span className="font-body-sm text-on-surface-variant w-48 truncate">{s.title}</span>
                    <div className="flex-1 h-2 bg-surface-container rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${s.completion}%` }} />
                    </div>
                    <span className="font-label-sm text-on-surface-variant w-10 text-right">{s.completion}%</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-headline-md text-body-lg font-semibold">Cross-document consistency</h2>
                <a href="/documents" className="font-label-sm text-primary">Documents →</a>
              </div>
              <div className="mt-3 space-y-2">
                {crossDoc.map((f) => (
                  <div key={f.finding_id} className="p-3 rounded-lg bg-surface-container-low flex items-center gap-2">
                    <Badge status={f.status} />
                    <span className="font-mono text-[11px] text-on-surface-variant">{f.rule_id}</span>
                    <span className="font-body-sm text-on-surface flex-1 truncate">{f.explanation}</span>
                  </div>
                ))}
                {crossDoc.length === 0 && <p className="font-body-sm text-on-surface-variant">No cross-document checks evaluated yet.</p>}
              </div>
            </section>

            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <h2 className="font-headline-md text-body-lg font-semibold">Missing evidence &amp; fields</h2>
              <div className="mt-3 space-y-2">
                {missingFields.slice(0, 6).map((f) => (
                  <div key={f.field_id} className="p-2 rounded-lg bg-surface-container-low flex items-center justify-between gap-2">
                    <span className="font-body-sm text-on-surface truncate">{f.label}</span>
                    <a href="/application" className="font-label-sm text-primary shrink-0">Fill →</a>
                  </div>
                ))}
                {missingFields.length === 0 && <p className="font-body-sm text-on-surface-variant">All required fields are captured.</p>}
              </div>
            </section>
          </div>

          <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5 mt-6">
            <div className="flex items-center justify-between">
              <h2 className="font-headline-md text-body-lg font-semibold">Regulatory applicability</h2>
              <AskCopilot
                context={{ kind: "analysis", label: "Regulatory applicability" }}
                prompt="Which regulations apply to my application and which are unresolved?"
                label="Ask about rules"
                className="px-2 py-1 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
              />
            </div>
            <div className="mt-3 divide-y divide-surface-container-high/60">
              {findings.map((f: Finding) => (
                <div key={f.finding_id} className="py-2 flex items-center gap-3">
                  <Badge status={f.status} />
                  <span className="font-mono text-[11px] text-on-surface-variant w-20">{f.rule_id}</span>
                  <span className="font-body-sm text-on-surface flex-1 truncate">{f.explanation}</span>
                  <span className="font-label-sm text-on-surface-variant">{f.severity}</span>
                </div>
              ))}
            </div>
            {unresolved.length > 0 && (
              <p className="font-body-sm text-on-surface-variant mt-3">
                {unresolved.length} unresolved item(s) — ask the Copilot to explain and suggest corrections.
              </p>
            )}
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}

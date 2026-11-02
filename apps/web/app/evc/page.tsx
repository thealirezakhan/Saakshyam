"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { AskCopilot } from "@/components/AskCopilot";
import { api, ensureApplication } from "@/lib/api";
import type { ApplicationSummary, EvcRecord, InfrastructureAnalysis } from "@/lib/types";

export default function EvcPage() {
  return (
    <AuthGuard>
      <Evc />
    </AuthGuard>
  );
}

function Evc() {
  const router = useRouter();
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [analysis, setAnalysis] = useState<InfrastructureAnalysis | null>(null);
  const [evc, setEvc] = useState<EvcRecord | null>(null);
  const [stage, setStage] = useState("");
  const [reason, setReason] = useState("Infrastructure evidence requires committee verification.");
  const [visitMode, setVisitMode] = useState("online");
  const [note, setNote] = useState("");
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2800);
  }

  async function load() {
    const id = await ensureApplication();
    setSummary(await api<ApplicationSummary>(`/applications/${id}`));
    const evcData = await api<{ evc: EvcRecord | null; workflow_stage: string }>(`/applications/${id}/evc`);
    setEvc(evcData.evc);
    setStage(evcData.workflow_stage);
    setAnalysis(await api<InfrastructureAnalysis>(`/applications/${id}/infrastructure/analyze`, { method: "POST" }));
  }

  useEffect(() => {
    load().catch(() => router.replace("/login"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function recommend() {
    setBusy(true);
    try {
      const id = await ensureApplication();
      const rec = await api<EvcRecord>(`/applications/${id}/evc/recommend`, {
        method: "POST",
        body: { reason, visit_mode: visitMode },
      });
      setEvc(rec);
      setStage("evc_recommended");
      flash("EVC recommendation recorded (human recommendation, not a completed visit).");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not record recommendation");
    } finally {
      setBusy(false);
    }
  }

  async function addNote() {
    if (!note.trim()) return;
    setBusy(true);
    try {
      const id = await ensureApplication();
      const rec = await api<EvcRecord>(`/applications/${id}/evc/notes`, {
        method: "POST",
        body: { note },
      });
      setEvc(rec);
      setStage("evc_notes_recorded");
      setNote("");
      flash("EVC note recorded.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not add note");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-5xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Expert Visit Committee</div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">
                Infrastructure &amp; EVC workspace
              </h1>
              <p className="font-body-md text-on-surface-variant mt-1">
                {summary?.reference_no} · {summary?.category_title} · stage {stage || "—"}
              </p>
            </div>
            <AskCopilot
              context={{ kind: "analysis", label: "Infrastructure evidence" }}
              prompt="Check whether the infrastructure evidence is sufficient."
              label="Ask about infrastructure"
            />
          </div>

          {analysis && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-md mt-5">
                <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
                  <h2 className="font-headline-md text-body-lg font-semibold">Evidence inventory</h2>
                  <div className="mt-3 space-y-2">
                    {analysis.evidence.map((e) => (
                      <div key={e.document_id} className="p-2 rounded-lg bg-surface-container-low flex items-center justify-between gap-2">
                        <span className="font-body-sm text-on-surface truncate">{e.filename}</span>
                        <Badge status={e.status} />
                      </div>
                    ))}
                    {analysis.evidence.length === 0 && <p className="font-body-sm text-on-surface-variant">No infrastructure evidence uploaded.</p>}
                  </div>
                </section>

                <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
                  <h2 className="font-headline-md text-body-lg font-semibold">Automated observations</h2>
                  <p className="font-label-sm text-on-surface-variant mt-1">Preliminary, not proof</p>
                  <ul className="mt-3 space-y-2">
                    {analysis.observations.map((o, i) => (
                      <li key={i} className="p-2 rounded-lg bg-copilot border border-copilot-border font-body-sm text-copilot-fg">{o}</li>
                    ))}
                  </ul>
                </section>

                <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
                  <h2 className="font-headline-md text-body-lg font-semibold">Gaps &amp; duplicates</h2>
                  <div className="mt-3 space-y-2 font-body-sm">
                    <div className="flex justify-between"><span className="text-on-surface-variant">Missing evidence</span><span className="font-semibold">{analysis.missing_evidence.length}</span></div>
                    <div className="flex justify-between"><span className="text-on-surface-variant">Duplicate groups</span><span className="font-semibold">{analysis.duplicate_groups.length}</span></div>
                    <div className="flex justify-between"><span className="text-on-surface-variant">EVC recommended</span><span className="font-semibold">{analysis.evc_recommended ? "Yes" : "No"}</span></div>
                  </div>
                  <p className="font-label-sm text-on-surface-variant mt-3">{analysis.disclaimer}</p>
                </section>
              </div>

              <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5 mt-5">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
                  <div>
                    <h2 className="font-headline-md text-body-lg font-semibold">Recommend EVC</h2>
                    <p className="font-label-sm text-on-surface-variant">A human recommendation; not a completed inspection.</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select value={visitMode} onChange={(e) => setVisitMode(e.target.value)} className="bg-white border border-outline-variant rounded-md px-3 py-1.5 font-body-sm">
                      <option value="online">Online</option>
                      <option value="offline">Offline</option>
                    </select>
                    <button onClick={recommend} disabled={busy} className="px-3.5 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md disabled:opacity-50">
                      Recommend / record visit
                    </button>
                  </div>
                </div>
                <input value={reason} onChange={(e) => setReason(e.target.value)} className="w-full mt-3 bg-white border border-outline-variant rounded-md px-3 py-2 font-body-sm" />
                {evc && (
                  <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-surface-container-low">
                      <div className="font-label-sm uppercase text-on-surface-variant">Status</div>
                      <div className="font-body-md font-semibold capitalize">{evc.status.replace(/_/g, " ")} · {evc.visit_mode}</div>
                      <div className="font-body-sm text-on-surface-variant mt-1">{evc.reason}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-surface-container-low">
                      <div className="font-label-sm uppercase text-on-surface-variant">Checklist</div>
                      <ul className="mt-1 space-y-1">
                        {evc.checklist.slice(0, 5).map((c, i) => (
                          <li key={i} className="font-body-sm text-on-surface flex justify-between gap-2">
                            <span className="truncate">{c.item}</span><span className="text-on-surface-variant">{c.status}</span>
                          </li>
                        ))}
                        {evc.checklist.length === 0 && <li className="font-body-sm text-on-surface-variant">No checklist items.</li>}
                      </ul>
                    </div>
                  </div>
                )}
              </section>

              <section className="bg-surface-container-lowest rounded-xl shadow-sm p-5 mt-5">
                <h2 className="font-headline-md text-body-lg font-semibold">EVC notes</h2>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Record a synthetic visit observation or additional evidence request…"
                  className="w-full mt-3 bg-white border border-outline-variant rounded-md px-3 py-2 font-body-sm"
                />
                <div className="flex justify-end mt-2">
                  <button onClick={addNote} disabled={busy || !note.trim()} className="px-3.5 py-1.5 rounded-full bg-inverse-surface text-inverse-on-surface font-label-md text-label-md disabled:opacity-50">
                    Add note
                  </button>
                </div>
                <div className="mt-4 space-y-2">
                  {(evc?.notes || []).map((n, i) => (
                    <div key={i} className="p-3 rounded-lg bg-surface-container-low">
                      <div className="font-label-sm text-on-surface-variant">{n.author} · {n.at}</div>
                      <div className="font-body-sm text-on-surface mt-1">{n.note}</div>
                    </div>
                  ))}
                  {(evc?.notes || []).length === 0 && <p className="font-body-sm text-on-surface-variant">No notes recorded yet.</p>}
                </div>
              </section>
            </>
          )}
        </div>
      </main>
      <Footer />
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg bg-inverse-surface text-inverse-on-surface shadow-utility font-body-sm max-w-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

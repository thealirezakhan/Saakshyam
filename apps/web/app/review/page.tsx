"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { api, ensureApplication } from "@/lib/api";
import type { ReviewAction, ReviewQueueItem } from "@/lib/types";

interface ReviewFinding {
  finding_id: string;
  rule_id: string;
  status: string;
  severity: string;
  lifecycle_status: string;
  human_review_required: boolean;
  explanation: string;
}

interface ReviewData {
  application_id: string;
  reference_no: string;
  workflow_stage: string;
  actions: ReviewAction[];
  findings: ReviewFinding[];
}

export default function ReviewPage() {
  return (
    <AuthGuard>
      <Review />
    </AuthGuard>
  );
}

function Review() {
  const router = useRouter();
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [data, setData] = useState<ReviewData | null>(null);
  const [finding, setFinding] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2800);
  }

  async function loadQueue() {
    const q = await api<ReviewQueueItem[]>("/review/queue");
    setQueue(q);
    if (!selected && q.length) select(q[0].application_id);
  }

  async function select(appId: string) {
    setSelected(appId);
    setFinding(null);
    setData(await api<ReviewData>(`/applications/${appId}/review`));
  }

  useEffect(() => {
    (async () => {
      try {
        await ensureApplication();
        await loadQueue();
      } catch {
        router.replace("/login");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function act(action: string) {
    if (!finding) {
      flash("Select a finding first.");
      return;
    }
    setBusy(true);
    try {
      await api(`/findings/${finding}/review/${action}`, {
        method: "POST",
        body: { note },
      });
      setNote("");
      if (selected) setData(await api<ReviewData>(`/applications/${selected}/review`));
      await loadQueue();
      flash("Review action recorded.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function recommendEvc() {
    if (!selected) return;
    setBusy(true);
    try {
      await api(`/applications/${selected}/review/recommend-evc`, {
        method: "POST",
        body: { note: note || "Reviewer recommended EVC.", visit_mode: "online" },
      });
      setNote("");
      setData(await api<ReviewData>(`/applications/${selected}/review`));
      flash("EVC recommendation recorded.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-6xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div>
            <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Scrutiny reviewer</div>
            <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">Review queue</h1>
            <p className="font-body-md text-on-surface-variant mt-1">
              Inspect findings, add observations, request evidence and recommend further review. Decisions remain human.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-md mt-5">
            <section className="bg-surface-container-lowest rounded-xl shadow-sm p-4">
              <h2 className="font-headline-md text-body-lg font-semibold">Applications</h2>
              <div className="mt-3 space-y-2">
                {queue.map((q) => (
                  <button
                    key={q.application_id}
                    onClick={() => select(q.application_id)}
                    className={
                      "w-full text-left p-3 rounded-lg border transition-colors " +
                      (selected === q.application_id
                        ? "border-primary bg-copilot"
                        : "border-outline-variant bg-surface-container-low hover:bg-surface-container")
                    }
                    type="button"
                  >
                    <div className="font-mono text-label-md text-primary">{q.reference_no}</div>
                    <div className="font-label-sm text-on-surface-variant capitalize">{q.category.replace(/_/g, " ")}</div>
                    <div className="mt-1 flex items-center gap-2 font-label-sm">
                      <span className="text-error">{q.open_findings} open</span>
                      <span className="text-on-surface-variant">· {q.human_review} human review</span>
                    </div>
                  </button>
                ))}
                {queue.length === 0 && <p className="font-body-sm text-on-surface-variant">No applications assigned.</p>}
              </div>
            </section>

            <section className="lg:col-span-2 bg-surface-container-lowest rounded-xl shadow-sm p-5">
              {data ? (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-mono text-primary">{data.reference_no}</div>
                      <div className="font-label-sm text-on-surface-variant capitalize">Stage: {data.workflow_stage.replace(/_/g, " ")}</div>
                    </div>
                    <button onClick={recommendEvc} disabled={busy} className="px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-label-md text-label-md hover:bg-surface-container disabled:opacity-50">
                      Recommend EVC
                    </button>
                  </div>

                  <div className="mt-4 space-y-2">
                    {data.findings.map((f) => (
                      <button
                        key={f.finding_id}
                        onClick={() => setFinding(f.finding_id)}
                        className={
                          "w-full text-left p-3 rounded-lg border transition-colors " +
                          (finding === f.finding_id ? "border-primary bg-copilot" : "border-outline-variant bg-surface-container-low")
                        }
                        type="button"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-[11px] text-on-surface-variant">{f.rule_id}</span>
                          <Badge status={f.status} />
                        </div>
                        <div className="font-body-sm text-on-surface mt-1">{f.explanation}</div>
                        <div className="font-label-sm text-on-surface-variant mt-1 capitalize">
                          {f.lifecycle_status} · {f.human_review_required ? "human review required" : "no manual flag"}
                        </div>
                      </button>
                    ))}
                    {data.findings.length === 0 && <p className="font-body-sm text-on-surface-variant">No findings. Run validation first.</p>}
                  </div>

                  <div className="mt-4">
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      rows={2}
                      placeholder="Observation or evidence request…"
                      className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 font-body-sm"
                    />
                    <div className="flex flex-wrap gap-2 mt-2">
                      <button onClick={() => act("observe")} disabled={busy} className="px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-label-md text-label-md disabled:opacity-50">Add observation</button>
                      <button onClick={() => act("request-evidence")} disabled={busy} className="px-3 py-1.5 rounded-full bg-pending text-pending-fg border border-pending-border font-label-md text-label-md disabled:opacity-50">Request evidence</button>
                      <button onClick={() => act("mark-manual")} disabled={busy} className="px-3 py-1.5 rounded-full bg-rejected text-rejected-fg border border-rejected-border font-label-md text-label-md disabled:opacity-50">Mark manual verification</button>
                    </div>
                  </div>

                  <div className="mt-5">
                    <h3 className="font-label-md font-semibold uppercase tracking-wide text-on-surface-variant">Review actions</h3>
                    <div className="mt-2 space-y-2">
                      {data.actions.map((a, i) => (
                        <div key={i} className="p-2.5 rounded-lg bg-surface-container-low">
                          <div className="flex items-center justify-between font-label-sm text-on-surface-variant">
                            <span className="capitalize">{a.action.replace(/_/g, " ")}</span>
                            <span>{a.at?.slice(0, 19)}</span>
                          </div>
                          {a.note && <div className="font-body-sm text-on-surface mt-1">{a.note}</div>}
                        </div>
                      ))}
                      {data.actions.length === 0 && <p className="font-body-sm text-on-surface-variant">No review actions yet.</p>}
                    </div>
                  </div>
                </>
              ) : (
                <p className="font-body-sm text-on-surface-variant">Select an application to review.</p>
              )}
            </section>
          </div>
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

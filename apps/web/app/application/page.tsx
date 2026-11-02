"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { AskCopilot } from "@/components/AskCopilot";
import { api, applicationId, currentUser, ensureApplication, setApplicationId } from "@/lib/api";
import type { ApplicationSummary, Checklist, Field, WorkflowSummary } from "@/lib/types";

export default function ApplicationPage() {
  return (
    <AuthGuard>
      <Workspace />
    </AuthGuard>
  );
}

type SaveState = "idle" | "saving" | "saved" | "error";

function Workspace() {
  const router = useRouter();
  const me = currentUser();
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [toast, setToast] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newType, setNewType] = useState("Increase in Intake / Additional Course");
  const [newCategory, setNewCategory] = useState("increase_intake");
  const [newYear, setNewYear] = useState("2027-28");
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);

  async function load() {
    const id = await ensureApplication();
    setSummary(await api<ApplicationSummary>("/applications/" + id));
    setChecklist(await api<Checklist>(`/applications/${id}/checklist`).catch(() => null));
  }
  useEffect(() => {
    load().catch(() => router.replace("/login"));
    api<WorkflowSummary[]>("/workflows").then(setWorkflows).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2600);
  }

  async function editField(field: Field, value: string) {
    if (!summary || field.locked) return;
    setSaveState("saving");
    try {
      const updated = await api<ApplicationSummary>(
        `/applications/${summary.application_id}/fields/${field.field_id}`,
        { method: "PATCH", body: { value, version: field.version } }
      );
      setSummary(updated);
      setSaveState("saved");
      setTimeout(() => setSaveState((s) => (s === "saved" ? "idle" : s)), 1800);
    } catch (e) {
      setSaveState("error");
      flash(e instanceof Error ? e.message : "Save failed");
    }
  }

  async function createApplication() {
    const inst = me?.institutions?.[0]?.institution_id;
    if (!inst) return;
    try {
      const created = await api<ApplicationSummary>("/applications", {
        method: "POST",
        body: { institution_id: inst, application_type: newType, academic_year: newYear, category: newCategory },
      });
      setApplicationId(created.application_id);
      setSummary(created);
      setChecklist(await api<Checklist>(`/applications/${created.application_id}/checklist`).catch(() => null));
      setShowNew(false);
      flash("New application created.");
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not create application");
    }
  }

  const pct = summary?.completion_pct ?? 0;

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-6xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Applications</div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">
                {summary?.reference_no || "Loading…"}
              </h1>
              <div className="flex items-center gap-2 font-label-md text-on-surface-variant mt-1 flex-wrap">
                <span className="px-2 py-0.5 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm">
                  {summary?.category_title || "Category"}
                </span>
                <span>AY {summary?.academic_year}</span>
                <span>•</span>
                <SaveIndicator state={saveState} />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowNew(true)}
                className="px-3 py-1.5 rounded-lg bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-colors"
                type="button"
              >
                New application
              </button>
              <button
                onClick={() => window.open(`/api/v1/applications/${applicationId()}/report/export`, "_blank")}
                className="px-3 py-1.5 rounded-lg bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-colors"
                type="button"
              >
                Export annexure
              </button>
              <AskCopilot context={{ kind: "section", label: summary?.reference_no }} prompt="Review my application and find issues." label="Review with Copilot" />
            </div>
          </div>

          <div className="mt-5 bg-surface-container-lowest rounded-xl shadow-sm p-4 flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
              <div className="h-full bg-secondary rounded-full transition-all" style={{ width: `${pct}%` }} />
            </div>
            <span className="font-label-md font-semibold text-on-surface w-12 text-right">{pct}%</span>
            <span className="font-label-sm text-on-surface-variant">
              {summary?.required_fields.filled}/{summary?.required_fields.total} required fields
            </span>
          </div>

          {summary && (
            <div className="mt-3 flex items-center gap-2 overflow-x-auto pb-1">
              {summary.stages.map((stage, i) => {
                const active = stage.key === summary.workflow_stage;
                const done = summary.stages.findIndex((s) => s.key === summary.workflow_stage) > i;
                return (
                  <div
                    key={stage.key}
                    className={
                      "shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border font-label-sm " +
                      (active
                        ? "bg-primary text-on-primary border-primary"
                        : done
                        ? "bg-compliant text-compliant-fg border-compliant-border"
                        : "bg-surface-container-lowest text-on-surface-variant border-outline-variant")
                    }
                  >
                    <span className="opacity-70">{i + 1}</span>
                    {stage.title}
                  </div>
                );
              })}
              <span className="shrink-0 font-label-sm text-on-surface-variant ml-2">Prototype workflow config</span>
            </div>
          )}

          {checklist && (
            <section className="mt-5 bg-surface-container-lowest rounded-xl shadow-sm p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-headline-md text-body-lg font-semibold">Document checklist</h2>
                  <p className="font-label-sm text-on-surface-variant">
                    {checklist.items.length} required · {checklist.missing} missing · category-specific
                  </p>
                </div>
                <a href="/documents" className="font-label-md text-primary">Open documents →</a>
              </div>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {checklist.items.map((item) => (
                  <div key={item.key} className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-surface-container-low">
                    <span className="font-body-sm text-on-surface capitalize truncate">
                      {item.key.replace(/_/g, " ")}
                    </span>
                    <ChecklistBadge state={item.state} />
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-space-md mt-5">
            {summary?.sections.map((s, i) => (
              <section key={s.section_id} className="bg-surface-container-lowest rounded-xl shadow-sm p-5">
                <div className="flex items-center justify-between pb-3 border-b border-surface-container-high/60">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-primary-fixed text-primary text-xs flex items-center justify-center font-bold">{i + 1}</span>
                    <span className="font-label-md text-on-surface font-semibold">{s.title}</span>
                    <span className="font-label-sm text-on-surface-variant">{s.completion}%</span>
                  </div>
                  <AskCopilot
                    context={{ kind: "section", label: s.title }}
                    prompt={`Review the “${s.title}” section of my application.`}
                    label="Ask"
                    className="px-2 py-1 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
                  />
                </div>
                <div className="space-y-2 pt-3">
                  {s.fields.map((f) => (
                    <FieldRow key={f.field_id} field={f} onSave={editField} />
                  ))}
                </div>
              </section>
            ))}
          </div>
          {!summary && <p className="text-body-sm text-on-surface-variant mt-6">Loading application record…</p>}
        </div>
      </main>
      <Footer />

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg bg-inverse-surface text-inverse-on-surface shadow-utility font-body-sm">
          {toast}
        </div>
      )}

      {showNew && (
        <div className="fixed inset-0 z-[70] bg-black/30 flex items-center justify-center p-4" onClick={() => setShowNew(false)}>
          <div className="bg-surface-container-lowest rounded-xl shadow-utility w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-headline-md font-semibold">New application</h3>
            <p className="font-body-sm text-on-surface-variant mt-1">Create a draft for this institution.</p>
            <label className="block font-label-sm uppercase tracking-wider text-on-surface-variant mt-4 mb-1">Category</label>
            <select
              value={newCategory}
              onChange={(e) => {
                setNewCategory(e.target.value);
                const w = workflows.find((x) => x.key === e.target.value);
                if (w) setNewType(w.title);
              }}
              className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 font-body-md"
            >
              {workflows.length === 0 && <option value="increase_intake">Increase in Intake / Additional Course</option>}
              {workflows.map((w) => (
                <option key={w.key} value={w.key}>{w.title}</option>
              ))}
            </select>
            <p className="font-label-sm text-on-surface-variant mt-1">
              {workflows.find((w) => w.key === newCategory)?.purpose || "Category-specific checklist and workflow."}
            </p>
            <label className="block font-label-sm uppercase tracking-wider text-on-surface-variant mt-3 mb-1">Academic year</label>
            <input
              value={newYear}
              onChange={(e) => setNewYear(e.target.value)}
              className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 font-body-md"
            />
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowNew(false)} className="px-3 py-2 rounded-lg bg-surface-container-low text-on-surface-variant text-label-md">Cancel</button>
              <button onClick={createApplication} className="px-4 py-2 rounded-lg bg-primary text-on-primary text-label-md">Create draft</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  if (state === "saving") return <span className="text-primary">Saving…</span>;
  if (state === "saved") return <span className="text-secondary">All changes saved</span>;
  if (state === "error") return <span className="text-error">Save failed</span>;
  return <span>Autosave on</span>;
}

function ChecklistBadge({ state }: { state: string }) {
  const map: Record<string, string> = {
    missing: "bg-rejected text-rejected-fg border-rejected-border",
    uploaded: "bg-compliant text-compliant-fg border-compliant-border",
    expired: "bg-rejected text-rejected-fg border-rejected-border",
    unverified: "bg-pending text-pending-fg border-pending-border",
    processing: "bg-surface-container text-on-surface-variant border-outline-variant",
  };
  const label = state === "missing" ? "Missing" : state.charAt(0).toUpperCase() + state.slice(1);
  return (
    <span className={"inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-semibold uppercase tracking-wide whitespace-nowrap " + (map[state] || map.processing)}>
      {label}
    </span>
  );
}

function FieldRow({ field, onSave }: { field: Field; onSave: (f: Field, v: string) => void }) {
  const [value, setValue] = useState(field.value || "");
  useEffect(() => setValue(field.value || ""), [field.value]);
  const filled = (field.value || "").length > 0;
  return (
    <div className="bg-surface-container-low p-3 rounded-lg">
      <div className="flex items-center justify-between">
        <span className={`font-label-sm uppercase tracking-wider font-semibold ${filled ? "text-on-surface-variant" : "text-error"}`}>
          {field.label}
        </span>
        <span className="flex items-center gap-2">
          {field.source_document_id && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-copilot text-copilot-fg border border-copilot-border text-[11px] font-semibold">
              <span className="material-symbols-outlined text-[12px]">auto_awesome</span>Evidence
            </span>
          )}
          {field.locked && (
            <span className="font-label-sm text-on-surface-variant flex items-center gap-1">
              <span className="material-symbols-outlined text-[13px]">lock</span>Locked
            </span>
          )}
        </span>
      </div>
      {field.locked ? (
        <p className="font-body-md font-medium text-on-surface mt-1">{field.value || "—"}</p>
      ) : (
        <input
          className="w-full mt-1 bg-white border border-outline-variant rounded-md px-2 py-1.5 font-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={() => value !== (field.value || "") && onSave(field, value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
        />
      )}
    </div>
  );
}

"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { PetalIcon } from "@/components/PetalIcon";
import { Badge } from "@/components/Badge";
import { api, applicationId, currentUser, loadSummary } from "@/lib/api";
import { getActiveConversation, loadMessages, sendMessage } from "@/lib/agent";
import { peekCopilotContext, takeCopilotContext, contextPrompt, type CopilotContext } from "@/lib/workspace";
import type { ApplicationSummary } from "@/lib/types";

const SUGGESTIONS = [
  "Review my entire application",
  "Find all missing documents",
  "Check faculty information against uploaded records",
  "Run complete application scrutiny",
  "Explain unresolved compliance findings",
  "Identify inconsistencies across documents",
  "Generate an internal compliance report",
  "Is my application ready for internal review?",
];

interface Turn {
  user: string;
  assistant: string;
  live: boolean;
  steps: string[];
  results: Array<{ tool: string; result: any }>;
}

export default function CopilotPage() {
  return (
    <AuthGuard>
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-on-surface-variant">Loading Copilot…</div>}>
        <Copilot />
      </Suspense>
    </AuthGuard>
  );
}

function Copilot() {
  const router = useRouter();
  const params = useSearchParams();
  const me = currentUser();
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [context, setContext] = useState<CopilotContext | null>(null);
  const [toast, setToast] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const booted = useRef(false);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2800);
  }

  useEffect(() => {
    (async () => {
      try {
        const s = await loadSummary();
        setSummary(s);
        const cid = await getActiveConversation();
        setConversationId(cid);
        const history = await loadMessages(cid);
        setTurns(buildTurns(history));
        const pending = peekCopilotContext();
        if (pending) setContext(pending);
      } catch {
        router.replace("/login");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  useEffect(() => {
    if (booted.current || !conversationId) return;
    const prompt = params.get("prompt") || contextPrompt(peekCopilotContext());
    if (prompt) {
      booted.current = true;
      const pending = takeCopilotContext();
      setContext(null);
      send(prompt, pending ?? undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  async function send(text: string, ctx?: CopilotContext) {
    if (!text.trim() || busy || !conversationId) return;
    setInput("");
    setBusy(true);
    setTurns((t) => [...t, { user: text, assistant: "", live: true, steps: [], results: [] }]);
    const activeCtx = ctx || context || null;
    try {
      await sendMessage(conversationId, text, activeCtx ? { kind: activeCtx.kind, id: activeCtx.id, label: activeCtx.label, data: activeCtx.data } : null, (event, data) => {
        setTurns((list) => {
          const next = [...list];
          const turn = { ...next[next.length - 1] };
          if (event === "message.delta") turn.assistant += data.content || "";
          else if (event === "tool.started") turn.steps = [...turn.steps, data.tool];
          else if (event === "tool.completed") turn.results = [...turn.results, { tool: data.tool, result: data.result }];
          else if (event === "proposal.staged") turn.results = [...turn.results, { tool: "proposal.staged", result: data }];
          else if (event === "message.complete") {
            turn.assistant = data.content || turn.assistant;
            turn.live = false;
          }
          next[next.length - 1] = turn;
          return next;
        });
      });
    } catch {
      setTurns((list) => {
        const next = [...list];
        const turn = { ...next[next.length - 1] };
        turn.assistant = "I couldn't reach the agent. Check that the backend is running and try again.";
        turn.live = false;
        next[next.length - 1] = turn;
        return next;
      });
    } finally {
      setBusy(false);
      setContext(null);
      loadSummary().then(setSummary).catch(() => {});
    }
  }

  async function onUpload(file: File | undefined) {
    if (!file) return;
    const fd = new FormData();
    const inst = me?.institutions?.[0]?.institution_id;
    if (inst) fd.append("institution_id", inst);
    if (applicationId()) fd.append("application_id", applicationId()!);
    fd.append("files", file);
    flash(`Uploading ${file.name}…`);
    try {
      await api("/documents/upload", { method: "POST", body: fd });
      flash(`${file.name} uploaded and indexed.`);
      send(`Review the document I just uploaded: ${file.name}`, { kind: "document", label: file.name });
    } catch {
      flash("Upload failed. Use a PDF, PNG or JPEG.");
    }
  }

  async function acceptProposal(proposal: any) {
    try {
      await api(`/copilot/proposals/${proposal.proposal_id}/apply`, { method: "POST", body: { confirm: true } });
      flash("Changes applied to the draft.");
      loadSummary().then(setSummary).catch(() => {});
    } catch (e) {
      flash(e instanceof Error ? e.message : "Could not apply changes");
    }
  }

  const empty = turns.length === 0;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <TopNav />
      <main className="flex-1 min-h-0 pt-14 flex flex-col">
        <div className="w-full max-w-4xl mx-auto flex-1 min-h-0 flex flex-col px-margin-mobile sm:px-margin">
          <div className="shrink-0 pt-6 pb-3 flex items-center justify-between gap-3">
            <div>
              <div className="inline-flex items-center gap-2 font-label-sm text-label-sm text-on-surface-variant">
                <span className="w-2 h-2 rounded-full bg-secondary" />
                Unified AI · one conversation across every workspace
              </div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight text-on-surface mt-1">
                Your AICTE Copilot
              </h1>
            </div>
            {summary && (
              <div className="text-right">
                <div className="font-mono text-label-md text-primary">{summary.reference_no}</div>
                <div className="font-label-sm text-on-surface-variant">{summary.application_type}</div>
              </div>
            )}
          </div>

          <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto pb-4 space-y-6">
            {empty && <Landing summary={summary} onPick={(s) => send(s)} />}
            {turns.map((t, i) => (
              <div key={i} className="space-y-3">
                <div className="flex justify-end">
                  <div className="max-w-[85%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-surface-container-high text-on-surface shadow-sm text-right font-body-md">
                    {t.user}
                  </div>
                </div>
                {t.steps.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pl-10">
                    {t.steps.map((s, j) => (
                      <span key={j} className="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                        {prettyTool(s)}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-full bg-secondary-fixed/40 flex-shrink-0 flex items-center justify-center text-secondary">
                    <PetalIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-body-md leading-relaxed whitespace-pre-wrap text-on-surface">
                      {t.assistant || (t.live ? "Working…" : "")}
                    </div>
                    {t.results.length > 0 && (
                      <div className="mt-3 space-y-3">
                        {t.results.map((r, j) => (
                          <ResultCard key={j} tool={r.tool} result={r.result} onAccept={acceptProposal} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="shrink-0 border-t border-surface-container-high bg-surface pt-3 pb-4">
            {context && (
              <div className="mb-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-copilot border border-copilot-border text-copilot-fg font-label-sm text-label-sm">
                <span className="material-symbols-outlined text-[14px]">attach_file</span>
                Context: {context.label || context.kind}
                <button onClick={() => setContext(null)} className="ml-1 hover:opacity-70">
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              </div>
            )}
            <div className="bg-surface-container-lowest rounded-2xl shadow-lg p-3 focus-within:shadow-xl">
              <textarea
                className="w-full bg-transparent resize-none outline-none text-on-surface placeholder:text-outline-variant font-body-md text-body-md px-1 py-1"
                placeholder="Ask anything or give me a task…"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
              />
              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => fileRef.current?.click()}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors font-label-md text-label-md"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[18px]">add</span>
                    Upload document
                  </button>
                  <input ref={fileRef} className="hidden" type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => onUpload(e.target.files?.[0])} />
                </div>
                <button
                  onClick={() => send(input)}
                  disabled={busy || !input.trim()}
                  className="w-9 h-9 rounded-full bg-primary text-on-primary hover:bg-primary-container disabled:opacity-40 flex items-center justify-center transition-all shadow-sm"
                  type="button"
                  aria-label="Send"
                >
                  <span className="material-symbols-outlined text-[19px]">arrow_upward</span>
                </button>
              </div>
            </div>
            <p className="text-center font-label-sm text-label-sm text-on-surface-variant/80 mt-2">
              One assistant · one conversation · one application context. Verify high-impact figures before submission.
            </p>
          </div>
        </div>
      </main>
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg bg-inverse-surface text-inverse-on-surface shadow-utility font-body-sm max-w-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

function Landing({ summary, onPick }: { summary: ApplicationSummary | null; onPick: (s: string) => void }) {
  return (
    <div className="pt-6">
      <div className="flex items-center gap-2 text-secondary">
        <PetalIcon className="w-6 h-6" />
        <span className="font-label-md text-label-md text-on-surface-variant">Active application</span>
      </div>
      <h2 className="font-headline-xl text-headline-xl font-semibold tracking-tight mt-2">
        What would you like to work on today?
      </h2>
      <p className="font-body-md text-body-md text-on-surface-variant mt-1 max-w-xl">
        I understand your active application, documents, evidence and compliance status. Ask anything or give me a task.
      </p>

      {summary && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
          <Mini label="Completion" value={`${summary.completion_pct}%`} />
          <Mini label="Fields captured" value={`${summary.required_fields.filled}/${summary.required_fields.total}`} />
          <Mini label="Academic year" value={summary.academic_year} />
          <Mini label="Status" value={summary.status} />
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="px-3.5 py-2 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:shadow hover:bg-surface-container-low transition-all"
            type="button"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-container-lowest rounded-lg p-3 shadow-sm">
      <div className="font-label-sm text-label-sm uppercase tracking-wide text-on-surface-variant">{label}</div>
      <div className="font-headline-md text-body-lg font-semibold text-on-surface mt-0.5 capitalize">{value}</div>
    </div>
  );
}

function prettyTool(tool: string) {
  return tool.replace(/_/g, " ");
}

function ResultCard({ tool, result, onAccept }: { tool: string; result: any; onAccept: (p: any) => void }) {
  if (!result) return null;

  if (tool === "proposal.staged" || (tool === "propose_field_updates" && result.proposal_id)) {
    const changes = result.changes || [];
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high p-4">
        <div className="flex items-center justify-between pb-2">
          <span className="font-label-md font-semibold">{changes.length} change(s) staged</span>
          <span className="px-2 py-0.5 rounded-full bg-secondary-fixed/40 text-[11px] font-semibold text-on-secondary-fixed">Ready to commit</span>
        </div>
        <div className="divide-y divide-surface-container-high/60">
          {changes.map((c: any, i: number) => (
            <div key={i} className="py-2">
              <div className="font-body-md font-semibold">{c.label}</div>
              <div className="font-body-sm text-on-surface-variant">
                <span className="line-through">{c.existing_value || "—"}</span> → <span className="font-medium text-on-surface">{c.proposed_value}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="pt-2 flex gap-2">
          <button onClick={() => onAccept(result)} className="px-3 py-1.5 rounded-lg bg-inverse-surface text-inverse-on-surface text-label-md font-medium">
            Accept changes
          </button>
          <a href="/application" className="px-3 py-1.5 rounded-lg bg-surface-container-low text-on-surface-variant text-label-md font-medium">
            Open application
          </a>
        </div>
      </div>
    );
  }

  if (result.findings && Array.isArray(result.findings)) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high overflow-hidden">
        <div className="px-4 py-2 bg-surface-container-low flex items-center justify-between">
          <span className="font-label-md font-semibold">Validation findings</span>
          <a href="/validation" className="font-label-sm text-primary">Open workspace →</a>
        </div>
        <div className="divide-y divide-surface-container-high/60">
          {result.findings.slice(0, 8).map((f: any, i: number) => (
            <div key={i} className="px-4 py-2 flex items-center gap-3">
              <Badge status={f.status} />
              <span className="font-mono text-[11px] text-on-surface-variant">{f.rule_id}</span>
              <span className="font-body-sm text-on-surface truncate flex-1">{f.explanation || f.field_key}</span>
            </div>
          ))}
          {result.findings.length === 0 && <div className="px-4 py-3 font-body-sm text-on-surface-variant">No findings.</div>}
        </div>
      </div>
    );
  }

  if (Array.isArray(result) && result.length && result[0].filename) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high overflow-hidden">
        <div className="px-4 py-2 bg-surface-container-low flex items-center justify-between">
          <span className="font-label-md font-semibold">Documents</span>
          <a href="/documents" className="font-label-sm text-primary">Open workspace →</a>
        </div>
        <div className="divide-y divide-surface-container-high/60">
          {result.slice(0, 8).map((d: any, i: number) => (
            <div key={i} className="px-4 py-2 flex items-center gap-3">
              <Badge status={d.status} />
              <span className="font-body-sm text-on-surface truncate flex-1">{d.filename}</span>
              <span className="font-label-sm text-on-surface-variant">{String(d.doc_class || "").replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.completion_pct !== undefined && result.sections) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high p-4">
        <div className="flex items-center justify-between">
          <span className="font-label-md font-semibold">Application summary</span>
          <a href="/application" className="font-label-sm text-primary">Open workspace →</a>
        </div>
        <div className="font-headline-md font-semibold mt-1">{result.completion_pct}% complete</div>
        <div className="mt-2 space-y-1">
          {result.sections.map((s: any) => (
            <div key={s.section_id} className="flex items-center gap-2">
              <span className="font-body-sm text-on-surface-variant w-44 truncate">{s.title}</span>
              <div className="flex-1 h-1.5 bg-surface-container rounded-full overflow-hidden">
                <div className="h-full bg-secondary" style={{ width: `${s.completion}%` }} />
              </div>
              <span className="font-label-sm text-on-surface-variant w-8 text-right">{s.completion}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.statuses) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high p-4">
        <div className="flex items-center justify-between">
          <span className="font-label-md font-semibold">Compliance report</span>
          <a href="/validation" className="font-label-sm text-primary">Open workspace →</a>
        </div>
        <div className="grid grid-cols-4 gap-2 mt-2">
          {Object.entries(result.statuses).map(([k, v]) => (
            <div key={k} className="text-center p-2 rounded-lg bg-surface-container-low">
              <div className="font-headline-md font-semibold">{String(v)}</div>
              <div className="font-label-sm text-on-surface-variant">{k.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.fields && Array.isArray(result.fields)) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high overflow-hidden">
        <div className="px-4 py-2 bg-surface-container-low font-label-md font-semibold">Extracted fields</div>
        <div className="divide-y divide-surface-container-high/60">
          {result.fields.map((f: any, i: number) => (
            <div key={i} className="px-4 py-2 flex items-center justify-between gap-3">
              <span className="font-body-sm text-on-surface">{f.field_name}</span>
              <span className="font-mono text-body-sm text-primary">{f.value}</span>
              <span className="font-label-sm text-on-surface-variant">p.{f.page}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.items && Array.isArray(result.items) && result.category) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high overflow-hidden">
        <div className="px-4 py-2 bg-surface-container-low flex items-center justify-between">
          <span className="font-label-md font-semibold">Document checklist</span>
          <a href="/documents" className="font-label-sm text-primary">Open documents →</a>
        </div>
        <div className="divide-y divide-surface-container-high/60">
          {result.items.map((i: any, idx: number) => (
            <div key={idx} className="px-4 py-2 flex items-center justify-between gap-3">
              <span className="font-body-sm text-on-surface capitalize">{String(i.key).replace(/_/g, " ")}</span>
              <Badge status={i.state === "uploaded" ? "PASS" : i.state} label={i.state} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.verifications && Array.isArray(result.verifications)) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high overflow-hidden">
        <div className="px-4 py-2 bg-surface-container-low font-label-md font-semibold">Simulated verification</div>
        <div className="divide-y divide-surface-container-high/60">
          {result.verifications.map((v: any, i: number) => (
            <div key={i} className="px-4 py-2 flex items-center gap-3">
              <span className="font-mono text-[11px] text-on-surface-variant">{v.request_id}</span>
              <span className="font-body-sm text-on-surface flex-1">{String(v.result).replace(/_/g, " ")}</span>
              <span className="font-label-sm text-on-surface-variant">{v.source}</span>
            </div>
          ))}
          {result.verifications.length === 0 && <div className="px-4 py-3 font-body-sm text-on-surface-variant">No verification requests yet.</div>}
        </div>
      </div>
    );
  }

  if (result.observations && Array.isArray(result.observations)) {
    return (
      <div className="bg-surface-container-lowest rounded-xl border border-surface-container-high p-4">
        <div className="flex items-center justify-between">
          <span className="font-label-md font-semibold">Infrastructure evidence review</span>
          <a href="/evc" className="font-label-sm text-primary">Open EVC →</a>
        </div>
        <ul className="mt-2 space-y-1">
          {result.observations.map((o: string, i: number) => (
            <li key={i} className="font-body-sm text-on-surface">• {o}</li>
          ))}
        </ul>
        <p className="font-label-sm text-on-surface-variant mt-2">Preliminary only; a physical inspection may be required.</p>
      </div>
    );
  }

  return null;
}

function buildTurns(history: Array<{ role: string; content: string }>): Turn[] {
  const turns: Turn[] = [];
  for (const m of history) {
    if (m.role === "user") {
      turns.push({ user: m.content, assistant: "", live: false, steps: [], results: [] });
    } else if (turns.length) {
      turns[turns.length - 1].assistant = m.content;
    }
  }
  return turns;
}

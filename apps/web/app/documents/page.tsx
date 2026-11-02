"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/AuthGuard";
import { TopNav } from "@/components/TopNav";
import { Footer } from "@/components/Footer";
import { Badge } from "@/components/Badge";
import { AskCopilot } from "@/components/AskCopilot";
import { api, applicationId, currentUser } from "@/lib/api";
import type { DocumentItem, ExtractedField, VerificationRecord } from "@/lib/types";

const FILTERS = [
  { key: "all", label: "All Documents" },
  { key: "land", label: "Land Deeds" },
  { key: "faculty", label: "Faculty Records" },
  { key: "safety", label: "Fire & Safety" },
  { key: "accounts", label: "Audited Accounts" },
];

const CLASS_GROUP: Record<string, string> = {
  land_deed: "land",
  faculty_statement: "faculty",
  fire_noc: "safety",
  building_stability: "safety",
  audited_accounts: "accounts",
};

export default function DocumentsPage() {
  return (
    <AuthGuard>
      <Documents />
    </AuthGuard>
  );
}

function Documents() {
  const router = useRouter();
  const me = currentUser();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [inspect, setInspect] = useState<{ doc: DocumentItem; fields: ExtractedField[] } | null>(null);
  const [verification, setVerification] = useState<VerificationRecord | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function load() {
    try {
      setDocs(await api<DocumentItem[]>("/documents"));
    } catch {
      /* ignore */
    }
  }
  useEffect(() => {
    load();
  }, []);

  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 2600);
  }

  const visible = docs.filter((d) => {
    if (filter !== "all" && CLASS_GROUP[d.doc_class] !== filter) return false;
    if (query && !d.filename.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  const succeeded = docs.filter((d) => d.status === "succeeded").length;
  const review = docs.filter((d) => d.status === "needs_review").length;
  const failed = docs.filter((d) => d.status === "failed").length;

  async function onUpload(file: File | undefined) {
    if (!file) return;
    const fd = new FormData();
    const inst = me?.institutions?.[0]?.institution_id;
    if (inst) fd.append("institution_id", inst);
    if (applicationId()) fd.append("application_id", applicationId()!);
    fd.append("files", file);
    setUploading(file.name);
    try {
      await api("/documents/upload", { method: "POST", body: fd });
      for (let i = 0; i < 10; i++) {
        await new Promise((r) => setTimeout(r, 600));
        const latest = await api<DocumentItem[]>("/documents");
        setDocs(latest);
        const doc = latest.find((d) => d.filename === file.name);
        if (doc && doc.status !== "processing" && doc.status !== "uploaded") break;
      }
      flash(`${file.name} processed.`);
    } catch {
      flash("Upload failed. Supported types: PDF, PNG, JPEG.");
    } finally {
      setUploading(null);
      load();
    }
  }

  async function inspectDoc(doc: DocumentItem) {
    setVerification(null);
    try {
      const payload = await api<{ fields: ExtractedField[] }>(`/documents/${doc.document_id}/fields`);
      setInspect({ doc, fields: payload.fields || [] });
    } catch {
      flash("Could not load extracted fields.");
    }
  }

  async function verifyDoc(doc: DocumentItem) {
    try {
      setVerification(await api<VerificationRecord>(`/documents/${doc.document_id}/verify`, { method: "POST" }));
    } catch (e) {
      flash(e instanceof Error ? e.message : "Verification failed");
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 pt-14">
        <div className="max-w-6xl mx-auto px-margin-mobile sm:px-margin py-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
            <div>
              <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Documents &amp; Evidence</div>
              <h1 className="font-headline-lg text-headline-lg font-semibold tracking-tight mt-1">Document intelligence</h1>
              <p className="font-body-md text-on-surface-variant mt-1">
                {docs.length} document(s) · {succeeded} extracted · {review} need review · {failed} failed
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fileRef.current?.click()}
                className="px-3.5 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md shadow-sm hover:bg-primary-container transition-colors"
                type="button"
              >
                {uploading ? "Uploading…" : "Upload document"}
              </button>
              <input ref={fileRef} className="hidden" type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => onUpload(e.target.files?.[0])} />
              <AskCopilot context={{ kind: "document", label: "All documents" }} prompt="Check my documents and evidence for missing or inconsistent items." label="Review evidence" />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3 mt-5">
            <div className="flex flex-wrap gap-2">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={
                    "px-3.5 py-1.5 rounded-full font-label-md text-label-md shadow-sm transition-all " +
                    (filter === f.key
                      ? "bg-inverse-surface text-inverse-on-surface"
                      : "bg-surface-container-lowest text-on-surface-variant hover:text-on-surface")
                  }
                  type="button"
                >
                  {f.label}
                </button>
              ))}
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documents…"
              className="sm:ml-auto w-full sm:w-64 bg-surface-container-lowest border border-outline-variant rounded-full px-3 py-1.5 font-body-sm text-on-surface focus:outline-none focus:border-primary"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-md mt-5">
            {visible.map((d, i) => (
              <div key={d.document_id} className="bg-surface-container-lowest rounded-xl p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                <div className="space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-label-sm uppercase tracking-wider text-on-surface-variant">
                      Document {String(i + 1).padStart(2, "0")}
                    </span>
                    <Badge status={d.status} />
                  </div>
                  <h3 className="font-body-md font-semibold tracking-tight break-words">{d.filename}</h3>
                  <p className="font-label-sm text-on-surface-variant">
                    {d.doc_class.replace(/_/g, " ")} · {d.extracted_fields || 0} fields
                  </p>
                </div>
                <div className="mt-4 flex items-center justify-between gap-2">
                  <button
                    onClick={() => inspectDoc(d)}
                    className="inline-flex items-center gap-1 font-label-md text-primary hover:text-primary-container"
                    type="button"
                  >
                    Inspect <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </button>
                  <AskCopilot
                    context={{ kind: "document", id: d.document_id, label: d.filename, data: { doc_class: d.doc_class } }}
                    prompt={`Review “${d.filename}” against my application and evidence.`}
                    label="Ask"
                    className="px-2 py-1 rounded-full bg-copilot text-copilot-fg border border-copilot-border font-label-sm text-label-sm"
                  />
                </div>
              </div>
            ))}
            {visible.length === 0 && (
              <div className="col-span-full text-center text-body-sm text-on-surface-variant py-10">
                No documents in this category yet. Upload one to begin extraction.
              </div>
            )}
          </div>

          <div className="mt-6 bg-surface-container-low rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-surface-container-lowest flex items-center justify-center shadow-sm text-secondary">
                <span className="material-symbols-outlined text-[24px]">document_scanner</span>
              </div>
              <div>
                <div className="font-body-md font-semibold text-on-surface">Real-time OCR pipeline</div>
                <div className="font-body-sm text-on-surface-variant">{succeeded} extracted · {review} need review · {failed} failed</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => window.open(`/api/v1/applications/${applicationId()}/report/export`, "_blank")}
                className="px-3.5 py-1.5 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-colors"
                type="button"
              >
                Download audit dossier
              </button>
              <button
                onClick={() => router.push("/validation")}
                className="px-3.5 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md shadow-sm hover:bg-primary-container transition-colors flex items-center gap-1.5"
                type="button"
              >
                Batch validate <span className="material-symbols-outlined text-[16px]">bolt</span>
              </button>
            </div>
          </div>
        </div>
      </main>
      <Footer />

      {inspect && (
        <div className="fixed inset-0 z-[70] bg-black/30 flex items-center justify-center p-4" onClick={() => setInspect(null)}>
          <div className="bg-surface-container-lowest rounded-xl shadow-utility w-full max-w-lg max-h-[75vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-3 mb-3">
              <div>
                <h3 className="font-headline-md font-semibold">{inspect.doc.filename}</h3>
                <p className="font-body-sm text-on-surface-variant">
                  {inspect.doc.doc_class.replace(/_/g, " ")} · {inspect.fields.length} extracted field(s)
                </p>
              </div>
              <button onClick={() => setInspect(null)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            {inspect.fields.length === 0 && (
              <p className="font-body-sm text-on-surface-variant">No structured fields were extracted. Manual review required.</p>
            )}
            <div className="space-y-2">
              {inspect.fields.map((f, i) => (
                <div key={i} className="p-3 rounded-lg bg-surface-container-low">
                  <div className="flex items-center justify-between">
                    <span className="font-label-md font-semibold text-on-surface">{f.field_name}</span>
                    <span className="font-label-sm text-on-surface-variant">page {f.page} · {Math.round((f.confidence || 1) * 100)}%</span>
                  </div>
                  <div className="font-mono text-body-sm text-primary mt-1">{f.value}</div>
                  <div className="font-body-sm text-on-surface-variant mt-1">“{f.text_span}”</div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <button
                onClick={() => verifyDoc(inspect.doc)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container transition-colors"
                type="button"
              >
                <span className="material-symbols-outlined text-[16px]">verified_user</span>
                Verify with issuing authority (simulated)
              </button>
              <AskCopilot
                context={{ kind: "document", id: inspect.doc.document_id, label: inspect.doc.filename }}
                prompt={`Compare “${inspect.doc.filename}” with my application fields.`}
                label="Ask Copilot about this document"
              />
            </div>

            {verification && (
              <div className="mt-4 rounded-lg border border-pending-border bg-pending/40 p-3">
                <div className="font-label-sm font-semibold text-pending-fg">{verification.banner}</div>
                <div className="mt-2 grid grid-cols-2 gap-2 font-body-sm">
                  <Field label="Request ID" value={verification.request_id} />
                  <Field label="Result" value={verification.result.replace(/_/g, " ")} />
                  <Field label="Simulated source" value={verification.source} />
                  <Field label="Reference" value={verification.reference_number || "—"} />
                  <Field label="Submitted" value={verification.submitted_value || "—"} />
                  <Field label="Returned" value={verification.returned_value || "—"} />
                  <Field label="Timestamp" value={verification.timestamp || "—"} />
                  <Field label="Manual review" value={verification.manual_review_required ? "Required" : "Not required"} />
                </div>
                <p className="font-body-sm text-on-surface mt-2">{verification.explanation}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg bg-inverse-surface text-inverse-on-surface shadow-utility font-body-sm">
          {toast}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-label-sm uppercase tracking-wide text-on-surface-variant">{label}</div>
      <div className="font-body-sm text-on-surface break-words">{value}</div>
    </div>
  );
}

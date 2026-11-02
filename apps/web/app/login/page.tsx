"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ensureApplication, login } from "@/lib/api";
import { PetalIcon } from "@/components/PetalIcon";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("inst.admin@aarohan.demo");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      await ensureApplication();
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      <div className="pointer-events-none fixed inset-x-0 top-0 h-[480px] bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(159,202,255,0.28),rgba(117,248,179,0.08),transparent_75%)] z-0" />
      <header className="fixed top-0 inset-x-0 z-50 bg-inverse-surface text-inverse-on-surface shadow-[0_1px_8px_rgba(0,0,0,0.12)]">
        <div className="h-14 max-w-7xl mx-auto px-margin-mobile lg:px-margin flex items-center">
          <span className="font-semibold tracking-tight text-body-lg">Saakshyam — AICTE Copilot</span>
        </div>
      </header>
      <main className="relative z-10 pt-24 pb-16 flex items-center justify-center px-4 min-h-screen">
        <div className="w-full max-w-md">
          <div className="bg-surface-container-lowest rounded-xl shadow-[0_12px_36px_-6px_rgba(11,28,48,0.12)] p-8 border border-outline-variant/40">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-9 h-9 rounded-lg bg-secondary flex items-center justify-center text-white">
                <PetalIcon className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-headline-md font-semibold tracking-tight">Sign in</h1>
                <p className="text-body-sm text-on-surface-variant">AICTE application workspace</p>
              </div>
            </div>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="block font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant mb-1" htmlFor="email">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 text-body-md text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  placeholder="admin@northstar.edu.in"
                />
              </div>
              <div>
                <label className="block font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant mb-1" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-outline-variant rounded-md px-3 py-2 text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  placeholder="••••••••"
                />
              </div>
              {error && <p className="text-body-sm text-error">{error}</p>}
              <button
                type="submit"
                disabled={busy}
                className="w-full h-10 rounded-md bg-primary-container hover:bg-primary text-on-primary text-body-md font-medium transition-colors disabled:opacity-60"
              >
                {busy ? "Signing in…" : "Continue"}
              </button>
            </form>
            <div className="mt-6 pt-4 border-t border-outline-variant/50 text-body-sm text-on-surface-variant">
              <p className="font-semibold mb-1">
                Demo accounts (password: <code className="font-mono">demo1234</code>)
              </p>
              <p>inst.admin@aarohan.demo · scrutiny@aicte.demo</p>
              <p>evc@aicte.demo · sysadmin@aicte.demo</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

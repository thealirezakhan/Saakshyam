"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { currentUser, clearSession } from "@/lib/api";

const NAV = [
  { path: "/copilot", label: "Copilot", key: "copilot" },
  { path: "/", label: "Overview", key: "overview" },
  { path: "/application", label: "Applications", key: "applications" },
  { path: "/documents", label: "Documents", key: "documents" },
  { path: "/validation", label: "Validation", key: "validation" },
  { path: "/analysis", label: "Analysis", key: "analysis" },
  { path: "/evc", label: "EVC", key: "evc" },
  { path: "/review", label: "Review", key: "review" },
];

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const me = currentUser();

  function logout() {
    clearSession();
    router.push("/login");
  }

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-inverse-surface text-inverse-on-surface shadow-[0_1px_8px_rgba(0,0,0,0.12)]">
      <div className="h-14 max-w-7xl mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-space-md">
        <Link href="/" className="flex items-center gap-space-sm shrink-0">
          <span className="font-semibold tracking-tight text-body-lg">Saakshyam</span>
          <span className="hidden sm:inline text-[10px] uppercase tracking-widest text-tertiary-fixed-dim">
            AICTE Copilot
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-1">
          {NAV.map((item) => {
            const active = pathname === item.path;
            return (
              <Link
                key={item.key}
                href={item.path}
                className={
                  "px-3 py-1.5 font-label-md text-label-md transition-colors rounded-full " +
                  (active
                    ? "bg-surface-variant/20 text-inverse-on-surface"
                    : "text-tertiary-fixed-dim hover:text-inverse-on-surface")
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-space-md">
          {pathname !== "/copilot" && (
            <Link
              href="/copilot"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary-fixed/20 text-secondary-fixed border border-secondary-fixed/30 hover:bg-secondary-fixed/30 transition-colors font-label-md text-label-md"
            >
              <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
              <span className="hidden sm:inline">Ask Copilot</span>
            </Link>
          )}
          <button
            onClick={logout}
            title="Sign out"
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center hover:bg-primary-container transition-colors"
            aria-label="Sign out"
          >
            <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
          </button>
        </div>
      </div>
    </header>
  );
}

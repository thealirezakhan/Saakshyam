"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { token } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!token()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center text-on-surface-variant text-body-md">
        Loading workspace…
      </div>
    );
  }
  return <>{children}</>;
}

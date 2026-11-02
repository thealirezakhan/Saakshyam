import type { ApplicationSummary, LoginResponse } from "./types";

const TOKEN_KEY = "aicte_token";
const USER_KEY = "aicte_user";
const APP_KEY = "aicte_application";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export const token = () =>
  typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);

export const currentUser = (): LoginResponse | null => {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
};

export const applicationId = () =>
  typeof window === "undefined" ? null : localStorage.getItem(APP_KEY);

export function canRunValidation(): boolean {
  const me = currentUser();
  return !!me?.institutions?.some((i) => i.permissions?.includes("validation.run"));
}

export function canManageReview(): boolean {
  const me = currentUser();
  return !!me?.institutions?.some(
    (i) => i.permissions?.includes("review.manage") || i.permissions?.includes("evc.manage")
  );
}

export function setSession(res: LoginResponse) {
  localStorage.setItem(TOKEN_KEY, res.token);
  localStorage.setItem(USER_KEY, JSON.stringify(res));
}

export function setApplicationId(id: string) {
  localStorage.setItem(APP_KEY, id);
}

export function clearSession() {
  localStorage.clear();
}

export type ApiOptions = Omit<RequestInit, "body"> & { body?: unknown };

export async function api<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as Record<string, string>) };
  const t = token();
  if (t) headers.Authorization = "Bearer " + t;
  let body = opts.body as BodyInit | undefined;
  if (opts.body && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  const res = await fetch("/api/v1" + path, { ...opts, headers, body });
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    const message = payload?.error?.message || payload?.detail || res.statusText;
    throw new ApiError(message, res.status);
  }
  return (payload && "data" in payload ? payload.data : payload) as T;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await api<LoginResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
  setSession(res);
  localStorage.removeItem(APP_KEY);
  return res;
}

export async function ensureApplication(): Promise<string> {
  const existing = applicationId();
  if (existing) {
    try {
      await api("/applications/" + existing);
      return existing;
    } catch {
      /* stale id (e.g. demo database reset) — fall through and reselect */
    }
  }
  const apps = await api<Array<{ application_id: string }>>("/applications");
  if (!apps.length) throw new ApiError("No application available", 404);
  setApplicationId(apps[0].application_id);
  return apps[0].application_id;
}

export async function loadSummary(): Promise<ApplicationSummary> {
  const id = await ensureApplication();
  return api<ApplicationSummary>("/applications/" + id);
}

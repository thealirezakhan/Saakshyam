export type ContextKind = "document" | "finding" | "section" | "analysis" | "overview";

export interface CopilotContext {
  kind: ContextKind;
  id?: string;
  label?: string;
  data?: Record<string, unknown>;
}

const KEY = "aicte_copilot_context";

export function setCopilotContext(ctx: CopilotContext) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(ctx));
}

export function peekCopilotContext(): CopilotContext | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(sessionStorage.getItem(KEY) || "null");
  } catch {
    return null;
  }
}

export function takeCopilotContext(): CopilotContext | null {
  const ctx = peekCopilotContext();
  if (typeof window !== "undefined") sessionStorage.removeItem(KEY);
  return ctx;
}

export function contextPrompt(ctx: CopilotContext | null): string {
  if (!ctx) return "";
  switch (ctx.kind) {
    case "document":
      return `Review document “${ctx.label}” in the context of my application.`;
    case "finding":
      return `Explain finding ${ctx.id} and how to resolve it.`;
    case "section":
      return `Review the “${ctx.label}” section of my application.`;
    case "analysis":
      return `Explain the current analytical result${ctx.label ? `: ${ctx.label}` : ""}.`;
    default:
      return "What needs my attention in my application right now?";
  }
}

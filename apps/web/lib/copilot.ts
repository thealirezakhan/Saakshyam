import { applicationId, token } from "./api";

export type SseHandlers = Record<string, (data: any) => void>;

export async function getConversation(appId: string): Promise<string> {
  const cacheKey = "aicte_conv_" + appId;
  const cached = typeof window !== "undefined" ? sessionStorage.getItem(cacheKey) : null;
  if (cached) return cached;
  const res = await fetch("/api/v1/copilot/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token() },
    body: JSON.stringify({ application_id: appId }),
  });
  const payload = await res.json();
  const id = payload?.data?.conversation_id;
  if (typeof window !== "undefined" && id) sessionStorage.setItem(cacheKey, id);
  return id;
}

export async function sendMessage(conversationId: string, content: string, handlers: SseHandlers) {
  const res = await fetch(`/api/v1/copilot/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token() },
    body: JSON.stringify({ content }),
  });
  if (!res.ok || !res.body) throw new Error("Copilot request failed");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let event = "message";
      let data: any = {};
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) {
          try {
            data = JSON.parse(line.slice(5).trim());
          } catch {
            /* ignore */
          }
        }
      }
      handlers[event]?.(data);
      handlers["*"]?.(data);
    }
  }
}

export async function conversationForCurrentApp(): Promise<string> {
  const appId = applicationId();
  if (!appId) throw new Error("No application selected");
  return getConversation(appId);
}

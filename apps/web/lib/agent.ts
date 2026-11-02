import { api, applicationId, ensureApplication, token } from "./api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  at?: string;
}

export interface AgentEvent {
  event: string;
  data: any;
}

export async function getActiveConversation(): Promise<string> {
  await ensureApplication();
  const res = await api<{ conversation_id: string }>(
    `/copilot/conversations/active?application_id=${applicationId()}`
  );
  return res.conversation_id;
}

export async function loadMessages(conversationId: string): Promise<ChatMessage[]> {
  return api<ChatMessage[]>(`/copilot/conversations/${conversationId}/messages`);
}

export type EventHandler = (event: string, data: any) => void;

export async function sendMessage(
  conversationId: string,
  content: string,
  context: Record<string, unknown> | null,
  onEvent: EventHandler
): Promise<void> {
  const res = await fetch(`/api/v1/copilot/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token() },
    body: JSON.stringify({ content, context }),
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
      onEvent(event, data);
    }
  }
}

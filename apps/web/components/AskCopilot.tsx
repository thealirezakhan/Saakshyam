"use client";

import { useRouter } from "next/navigation";
import { setCopilotContext, type CopilotContext } from "@/lib/workspace";

export function AskCopilot({
  context,
  prompt,
  label = "Ask Copilot",
  className,
}: {
  context: CopilotContext;
  prompt?: string;
  label?: string;
  className?: string;
}) {
  const router = useRouter();
  return (
    <button
      type="button"
      onClick={() => {
        setCopilotContext(context);
        router.push(prompt ? `/copilot?prompt=${encodeURIComponent(prompt)}` : "/copilot");
      }}
      className={
        className ||
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-copilot text-copilot-fg border border-copilot-border hover:bg-copilot/70 transition-colors font-label-md text-label-md"
      }
    >
      <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
      {label}
    </button>
  );
}

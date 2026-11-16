"use client";

import { Citation } from "@/lib/api";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  relevanceStatus?: string | null;
  loopCount?: number;
  latencyMs?: number | null;
  isStreaming?: boolean;
}

export default function ChatMessage({
  role,
  content,
  citations,
  relevanceStatus,
  loopCount,
  latencyMs,
  isStreaming,
}: ChatMessageProps) {
  return (
    <div
      className={`flex gap-3 px-4 py-5 ${
        role === "user" ? "bg-zinc-950" : "bg-zinc-900/50"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
          role === "user"
            ? "bg-blue-600 text-white"
            : "bg-emerald-600 text-white"
        }`}
      >
        {role === "user" ? "U" : "AI"}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1 space-y-3">
        <div className="text-sm leading-relaxed text-zinc-200 whitespace-pre-wrap">
          {content}
          {isStreaming && (
            <span className="ml-1 inline-block h-4 w-1.5 animate-pulse bg-blue-400" />
          )}
        </div>

        {/* Citations */}
        {citations && citations.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
              Sources
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {citations.map((c, i) => (
                <div
                  key={c.chunk_id || i}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 p-3"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-emerald-400">
                      📄 {c.source}
                    </span>
                    <span className="text-xs text-zinc-600">
                      Score: {(c.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 line-clamp-3">
                    {c.preview}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        {role === "assistant" && !isStreaming && (
          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-600">
            {relevanceStatus && (
              <span
                className={`rounded-full px-2 py-0.5 ${
                  relevanceStatus === "relevant"
                    ? "bg-emerald-950 text-emerald-400"
                    : relevanceStatus === "fallback"
                    ? "bg-amber-950 text-amber-400"
                    : "bg-zinc-800 text-zinc-400"
                }`}
              >
                {relevanceStatus === "relevant"
                  ? "✅ Grounded"
                  : relevanceStatus === "fallback"
                  ? "🌐 Web Fallback"
                  : relevanceStatus}
              </span>
            )}
            {(loopCount ?? 0) > 0 && (
              <span>🔄 {loopCount} rewrite(s)</span>
            )}
            {latencyMs != null && (
              <span>⚡ {latencyMs.toFixed(0)}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

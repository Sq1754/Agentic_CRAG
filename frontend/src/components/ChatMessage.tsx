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
  if (role === "user") {
    return (
      <div className="mb-6 flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-3 text-sm text-white leading-relaxed shadow-lg shadow-blue-600/10">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 flex gap-3">
      {/* AI avatar */}
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 shadow-md shadow-violet-500/20 mt-0.5">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1L11 3.5V8.5L6 11L1 8.5V3.5L6 1Z" stroke="white" strokeWidth="1.2" fill="none"/>
          <circle cx="6" cy="6" r="1.5" fill="white" opacity="0.7"/>
        </svg>
      </div>

      <div className="min-w-0 flex-1 space-y-3">
        {/* Content */}
        <div className="text-sm leading-relaxed text-zinc-200 whitespace-pre-wrap">
          {isStreaming && !content ? (
            <div className="flex items-center gap-1.5 py-1">
              <div className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <div className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <div className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          ) : (
            <>
              {content}
              {isStreaming && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-blue-400 align-middle" />
              )}
            </>
          )}
        </div>

        {/* Citations */}
        {citations && citations.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
              Sources
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {citations.map((c, i) => (
                <div
                  key={c.chunk_id || i}
                  className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 hover:border-white/[0.12] transition-colors"
                >
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-medium text-emerald-400">
                      {c.source}
                    </span>
                    <span className="shrink-0 rounded-full bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-500">
                      {(c.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 line-clamp-3 leading-relaxed">
                    {c.preview}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata badges */}
        {!isStreaming && (
          <div className="flex flex-wrap items-center gap-2">
            {relevanceStatus && (
              <span
                className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                  relevanceStatus === "relevant"
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                    : relevanceStatus === "fallback"
                    ? "border-amber-500/20 bg-amber-500/10 text-amber-400"
                    : "border-zinc-700 bg-zinc-800 text-zinc-400"
                }`}
              >
                {relevanceStatus === "relevant" ? (
                  <>
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12">
                      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                    Grounded
                  </>
                ) : relevanceStatus === "fallback" ? (
                  <>
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12">
                      <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                      <path d="M4 6h4M6 4v4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                    </svg>
                    Web Fallback
                  </>
                ) : relevanceStatus}
              </span>
            )}
            {(loopCount ?? 0) > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full border border-zinc-800 bg-zinc-900 px-2.5 py-0.5 text-xs text-zinc-500">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12">
                  <path d="M10 6a4 4 0 1 1-4-4" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                  <path d="M10 2v4H6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                </svg>
                {loopCount} rewrite{(loopCount ?? 0) !== 1 ? "s" : ""}
              </span>
            )}
            {latencyMs != null && (
              <span className="text-[10px] text-zinc-700">
                {latencyMs < 1000 ? `${latencyMs.toFixed(0)}ms` : `${(latencyMs / 1000).toFixed(1)}s`}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

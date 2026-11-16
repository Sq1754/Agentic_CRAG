"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <main className="flex flex-col items-center justify-center px-4 py-24">
      {/* Hero */}
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl">
          <span className="text-blue-400">AI</span> Knowledge Base
          <br />
          for Teams
        </h1>
        <p className="text-lg text-zinc-400 leading-relaxed">
          Upload your documents. Ask natural language questions.
          Get <span className="text-emerald-400 font-medium">accurate, cited answers</span> powered
          by self-correcting Agentic RAG with hallucination detection.
        </p>

        <div className="flex justify-center gap-4 pt-2">
          {user ? (
            <Link
              href="/dashboard"
              className="rounded-xl bg-blue-600 px-8 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition shadow-lg shadow-blue-600/20"
            >
              Go to Dashboard →
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="rounded-xl bg-blue-600 px-8 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition shadow-lg shadow-blue-600/20"
              >
                Get Started Free →
              </Link>
              <Link
                href="/login"
                className="rounded-xl border border-zinc-700 px-8 py-3 text-sm font-medium text-zinc-300 hover:bg-zinc-900 transition"
              >
                Login
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="mt-24 grid max-w-4xl gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[
          {
            icon: "🔍",
            title: "Hybrid Search",
            desc: "Dense vectors + BM25 keyword search fused with Reciprocal Rank Fusion for best-in-class retrieval.",
          },
          {
            icon: "🛡️",
            title: "Self-Correcting AI",
            desc: "Documents graded for relevance. Queries rewritten automatically. Hallucinations detected and blocked.",
          },
          {
            icon: "🌐",
            title: "Web Fallback",
            desc: "When internal docs lack the answer, the agent searches the web automatically instead of fabricating.",
          },
          {
            icon: "📄",
            title: "Multi-Format Upload",
            desc: "Upload PDF, DOCX, Markdown, or plain text. Documents are parsed, chunked, and indexed automatically.",
          },
          {
            icon: "🏢",
            title: "Team Workspaces",
            desc: "Multi-tenant workspaces with role-based access. Each team's data is fully isolated.",
          },
          {
            icon: "⚡",
            title: "Real-Time Streaming",
            desc: "Watch the AI think in real-time. See each retrieval step, rewrite, and generation as it happens.",
          },
        ].map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-2"
          >
            <div className="text-2xl">{f.icon}</div>
            <h3 className="text-sm font-semibold text-white">{f.title}</h3>
            <p className="text-xs text-zinc-500 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Footer Tagline */}
      <p className="mt-24 text-xs text-zinc-700">
        Built with LangGraph • FastAPI • Qdrant • Next.js
      </p>
    </main>
  );
}

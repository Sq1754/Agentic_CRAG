"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

const features = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 3L17 7V13L10 17L3 13V7L10 3Z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
        <circle cx="10" cy="10" r="2" fill="currentColor" opacity="0.5"/>
      </svg>
    ),
    color: "from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400",
    title: "Hybrid Search",
    desc: "Dense vectors + BM25 keyword search fused with Reciprocal Rank Fusion for best-in-class retrieval accuracy.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2C5.58 2 2 5.58 2 10s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
        <path d="M7 10l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    color: "from-violet-500/20 to-violet-600/10 border-violet-500/20 text-violet-400",
    title: "Self-Correcting AI",
    desc: "Documents graded for relevance. Queries rewritten automatically. Hallucinations detected and blocked.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" fill="none"/>
        <path d="M10 6v4l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    color: "from-emerald-500/20 to-emerald-600/10 border-emerald-500/20 text-emerald-400",
    title: "Web Fallback",
    desc: "When internal docs lack the answer, the agent searches the web automatically — never fabricates.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M4 4h12v12H4z" stroke="currentColor" strokeWidth="1.5" fill="none" rx="2"/>
        <path d="M8 8h4M8 11h4M8 14h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    ),
    color: "from-amber-500/20 to-amber-600/10 border-amber-500/20 text-amber-400",
    title: "Multi-Format Upload",
    desc: "Upload PDF, DOCX, Markdown, or plain text. Parsed, chunked, and indexed automatically.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2L4 5v5c0 4.4 2.6 8.5 6 10 3.4-1.5 6-5.6 6-10V5L10 2z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
      </svg>
    ),
    color: "from-pink-500/20 to-pink-600/10 border-pink-500/20 text-pink-400",
    title: "Team Workspaces",
    desc: "Multi-tenant workspaces with role-based access. Each team's data is fully isolated.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 3v14M3 10h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="1.5" fill="none"/>
      </svg>
    ),
    color: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/20 text-cyan-400",
    title: "Real-Time Streaming",
    desc: "Watch the AI think live. See each retrieval step, rewrite, and generation as it happens.",
  },
];

const stack = ["LangGraph", "FastAPI", "Qdrant", "Next.js", "PostgreSQL", "sentence-transformers"];

export default function HomePage() {
  const { user } = useAuth();

  return (
    <main className="hero-bg relative overflow-hidden">
      {/* Decorative grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center px-4 pt-28 pb-20 text-center">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-xs font-medium text-blue-400">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
          Agentic CRAG · Self-Correcting AI
        </div>

        <h1 className="max-w-3xl text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl leading-[1.08]">
          Your documents,{" "}
          <span className="gradient-text">actually understood</span>
        </h1>

        <p className="mt-6 max-w-xl text-lg text-zinc-400 leading-relaxed">
          Upload any document. Ask anything in natural language.
          Get <span className="text-white font-medium">accurate, cited answers</span> with
          hallucination detection built in.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-3">
          {user ? (
            <Link
              href="/dashboard"
              className="group flex items-center gap-2 rounded-xl bg-blue-600 px-7 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-500 hover:shadow-blue-500/40 transition-all duration-200"
            >
              Go to Dashboard
              <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 16 16">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="group flex items-center gap-2 rounded-xl bg-blue-600 px-7 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-500 hover:shadow-blue-500/40 transition-all duration-200"
              >
                Get Started Free
                <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 16 16">
                  <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </Link>
              <Link
                href="/login"
                className="rounded-xl border border-zinc-700/70 px-7 py-3 text-sm font-medium text-zinc-300 hover:border-zinc-500 hover:text-white hover:bg-white/[0.04] transition-all duration-200"
              >
                Sign In
              </Link>
            </>
          )}
        </div>

        {/* Stats row */}
        <div className="mt-16 flex flex-wrap justify-center gap-8 text-sm">
          {[
            { label: "Retrieval Strategy", value: "Hybrid RRF" },
            { label: "Hallucination Guard", value: "Built-in" },
            { label: "Supported Formats", value: "PDF · DOCX · MD · TXT" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="font-semibold text-white">{s.value}</div>
              <div className="mt-0.5 text-xs text-zinc-600">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Feature Grid ──────────────────────────────────────────────── */}
      <section className="relative mx-auto max-w-5xl px-4 pb-24">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold text-white">Everything you need</h2>
          <p className="mt-2 text-sm text-zinc-500">Built on production-grade AI infrastructure</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className={`group relative rounded-2xl border bg-gradient-to-br p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl ${f.color}`}
            >
              <div className={`mb-4 inline-flex rounded-xl p-2.5 bg-gradient-to-br ${f.color}`}>
                {f.icon}
              </div>
              <h3 className="mb-1.5 text-sm font-semibold text-white">{f.title}</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Stack ─────────────────────────────────────────────────────── */}
      <section className="relative border-t border-white/[0.05] py-10">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-x-8 gap-y-3 px-4">
          <span className="text-xs font-medium text-zinc-600 uppercase tracking-wider">Built with</span>
          {stack.map((s) => (
            <span key={s} className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors">
              {s}
            </span>
          ))}
        </div>
      </section>
    </main>
  );
}

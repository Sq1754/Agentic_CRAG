"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Workspace, listWorkspaces, createWorkspace } from "@/lib/api";

function WorkspaceCard({ ws, onClick }: { ws: Workspace; onClick: () => void }) {
  const initials = ws.name.slice(0, 2).toUpperCase();
  const colors = [
    "from-blue-500 to-violet-600",
    "from-emerald-500 to-cyan-600",
    "from-orange-500 to-pink-600",
    "from-violet-500 to-pink-600",
    "from-cyan-500 to-blue-600",
    "from-pink-500 to-rose-600",
  ];
  const colorIdx = ws.name.charCodeAt(0) % colors.length;

  return (
    <button
      onClick={onClick}
      className="group relative w-full text-left rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 hover:border-white/[0.14] hover:bg-white/[0.05] transition-all duration-200"
    >
      {/* Hover glow */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{ background: "radial-gradient(circle at 50% 0%, rgba(59,130,246,0.06), transparent 70%)" }} />

      <div className="relative flex items-start gap-4">
        {/* Avatar */}
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${colors[colorIdx]} text-sm font-bold text-white shadow-lg`}>
          {initials}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="truncate text-sm font-semibold text-white">{ws.name}</h3>
            <svg className="h-4 w-4 shrink-0 text-zinc-700 group-hover:text-zinc-400 group-hover:translate-x-0.5 transition-all" fill="none" viewBox="0 0 16 16">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          {ws.description && (
            <p className="mt-1 text-xs text-zinc-500 line-clamp-2 leading-relaxed">{ws.description}</p>
          )}
          <div className="mt-3 flex items-center gap-3 text-xs text-zinc-700">
            <span className="flex items-center gap-1">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12">
                <circle cx="6" cy="4" r="2" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                <path d="M2 10c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
              </svg>
              {ws.member_count} member{ws.member_count !== 1 ? "s" : ""}
            </span>
            <span>·</span>
            <span>{new Date(ws.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>
          </div>
        </div>
      </div>
    </button>
  );
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      listWorkspaces()
        .then(setWorkspaces)
        .finally(() => setLoading(false));
    }
  }, [user]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const ws = await createWorkspace(newName.trim(), newDesc.trim());
      setWorkspaces((prev) => [ws, ...prev]);
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
    } finally {
      setCreating(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workspaces</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {workspaces.length > 0
              ? `${workspaces.length} workspace${workspaces.length !== 1 ? "s" : ""}`
              : "Create a workspace to start querying your documents"}
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-600/20 hover:bg-blue-500 transition-all"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 16 16">
            <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          New Workspace
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 space-y-3"
        >
          <h2 className="text-sm font-semibold text-white mb-4">New Workspace</h2>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Workspace name  (e.g. Engineering Docs)"
            required
            autoFocus
            className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30 transition-all"
          />
          <input
            type="text"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30 transition-all"
          />
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={creating}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-all"
            >
              {creating ? (
                <>
                  <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                  </svg>
                  Creating…
                </>
              ) : "Create"}
            </button>
            <button
              type="button"
              onClick={() => { setShowCreate(false); setNewName(""); setNewDesc(""); }}
              className="rounded-xl border border-white/[0.08] px-5 py-2.5 text-sm text-zinc-500 hover:text-zinc-300 hover:border-white/[0.14] transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-24">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : workspaces.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.08] py-24 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.04] border border-white/[0.08]">
            <svg className="h-6 w-6 text-zinc-600" fill="none" viewBox="0 0 24 24">
              <path d="M19 11H5M19 11a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2M19 11V9a2 2 0 0 0-2-2M5 11V9a2 2 0 0 1 2-2m0 0V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2M7 7h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <p className="text-sm font-medium text-zinc-400">No workspaces yet</p>
          <p className="mt-1 text-xs text-zinc-600">Create one above to start uploading documents</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {workspaces.map((ws) => (
            <WorkspaceCard
              key={ws.id}
              ws={ws}
              onClick={() => router.push(`/dashboard/${ws.id}`)}
            />
          ))}
        </div>
      )}
    </main>
  );
}

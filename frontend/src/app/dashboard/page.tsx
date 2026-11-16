"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  Workspace,
  listWorkspaces,
  createWorkspace,
} from "@/lib/api";

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
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Workspaces</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Create a workspace and upload documents to start querying.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 transition"
        >
          + New Workspace
        </button>
      </div>

      {/* Create Workspace Form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-8 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3"
        >
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Workspace name (e.g. Engineering Docs)"
            required
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-200 outline-none focus:border-blue-500"
          />
          <input
            type="text"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-200 outline-none focus:border-blue-500"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {creating ? "Creating..." : "Create"}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-800"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Workspace Cards */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : workspaces.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-12 text-center">
          <p className="text-3xl mb-3">🏢</p>
          <p className="text-sm text-zinc-400">
            No workspaces yet. Create one to get started!
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {workspaces.map((ws) => (
            <div
              key={ws.id}
              onClick={() => router.push(`/dashboard/${ws.id}`)}
              className="cursor-pointer rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 hover:border-zinc-600 hover:bg-zinc-900 transition space-y-2"
            >
              <h3 className="text-base font-semibold text-white">{ws.name}</h3>
              {ws.description && (
                <p className="text-xs text-zinc-500 line-clamp-2">
                  {ws.description}
                </p>
              )}
              <div className="flex items-center gap-3 text-xs text-zinc-600">
                <span>👥 {ws.member_count} member(s)</span>
                <span>
                  Created {new Date(ws.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

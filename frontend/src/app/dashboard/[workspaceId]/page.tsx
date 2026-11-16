"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import {
  Document,
  Workspace,
  getWorkspace,
  listDocuments,
  deleteDocument,
} from "@/lib/api";
import DocumentUpload from "@/components/DocumentUpload";

export default function WorkspacePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  const loadData = async () => {
    try {
      const [ws, docs] = await Promise.all([
        getWorkspace(workspaceId),
        listDocuments(workspaceId),
      ]);
      setWorkspace(ws);
      setDocuments(docs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) loadData();
  }, [user, workspaceId]);

  const handleDelete = async (docId: string) => {
    if (!confirm("Delete this document?")) return;
    await deleteDocument(workspaceId, docId);
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  };

  if (authLoading || loading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
        <Link href="/dashboard" className="hover:text-zinc-300">
          Workspaces
        </Link>
        <span>/</span>
        <span className="text-zinc-200">{workspace?.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{workspace?.name}</h1>
          {workspace?.description && (
            <p className="text-sm text-zinc-500 mt-1">
              {workspace.description}
            </p>
          )}
        </div>
        <Link
          href={`/dashboard/${workspaceId}/chat`}
          className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-500 transition flex items-center gap-2"
        >
          💬 Open Chat
        </Link>
      </div>

      {/* Upload */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">
          Upload Documents
        </h2>
        <DocumentUpload workspaceId={workspaceId} onUploaded={loadData} />
      </div>

      {/* Document List */}
      <div>
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">
          Indexed Documents ({documents.length})
        </h2>
        {documents.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-8 text-center">
            <p className="text-sm text-zinc-500">
              No documents yet. Upload a file above to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-lg">
                    {doc.file_type === "pdf"
                      ? "📕"
                      : doc.file_type === "docx"
                      ? "📘"
                      : doc.file_type === "md"
                      ? "📗"
                      : "📄"}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm text-zinc-200 truncate">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-zinc-600">
                      {doc.chunk_count} chunks •{" "}
                      {doc.file_size
                        ? `${(doc.file_size / 1024).toFixed(0)} KB`
                        : "—"}{" "}
                      • {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      doc.status === "ready"
                        ? "bg-emerald-950 text-emerald-400"
                        : doc.status === "processing"
                        ? "bg-amber-950 text-amber-400"
                        : "bg-red-950 text-red-400"
                    }`}
                  >
                    {doc.status}
                  </span>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-xs text-zinc-600 hover:text-red-400 transition"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

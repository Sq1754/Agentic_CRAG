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

const FILE_ICONS: Record<string, { icon: string; color: string }> = {
  pdf: { icon: "PDF", color: "bg-red-500/20 text-red-400 border-red-500/20" },
  docx: { icon: "DOC", color: "bg-blue-500/20 text-blue-400 border-blue-500/20" },
  md: { icon: "MD", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/20" },
  txt: { icon: "TXT", color: "bg-zinc-500/20 text-zinc-400 border-zinc-500/20" },
};

const STATUS_STYLES: Record<string, string> = {
  ready: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  processing: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
};

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
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      {/* Breadcrumb */}
      <div className="mb-6 flex items-center gap-2 text-sm">
        <Link href="/dashboard" className="text-zinc-600 hover:text-zinc-300 transition-colors">
          Workspaces
        </Link>
        <svg className="h-3 w-3 text-zinc-700" fill="none" viewBox="0 0 12 12">
          <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span className="text-zinc-300">{workspace?.name}</span>
      </div>

      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">{workspace?.name}</h1>
          {workspace?.description && (
            <p className="mt-1 text-sm text-zinc-500">{workspace.description}</p>
          )}
          <div className="mt-3 flex items-center gap-4 text-xs text-zinc-600">
            <span>{documents.length} document{documents.length !== 1 ? "s" : ""}</span>
            <span>·</span>
            <span>{workspace?.member_count} member{(workspace?.member_count ?? 0) !== 1 ? "s" : ""}</span>
          </div>
        </div>
        <Link
          href={`/dashboard/${workspaceId}/chat`}
          className="flex shrink-0 items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-600/20 hover:from-emerald-500 hover:to-cyan-500 transition-all duration-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 16 16">
            <path d="M14 10c0 .6-.5 1-1 1H4l-3 3V3c0-.6.5-1 1-1h11c.6 0 1 .4 1 1v7z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
          </svg>
          Open Chat
        </Link>
      </div>

      {/* Upload section */}
      <div className="mb-8 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6">
        <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-zinc-300">
          <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 16 16">
            <path d="M8 1v10M4 5l4-4 4 4M2 13h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Upload Documents
        </h2>
        <DocumentUpload workspaceId={workspaceId} onUploaded={loadData} />
      </div>

      {/* Document list */}
      <div>
        <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-zinc-300">
          <svg className="h-4 w-4 text-zinc-500" fill="none" viewBox="0 0 16 16">
            <path d="M3 2h7l3 3v9H3V2z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
            <path d="M10 2v3h3M5 7h6M5 10h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          Indexed Documents
          <span className="ml-auto rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-normal text-zinc-500">{documents.length}</span>
        </h2>

        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.07] py-14 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-white/[0.04] border border-white/[0.07]">
              <svg className="h-5 w-5 text-zinc-600" fill="none" viewBox="0 0 20 20">
                <path d="M4 4h7l4 4v8H4V4z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M11 4v4h4" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <p className="text-sm text-zinc-500">No documents yet</p>
            <p className="mt-1 text-xs text-zinc-700">Upload a file above to index it</p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => {
              const fi = FILE_ICONS[doc.file_type] ?? FILE_ICONS.txt;
              const st = STATUS_STYLES[doc.status] ?? STATUS_STYLES.failed;
              return (
                <div
                  key={doc.id}
                  className="group flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3.5 hover:border-white/[0.1] hover:bg-white/[0.04] transition-all"
                >
                  {/* File type badge */}
                  <span className={`inline-flex shrink-0 items-center rounded-lg border px-2 py-1 text-[10px] font-bold tracking-wider ${fi.color}`}>
                    {fi.icon}
                  </span>

                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-zinc-200 font-medium">{doc.filename}</p>
                    <p className="mt-0.5 text-xs text-zinc-600">
                      {doc.chunk_count} chunks
                      {doc.file_size ? ` · ${(doc.file_size / 1024).toFixed(0)} KB` : ""}
                      {" · "}{new Date(doc.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </p>
                  </div>

                  {/* Status */}
                  <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${st}`}>
                    {doc.status}
                  </span>

                  {/* Delete */}
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="shrink-0 rounded-lg p-1.5 text-zinc-700 hover:bg-red-500/10 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete document"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 16 16">
                      <path d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5M3 4l1 10h8l1-10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}

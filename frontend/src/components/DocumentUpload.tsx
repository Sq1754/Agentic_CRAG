"use client";

import { useState, useCallback } from "react";
import { uploadDocument } from "@/lib/api";

interface DocumentUploadProps {
  workspaceId: string;
  onUploaded: () => void;
}

export default function DocumentUpload({ workspaceId, onUploaded }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleUpload = useCallback(async (file: File) => {
    setError("");
    setSuccess("");
    setUploading(true);
    try {
      await uploadDocument(workspaceId, file);
      setSuccess(`"${file.name}" uploaded and indexed successfully`);
      onUploaded();
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [workspaceId, onUploaded]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  };

  return (
    <div>
      <label
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-200 ${
          uploading
            ? "border-blue-500/40 bg-blue-500/5 cursor-wait"
            : dragOver
            ? "border-blue-500 bg-blue-500/10 scale-[1.01]"
            : "border-white/[0.08] bg-white/[0.01] hover:border-white/[0.15] hover:bg-white/[0.03]"
        }`}
      >
        {uploading ? (
          <>
            <div className="relative flex h-12 w-12 items-center justify-center">
              <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-blue-500" />
              <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 20 20">
                <path d="M4 4h7l4 4v8H4V4z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <path d="M11 4v4h4" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-300">Processing document…</p>
              <p className="mt-0.5 text-xs text-zinc-600">Parsing, chunking, and indexing</p>
            </div>
          </>
        ) : (
          <>
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl border transition-all ${
              dragOver
                ? "border-blue-500/40 bg-blue-500/20 text-blue-400"
                : "border-white/[0.08] bg-white/[0.04] text-zinc-500"
            }`}>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path d="M4 16v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1M12 4v12M8 8l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-300">
                {dragOver ? "Drop to upload" : "Drop a file or "}
                {!dragOver && (
                  <span className="text-blue-400">click to browse</span>
                )}
              </p>
              <p className="mt-1 text-xs text-zinc-600">PDF · DOCX · Markdown · TXT — max 20 MB</p>
            </div>
          </>
        )}

        <input
          type="file"
          accept=".pdf,.docx,.md,.txt"
          onChange={onFileChange}
          disabled={uploading}
          className="hidden"
        />
      </label>

      {error && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5">
          <svg className="h-4 w-4 shrink-0 text-red-400" fill="none" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M8 5v4M8 11v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5">
          <svg className="h-4 w-4 shrink-0 text-emerald-400" fill="none" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <p className="text-xs text-emerald-400">{success}</p>
        </div>
      )}
    </div>
  );
}

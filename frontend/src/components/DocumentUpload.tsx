"use client";

import { useState, useCallback } from "react";
import { uploadDocument } from "@/lib/api";

interface DocumentUploadProps {
  workspaceId: string;
  onUploaded: () => void;
}

export default function DocumentUpload({
  workspaceId,
  onUploaded,
}: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = useCallback(
    async (file: File) => {
      setError("");
      setUploading(true);
      try {
        await uploadDocument(workspaceId, file);
        onUploaded();
      } catch (e: any) {
        setError(e.message || "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [workspaceId, onUploaded]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      className={`rounded-xl border-2 border-dashed p-8 text-center transition ${
        dragOver
          ? "border-blue-500 bg-blue-500/5"
          : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-600"
      }`}
    >
      {uploading ? (
        <div className="flex flex-col items-center gap-2">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <p className="text-sm text-zinc-400">Processing document...</p>
        </div>
      ) : (
        <>
          <p className="text-3xl mb-2">📄</p>
          <p className="text-sm text-zinc-300 mb-1">
            Drag & drop a file or{" "}
            <label className="cursor-pointer text-blue-400 hover:text-blue-300 underline">
              browse
              <input
                type="file"
                accept=".pdf,.docx,.md,.txt"
                onChange={onFileChange}
                className="hidden"
              />
            </label>
          </p>
          <p className="text-xs text-zinc-600">
            Supports PDF, DOCX, Markdown, TXT (max 20MB)
          </p>
        </>
      )}
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  );
}

"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import {
  ChatSession,
  ChatMessage as ChatMessageType,
  Citation,
  listSessions,
  createSession,
  getSessionMessages,
  deleteSession,
  executeQuery,
} from "@/lib/api";
import ChatMessage from "@/components/ChatMessage";

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  relevanceStatus?: string | null;
  loopCount?: number;
  latencyMs?: number | null;
  isStreaming?: boolean;
}

function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  workspaceId,
}: {
  sessions: ChatSession[];
  activeId?: string;
  onSelect: (s: ChatSession) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  workspaceId: string;
}) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-white/[0.06] bg-[#0a0a0f]">
      {/* Top */}
      <div className="flex items-center justify-between p-4 border-b border-white/[0.05]">
        <Link href={`/dashboard/${workspaceId}`} className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 14 14">
            <path d="M9 2L4 7l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          Documents
        </Link>
        <button
          onClick={onNew}
          className="flex items-center gap-1 rounded-lg bg-white/[0.06] px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:bg-white/[0.1] transition-all"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 14 14">
            <path d="M7 2v10M2 7h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          New chat
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {sessions.length === 0 ? (
          <p className="px-4 py-6 text-xs text-zinc-700 text-center">No chats yet</p>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center gap-2 px-3 py-2.5 mx-2 my-0.5 rounded-xl cursor-pointer transition-all ${
                activeId === s.id
                  ? "bg-blue-500/10 border border-blue-500/20 text-white"
                  : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-300 border border-transparent"
              }`}
              onClick={() => onSelect(s)}
            >
              <svg className="h-3.5 w-3.5 shrink-0 opacity-50" fill="none" viewBox="0 0 14 14">
                <path d="M13 8.5c0 .5-.4 1-1 1H3l-2 2.5V2c0-.5.4-1 1-1h10c.6 0 1 .5 1 1v6.5z" stroke="currentColor" strokeWidth="1.2" fill="none"/>
              </svg>
              <span className="flex-1 truncate text-xs">
                {s.title || "New conversation"}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                className="shrink-0 rounded p-0.5 opacity-0 group-hover:opacity-100 hover:text-red-400 transition-all"
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12">
                  <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

export default function ChatPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  const loadSessions = useCallback(async () => {
    if (!user) return;
    const sess = await listSessions(workspaceId);
    setSessions(sess);
  }, [user, workspaceId]);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSelectSession = async (session: ChatSession) => {
    setActiveSession(session);
    try {
      const msgs = await getSessionMessages(workspaceId, session.id);
      setMessages(msgs.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations,
        relevanceStatus: m.relevance_status,
        loopCount: m.loop_count,
        latencyMs: m.latency_ms,
      })));
    } catch { setMessages([]); }
  };

  const handleNewChat = async () => {
    try {
      const session = await createSession(workspaceId);
      setSessions((prev) => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
    } catch (e) { console.error("Failed to create session", e); }
  };

  const handleDeleteSession = async (sessionId: string) => {
    await deleteSession(workspaceId, sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSession?.id === sessionId) { setActiveSession(null); setMessages([]); }
  };

  const handleSend = async () => {
    const query = input.trim();
    if (!query || isQuerying) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    let session = activeSession;
    if (!session) {
      session = await createSession(workspaceId, query.slice(0, 60));
      setSessions((prev) => [session!, ...prev]);
      setActiveSession(session);
    }

    const userMsg: DisplayMessage = { id: `user-${Date.now()}`, role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);

    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "", isStreaming: true }]);
    setIsQuerying(true);

    try {
      const response = await executeQuery(workspaceId, query, session.id);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: response.answer, citations: response.citations, relevanceStatus: response.relevance_status, loopCount: response.loop_count, latencyMs: response.latency_ms, isStreaming: false }
            : m
        )
      );
      loadSessions();
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error: ${err.message || "Query failed"}`, isStreaming: false }
            : m
        )
      );
    } finally { setIsQuerying(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  if (authLoading || !user) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeId={activeSession?.id}
        onSelect={handleSelectSession}
        onNew={handleNewChat}
        onDelete={handleDeleteSession}
        workspaceId={workspaceId}
      />

      {/* Main chat */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-4 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-500/20">
                <svg className="h-7 w-7 text-blue-400" fill="none" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                  <path d="M12 8v4M12 16v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-white">Ask your documents anything</h2>
              <p className="mt-2 max-w-sm text-sm text-zinc-500 leading-relaxed">
                Using hybrid search, cross-encoder re-ranking, and self-correcting AI to give you accurate, cited answers.
              </p>
              <div className="mt-8 grid gap-2 sm:grid-cols-2 max-w-lg w-full">
                {[
                  "Summarize the key points from my documents",
                  "What are the main topics covered?",
                  "Find information about a specific topic",
                  "Compare findings across documents",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => { setInput(prompt); textareaRef.current?.focus(); }}
                    className="rounded-xl border border-white/[0.07] bg-white/[0.02] px-4 py-3 text-left text-xs text-zinc-400 hover:border-white/[0.14] hover:bg-white/[0.05] hover:text-zinc-200 transition-all"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl px-4 py-6">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  citations={msg.citations}
                  relevanceStatus={msg.relevanceStatus}
                  loopCount={msg.loopCount}
                  latencyMs={msg.latencyMs}
                  isStreaming={msg.isStreaming}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="border-t border-white/[0.05] bg-[#060608] px-4 py-4">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-end gap-3 rounded-2xl border border-white/[0.1] bg-white/[0.04] px-4 py-3 focus-within:border-blue-500/50 focus-within:bg-white/[0.06] transition-all">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
                }}
                onKeyDown={handleKeyDown}
                disabled={isQuerying}
                placeholder="Ask anything about your documents…"
                rows={1}
                className="flex-1 resize-none bg-transparent text-sm text-zinc-200 placeholder-zinc-600 outline-none disabled:opacity-50"
                style={{ maxHeight: "160px" }}
              />
              <button
                onClick={handleSend}
                disabled={isQuerying || !input.trim()}
                className="shrink-0 flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                {isQuerying ? (
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 16 16">
                    <path d="M2 14L14 8 2 2v5l8 1-8 1v5z" fill="currentColor"/>
                  </svg>
                )}
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-zinc-700">
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
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
import SessionSidebar from "@/components/SessionSidebar";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";

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

export default function ChatPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspaceId as string;

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  // Load sessions
  const loadSessions = useCallback(async () => {
    if (!user) return;
    const sess = await listSessions(workspaceId);
    setSessions(sess);
  }, [user, workspaceId]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load session messages
  const handleSelectSession = async (session: ChatSession) => {
    setActiveSession(session);
    try {
      const msgs = await getSessionMessages(workspaceId, session.id);
      setMessages(
        msgs.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations,
          relevanceStatus: m.relevance_status,
          loopCount: m.loop_count,
          latencyMs: m.latency_ms,
        }))
      );
    } catch {
      setMessages([]);
    }
  };

  // New chat
  const handleNewChat = async () => {
    try {
      const session = await createSession(workspaceId);
      setSessions((prev) => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
    } catch (e) {
      console.error("Failed to create session", e);
    }
  };

  // Delete session
  const handleDeleteSession = async (sessionId: string) => {
    await deleteSession(workspaceId, sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSession?.id === sessionId) {
      setActiveSession(null);
      setMessages([]);
    }
  };

  // Send message
  const handleSend = async (query: string) => {
    if (!query.trim() || isQuerying) return;

    // Auto-create session if none active
    let session = activeSession;
    if (!session) {
      session = await createSession(workspaceId, query.slice(0, 60));
      setSessions((prev) => [session!, ...prev]);
      setActiveSession(session);
    }

    // Add user message to display
    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
    };
    setMessages((prev) => [...prev, userMsg]);

    // Add streaming placeholder
    const assistantId = `assistant-${Date.now()}`;
    const streamingMsg: DisplayMessage = {
      id: assistantId,
      role: "assistant",
      content: "Thinking...",
      isStreaming: true,
    };
    setMessages((prev) => [...prev, streamingMsg]);
    setIsQuerying(true);

    try {
      const response = await executeQuery(workspaceId, query, session.id);

      // Replace streaming placeholder with real response
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: response.answer,
                citations: response.citations,
                relevanceStatus: response.relevance_status,
                loopCount: response.loop_count,
                latencyMs: response.latency_ms,
                isStreaming: false,
              }
            : m
        )
      );

      // Refresh session list for updated title
      loadSessions();
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: `Error: ${err.message || "Query failed"}`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsQuerying(false);
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
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSession?.id}
        onSelect={handleSelectSession}
        onNewChat={handleNewChat}
        onDelete={handleDeleteSession}
      />

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center px-4">
              <p className="text-4xl mb-4">🧠</p>
              <h2 className="text-lg font-semibold text-white mb-2">
                Ask anything about your documents
              </h2>
              <p className="text-sm text-zinc-500 max-w-md">
                Your questions are answered using hybrid search, cross-encoder
                re-ranking, and self-correcting AI. Inaccurate retrievals are
                automatically detected and rewritten.
              </p>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl">
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

        {/* Input */}
        <ChatInput onSend={handleSend} disabled={isQuerying} />
      </div>
    </div>
  );
}

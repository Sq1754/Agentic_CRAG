"use client";

import { ChatSession, deleteSession } from "@/lib/api";

interface SessionSidebarProps {
  sessions: ChatSession[];
  activeSessionId?: string;
  onSelect: (session: ChatSession) => void;
  onNewChat: () => void;
  onDelete: (sessionId: string) => void;
}

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onDelete,
}: SessionSidebarProps) {
  return (
    <div className="flex h-full w-64 flex-col border-r border-zinc-800 bg-zinc-950">
      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition flex items-center gap-2"
        >
          <span className="text-lg">+</span>
          <span>New Chat</span>
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {sessions.length === 0 ? (
          <p className="px-3 py-4 text-xs text-zinc-600 text-center">
            No conversations yet
          </p>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-2 rounded-lg px-3 py-2.5 cursor-pointer transition ${
                  activeSessionId === session.id
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                }`}
                onClick={() => onSelect(session)}
              >
                <span className="text-sm truncate flex-1">
                  {session.title}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                  }}
                  className="hidden text-zinc-600 hover:text-red-400 group-hover:block text-xs"
                  title="Delete session"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

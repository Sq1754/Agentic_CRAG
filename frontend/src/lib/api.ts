const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token Management ───────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("documind_token");
}

export function setToken(token: string) {
  localStorage.setItem("documind_token", token);
}

export function clearToken() {
  localStorage.removeItem("documind_token");
}

// ── API Fetch Wrapper ──────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API Error ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
}

export async function register(email: string, name: string, password: string) {
  return apiFetch<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name, password }),
  });
}

export async function login(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(body.detail);
  }

  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function getMe() {
  return apiFetch<User>("/api/v1/auth/me");
}

// ── Workspaces ──────────────────────────────────────────────────────────────

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  member_count: number;
}

export async function createWorkspace(name: string, description: string = "") {
  return apiFetch<Workspace>("/api/v1/workspaces/", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export async function listWorkspaces() {
  return apiFetch<Workspace[]>("/api/v1/workspaces/");
}

export async function getWorkspace(id: string) {
  return apiFetch<Workspace>(`/api/v1/workspaces/${id}`);
}

// ── Documents ───────────────────────────────────────────────────────────────

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number | null;
  chunk_count: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

export async function uploadDocument(workspaceId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<Document>(
    `/api/v1/workspaces/${workspaceId}/documents/upload`,
    { method: "POST", body: formData }
  );
}

export async function listDocuments(workspaceId: string) {
  return apiFetch<Document[]>(
    `/api/v1/workspaces/${workspaceId}/documents/`
  );
}

export async function deleteDocument(workspaceId: string, docId: string) {
  return apiFetch<void>(
    `/api/v1/workspaces/${workspaceId}/documents/${docId}`,
    { method: "DELETE" }
  );
}

// ── Chat Sessions ───────────────────────────────────────────────────────────

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  rewritten_query: string | null;
  relevance_status: string | null;
  loop_count: number;
  citations: Citation[] | null;
  latency_ms: number | null;
  created_at: string;
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  source: string;
  score: number;
  preview: string;
}

export async function createSession(workspaceId: string, title?: string) {
  return apiFetch<ChatSession>(
    `/api/v1/workspaces/${workspaceId}/chat/sessions`,
    { method: "POST", body: JSON.stringify({ title: title || "New Chat" }) }
  );
}

export async function listSessions(workspaceId: string) {
  return apiFetch<ChatSession[]>(
    `/api/v1/workspaces/${workspaceId}/chat/sessions`
  );
}

export async function getSessionMessages(
  workspaceId: string,
  sessionId: string
) {
  return apiFetch<ChatMessage[]>(
    `/api/v1/workspaces/${workspaceId}/chat/sessions/${sessionId}/messages`
  );
}

export async function deleteSession(workspaceId: string, sessionId: string) {
  return apiFetch<void>(
    `/api/v1/workspaces/${workspaceId}/chat/sessions/${sessionId}`,
    { method: "DELETE" }
  );
}

// ── Query (CRAG) ────────────────────────────────────────────────────────────

export interface QueryResponse {
  answer: string;
  query: string;
  rewritten_query: string | null;
  relevance_status: string;
  loop_count: number;
  citations: Citation[];
  latency_ms: number;
  session_id: string | null;
}

export async function executeQuery(
  workspaceId: string,
  query: string,
  sessionId?: string
) {
  return apiFetch<QueryResponse>(
    `/api/v1/workspaces/${workspaceId}/query`,
    {
      method: "POST",
      body: JSON.stringify({
        query,
        session_id: sessionId || null,
        max_retries: 2,
      }),
    }
  );
}

// ── SSE Stream Query ────────────────────────────────────────────────────────

export interface StreamEvent {
  node: string;
  relevance_status: string | null;
  loop_count: number | null;
  rewritten_query: string | null;
  generation: string | null;
}

export function streamQuery(
  workspaceId: string,
  query: string,
  sessionId?: string,
  onEvent?: (event: StreamEvent) => void,
  onDone?: () => void
) {
  const token = getToken();
  const params = new URLSearchParams({
    query,
    max_retries: "2",
    ...(sessionId ? { session_id: sessionId } : {}),
  });

  const url = `${API_BASE}/api/v1/workspaces/${workspaceId}/query/stream?${params}`;
  const eventSource = new EventSource(url);

  // Note: EventSource doesn't support custom headers natively.
  // For auth with SSE, the token would need to be passed as a query param
  // or via cookies in production. This is a known limitation.

  eventSource.onmessage = (e) => {
    try {
      const data: StreamEvent = JSON.parse(e.data);
      onEvent?.(data);
    } catch {
      // Ignore parse errors
    }
  };

  eventSource.onerror = () => {
    eventSource.close();
    onDone?.();
  };

  return eventSource;
}

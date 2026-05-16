const PYTHON_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type User = { id: string; name: string; email: string; created_at: string };
export type Conversation = { id: string; user_id: string; title: string; created_at: string };
export type Message = { id: string; conversation_id: string; role: string; content: string; created_at: string };

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${PYTHON_API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error('Login failed');
  return res.json();
}

export async function register(name: string, email: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${PYTHON_API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) throw new Error('Register failed');
  return res.json();
}

export async function fetchUsers() {
  const res = await fetch(`${PYTHON_API}/users`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function createUser(data: { name: string; email: string }) {
  const res = await fetch(`${PYTHON_API}/users`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create user');
  return res.json();
}

export async function updateUser(id: string, data: { name?: string; email?: string }) {
  const res = await fetch(`${PYTHON_API}/users/${id}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update user');
  return res.json();
}

export async function deleteUser(id: string) {
  const res = await fetch(`${PYTHON_API}/users/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete user');
  return res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${PYTHON_API}/conversations`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function createConversation(data: { title?: string }) {
  const res = await fetch(`${PYTHON_API}/conversations`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create conversation');
  return res.json();
}

export async function updateConversation(id: string, data: { title: string }) {
  const res = await fetch(`${PYTHON_API}/conversations/${id}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update conversation');
  return res.json();
}

export async function deleteConversation(id: string) {
  const res = await fetch(`${PYTHON_API}/conversations/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete conversation');
  return res.json();
}

export async function fetchMessages(conversationId: string) {
  const res = await fetch(`${PYTHON_API}/messages/conversation/${conversationId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function deleteMessage(id: string) {
  const res = await fetch(`${PYTHON_API}/messages/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete message');
  return res.json();
}

export type Citation = { doc_name: string; chunk_index: number; start_char: number; end_char: number };

export type StreamEvent =
  | { type: 'delta'; content: string }
  | { type: 'retrieval_start' }
  | { type: 'retrieval_done'; chunk_count: number }
  | { type: 'done'; citations: Citation[] }
  | { type: 'error'; message: string };

export async function* streamChat(
  messages: { role: string; content: string }[],
  conversationId?: string,
  useRag = true,
): AsyncGenerator<StreamEvent> {
  const token = getToken();
  const res = await fetch(`${PYTHON_API}/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages, conversation_id: conversationId, use_rag: useRag }),
  });

  if (!res.ok) throw new Error('Failed to start chat');
  if (!res.body) throw new Error('No response body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      try {
        const event = JSON.parse(raw) as StreamEvent;
        yield event;
        if (event.type === 'done' || event.type === 'error') return;
      } catch {}
    }
  }
}


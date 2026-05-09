const PYTHON_API = process.env.PYTHON_API_URL || 'http://localhost:8000';

export async function fetchUsers() {
  const res = await fetch(`${PYTHON_API}/users`);
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function createUser(data: { name: string; email: string }) {
  const res = await fetch(`${PYTHON_API}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create user');
  return res.json();
}

export async function updateUser(id: string, data: { name?: string; email?: string }) {
  const res = await fetch(`${PYTHON_API}/users/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update user');
  return res.json();
}

export async function deleteUser(id: string) {
  const res = await fetch(`${PYTHON_API}/users/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete user');
  return res.json();
}

export async function fetchConversations(userId: string) {
  const res = await fetch(`${PYTHON_API}/conversations/user/${userId}`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function createConversation(data: { user_id: string; title?: string }) {
  const res = await fetch(`${PYTHON_API}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create conversation');
  return res.json();
}

export async function updateConversation(id: string, data: { title: string }) {
  const res = await fetch(`${PYTHON_API}/conversations/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update conversation');
  return res.json();
}

export async function deleteConversation(id: string) {
  const res = await fetch(`${PYTHON_API}/conversations/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete conversation');
  return res.json();
}

export async function fetchMessages(conversationId: string) {
  const res = await fetch(`${PYTHON_API}/messages/conversation/${conversationId}`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function deleteMessage(id: string) {
  const res = await fetch(`${PYTHON_API}/messages/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete message');
  return res.json();
}

// LLM Chat - stream directly from Python backend
export async function* streamChat(
  messages: { role: string; content: string }[],
  conversationId?: string,
  userId?: string
): AsyncGenerator<string> {
  const res = await fetch(`${PYTHON_API}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, conversation_id: conversationId, user_id: userId }),
  });

  if (!res.ok) throw new Error('Failed to start chat');
  if (!res.body) throw new Error('No response body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try {
          const parsed = JSON.parse(data);
          if (parsed.content) yield parsed.content;
        } catch {}
      }
    }
  }
}

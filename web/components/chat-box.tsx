'use client';

import { useState, useEffect, useRef } from 'react';
import { fetchMessages, deleteMessage, streamChat, type Citation, type Conversation, type User, type Message } from '@/lib/api';

interface ChatBoxProps {
  user: User | null;
  conversation: Conversation | null;
}

type ChatMessage = { role: string; content: string; id?: string; citations?: Citation[] };

export function ChatBox({ user, conversation }: ChatBoxProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [retrieving, setRetrieving] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversation) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadMessages = async () => {
    if (!conversation) return;
    try {
      const data = await fetchMessages(conversation.id);
      setMessages(data.map((m: Message) => ({ role: m.role, content: m.content, id: m.id })));
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleDeleteMessage = async (id: string) => {
    if (!confirm('删除这条消息？')) return;
    try {
      await deleteMessage(id);
      setMessages(messages.filter((m) => m.id !== id));
    } catch {
      alert('删除失败');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !conversation || !user) return;

    const userContent = input;
    setInput('');

    setMessages(prev => [...prev, { role: 'user', content: userContent }]);

    try {
      let assistantContent = '';
      let finalCitations: Citation[] = [];
      const currentMessages = [...messages, { role: 'user', content: userContent }];

      for await (const event of streamChat(
        currentMessages.map((m) => ({ role: m.role, content: m.content })),
        conversation.id,
      )) {
        if (event.type === 'retrieval_start') {
          setRetrieving(true);
        } else if (event.type === 'retrieval_done') {
          setRetrieving(false);
        } else if (event.type === 'delta') {
          assistantContent += event.content;
          setMessages(prev => {
            const withoutLast = prev[prev.length - 1]?.role === 'assistant'
              ? prev.slice(0, -1)
              : prev;
            return [...withoutLast, { role: 'assistant', content: assistantContent }];
          });
        } else if (event.type === 'done') {
          finalCitations = event.citations;
          if (finalCitations.length > 0) {
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last?.role !== 'assistant') return prev;
              return [...prev.slice(0, -1), { ...last, citations: finalCitations }];
            });
          }
        } else if (event.type === 'error') {
          setMessages(prev => [...prev, { role: 'assistant', content: event.message }]);
          return;
        }
      }

      await new Promise(resolve => setTimeout(resolve, 500));
      await loadMessages();
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，出错了。' }]);
    } finally {
      setRetrieving(false);
    }
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center text-zinc-400">
        选择一个会话开始聊天
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {retrieving && (
          <div className="flex justify-start">
            <div className="text-xs text-zinc-400 px-3 py-1 bg-zinc-50 rounded-full border border-zinc-200">
              检索知识库中…
            </div>
          </div>
        )}
        {messages.map((m, index) => (
          <div
            key={index}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 whitespace-pre-wrap group relative ${
                m.role === 'user'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-900'
              }`}
            >
              {m.content}
              {m.id && (
                <button
                  onClick={() => handleDeleteMessage(m.id!)}
                  className="absolute -right-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 text-red-400 text-xs px-2"
                >
                  删除
                </button>
              )}
            </div>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1 max-w-[80%]">
                {m.citations.map((c, i) => (
                  <span key={i} className="text-xs text-zinc-400 bg-zinc-50 border border-zinc-200 rounded px-2 py-0.5">
                    {c.doc_name} §{c.chunk_index + 1}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-200 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息..."
          className="flex-1 rounded-xl border border-zinc-300 px-4 py-3 focus:outline-none focus:border-zinc-900"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="bg-zinc-900 text-white rounded-xl px-6 py-3 disabled:opacity-50"
        >
          发送
        </button>
      </form>
    </div>
  );
}


'use client';

import { useState, useEffect } from 'react';
import {
  fetchConversations,
  createConversation,
  deleteConversation,
  updateConversation,
  type Conversation,
  type User,
} from '@/lib/api';

interface ConversationListProps {
  user: User | null;
  currentId: string | null;
  onSelect: (conv: Conversation | null) => void;
}

export function ConversationList({ user, currentId, onSelect }: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    if (user) loadConversations();
  }, [user]);

  const loadConversations = async () => {
    if (!user) return;
    try {
      const data = await fetchConversations(user.id);
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const handleCreate = async () => {
    if (!user) return;
    try {
      const conv = await createConversation({ user_id: user.id });
      setConversations([conv, ...conversations]);
      onSelect(conv);
    } catch {
      alert('创建失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此会话？')) return;
    try {
      await deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (currentId === id) onSelect(null);
    } catch {
      alert('删除失败');
    }
  };

  const startEdit = (conv: Conversation) => {
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const saveEdit = async (id: string) => {
    try {
      await updateConversation(id, { title: editTitle });
      setConversations(
        conversations.map((c) => (c.id === id ? { ...c, title: editTitle } : c))
      );
      setEditingId(null);
    } catch {
      alert('更新失败');
    }
  };

  if (!user) {
    return <div className="p-4 text-zinc-400">请先选择用户</div>;
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-bold">会话</h2>
        <button
          onClick={handleCreate}
          className="text-sm bg-zinc-100 px-3 py-1 rounded hover:bg-zinc-200"
        >
          + 新建
        </button>
      </div>

      <div className="space-y-2">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`p-3 rounded cursor-pointer ${
              currentId === conv.id ? 'bg-zinc-100' : 'hover:bg-zinc-50'
            }`}
          >
            {editingId === conv.id ? (
              <div className="flex gap-2">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="flex-1 px-2 py-1 border rounded text-sm"
                  onKeyDown={(e) => e.key === 'Enter' && saveEdit(conv.id)}
                />
                <button
                  onClick={() => saveEdit(conv.id)}
                  className="text-sm text-zinc-600"
                >
                  保存
                </button>
              </div>
            ) : (
              <div onClick={() => onSelect(conv)} className="flex justify-between items-center">
                <div className="font-medium truncate">{conv.title}</div>
                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startEdit(conv);
                    }}
                    className="text-xs text-zinc-400 hover:text-zinc-600"
                  >
                    重命名
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(conv.id);
                    }}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    删除
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

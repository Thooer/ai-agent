'use client';

import { useState, useEffect } from 'react';
import { fetchUsers, createUser, deleteUser, type User } from '@/lib/api';

interface UserManagerProps {
  onSelectUser: (user: User | null) => void;
  currentUser: User | null;
}

export function UserManager({ onSelectUser, currentUser }: UserManagerProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newEmail.trim()) return;
    try {
      const user = await createUser({ name: newName, email: newEmail });
      setUsers([...users, user]);
      setNewName('');
      setNewEmail('');
      setIsCreating(false);
      onSelectUser(user);
    } catch {
      alert('创建失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除？')) return;
    try {
      await deleteUser(id);
      setUsers(users.filter((u) => u.id !== id));
      if (currentUser?.id === id) onSelectUser(null);
    } catch {
      alert('删除失败');
    }
  };

  return (
    <div className="p-4 border-b border-zinc-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-bold">用户</h2>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="text-sm bg-zinc-100 px-3 py-1 rounded hover:bg-zinc-200"
        >
          {isCreating ? '取消' : '+ 新建'}
        </button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreate} className="mb-4 space-y-2">
          <input
            placeholder="姓名"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          />
          <input
            placeholder="邮箱"
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          />
          <button type="submit" className="w-full bg-zinc-900 text-white py-2 rounded">创建</button>
        </form>
      )}

      <div className="space-y-2">
        {users.map((user) => (
          <div
            key={user.id}
            onClick={() => onSelectUser(user)}
            className={`p-3 rounded cursor-pointer flex justify-between items-center ${
              currentUser?.id === user.id ? 'bg-zinc-900 text-white' : 'bg-zinc-50 hover:bg-zinc-100'
            }`}
          >
            <div>
              <div className="font-medium">{user.name}</div>
              <div className={`text-sm ${currentUser?.id === user.id ? 'text-zinc-300' : 'text-zinc-500'}`}>
                {user.email}
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(user.id);
              }}
              className="text-red-500 text-sm px-2"
            >
              删除
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

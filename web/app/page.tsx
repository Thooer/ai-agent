'use client';

import { useState } from 'react';
import { UserManager } from '@/components/user-manager';
import { ConversationList } from '@/components/conversation-list';
import { ChatBox } from '@/components/chat-box';
import type { User, Conversation } from '@/lib/api';

export default function Home() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);

  const handleSelectUser = (user: User | null) => {
    setCurrentUser(user);
    setCurrentConversation(null);
  };

  const handleSelectConversation = (conv: Conversation | null) => {
    setCurrentConversation(conv);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-200 p-4">
        <h1 className="text-xl font-bold">AI Chat</h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-80 border-r border-zinc-200 overflow-y-auto">
          <UserManager onSelectUser={handleSelectUser} currentUser={currentUser} />
          <ConversationList
            user={currentUser}
            currentId={currentConversation?.id || null}
            onSelect={handleSelectConversation}
          />
        </div>

        {/* Chat Area */}
        <ChatBox user={currentUser} conversation={currentConversation} />
      </div>
    </div>
  );
}

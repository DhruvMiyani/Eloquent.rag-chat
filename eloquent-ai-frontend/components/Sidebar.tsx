'use client';

import React, { useState } from 'react';
import { Plus, Search, Settings, Trash2, Edit2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';
import useStore from '@/store/useStore';

const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'Just now';

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Just now';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Just now';
  }
};

export default function Sidebar() {
  const {
    conversations,
    currentConversation,
    createNewConversation,
    selectConversation,
    deleteConversation,
    updateConversationTitle
  } = useStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleEdit = (conv: any) => {
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveEdit = async (id: string) => {
    if (editTitle.trim()) {
      await updateConversationTitle(id, editTitle);
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      try {
        await deleteConversation(id);
      } catch (error) {
        // If backend doesn't support delete, remove it from local state only
        console.error('Delete not supported by backend, removing from local state');
        // The store's deleteConversation will handle local removal
      }
    }
  };

  return (
    <div className="w-80 flex flex-col bg-gray-50 border-r border-gray-200">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-700">Financial Operations</h2>
        </div>

        <button
          onClick={createNewConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-medium transition-colors"
        >
          <Plus className="h-5 w-5" />
          New Chat
        </button>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4">
        <div className="space-y-1">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Recent Conversations
          </h3>
          {filteredConversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={clsx(
                'group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors',
                currentConversation?.id === conv.id
                  ? 'bg-purple-100 text-purple-900'
                  : 'hover:bg-gray-100'
              )}
            >
              {editingId === conv.id ? (
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => handleSaveEdit(conv.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveEdit(conv.id);
                    } else if (e.key === 'Escape') {
                      setEditingId(null);
                      setEditTitle('');
                    }
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="flex-1 px-2 py-1 bg-white border border-purple-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
                  autoFocus
                />
              ) : (
                <>
                  <div className="flex-1 min-w-0">
                    <p className={clsx(
                      "font-medium text-sm truncate",
                      currentConversation?.id === conv.id ? "text-purple-900" : "text-gray-900"
                    )}>{conv.title}</p>
                    <p className={clsx(
                      "text-xs",
                      currentConversation?.id === conv.id ? "text-purple-700" : "text-gray-600"
                    )}>
                      {formatDate(conv.updatedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(conv);
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Edit2 className="h-3 w-3 text-gray-700" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(conv.id, e)}
                      className="p-1 hover:bg-red-100 rounded"
                    >
                      <Trash2 className="h-3 w-3 text-red-600" />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 border-t border-gray-200">
        <button className="flex items-center gap-2 p-2 w-full hover:bg-gray-100 rounded-lg transition-colors">
          <Settings className="h-5 w-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Settings</span>
        </button>
      </div>
    </div>
  );
}
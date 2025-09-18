'use client';

import { useEffect } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import useStore from '@/store/useStore';

export default function Home() {
  const { user, initializeAuth } = useStore();

  // For anonymous users, show simple ChatGPT-style layout without sidebar
  if (user?.isAnonymous) {
    return (
      <div className="h-screen flex flex-col bg-gray-50">
        <Header />
        <ChatArea />
      </div>
    );
  }

  // For registered users, show full layout with sidebar
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <ChatArea />
      </div>
    </div>
  );
}
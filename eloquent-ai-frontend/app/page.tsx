'use client';

import { useEffect } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import useStore from '@/store/useStore';

export default function Home() {
  const { user, loginAnonymous, loadConversations } = useStore();

  useEffect(() => {
    const initializeApp = async () => {
      if (!user) {
        await loginAnonymous();
      } else {
        await loadConversations();
      }
    };

    initializeApp();
  }, []);

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
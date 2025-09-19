'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { clsx } from 'clsx';
import useStore from '@/store/useStore';
import { SuggestedQuestion } from '@/types';
import AuthModal from './AuthModal';

const suggestedQuestions: SuggestedQuestion[] = [
  { text: 'How do I reset my password?', category: 'password' },
  { text: 'What documents do I need to open an account?', category: 'account' },
  { text: 'How do I enable two-factor authentication?', category: 'security' },
];

export default function ChatArea() {
  const {
    currentConversation,
    messages,
    isLoading,
    sendMessage,
    user,
    createNewConversation,
    initializeAuth
  } = useStore();

  const [input, setInput] = useState('');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [chatStartTime, setChatStartTime] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize authentication (check for existing token or create anonymous session)
  useEffect(() => {
    if (!user) {
      console.log('No user found, initializing auth...');
      initializeAuth();
    }
  }, [user, initializeAuth]);

  // Start chat timer and show auth modal after 20 seconds
  useEffect(() => {
    console.log('Timer effect triggered:', {
      messagesLength: messages.length,
      chatStartTime,
      isAnonymous: user?.isAnonymous,
      userId: user?.id
    });

    if (messages.length > 0 && !chatStartTime && user?.isAnonymous) {
      console.log('Starting 20-second timer for anonymous user');
      setChatStartTime(Date.now());

      const timer = setTimeout(() => {
        console.log('20-second timer fired, checking if still anonymous:', user?.isAnonymous);
        if (user?.isAnonymous) {
          console.log('Showing auth modal');
          setShowAuthModal(true);
        }
      }, 20000); // 20 seconds

      return () => {
        console.log('Clearing timer');
        clearTimeout(timer);
      };
    }
  }, [messages.length, chatStartTime, user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const messageText = input;
    setInput('');

    try {
      if (!currentConversation) {
        await createNewConversation();
      }
      await sendMessage(messageText);
    } catch (error) {
      console.error('Failed to send message:', error);
      setInput(messageText);
    }
  };

  const handleSuggestedQuestion = async (question: string) => {
    if (isLoading) return;

    try {
      if (!currentConversation) {
        await createNewConversation();
      }
      await sendMessage(question);
    } catch (error) {
      console.error('Failed to send suggested question:', error);
    }
  };

  // Show loading while logging in anonymous user
  if (!user) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Eloquent AI</h2>
          <p className="text-gray-600">Initializing your session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="flex items-center gap-2 mb-8">
            <Sparkles className="h-8 w-8 text-purple-600" />
            <h1 className="text-3xl font-bold text-gray-900">Eloquent AI responds instantly</h1>
          </div>
          <p className="text-gray-600 mb-12">Ask me anything about banking, accounts, payments, or financial services</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question.text)}
                className="p-4 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition-colors border border-gray-200"
              >
                <p className="text-sm font-medium text-gray-700">{question.text}</p>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-8">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={clsx(
                  'flex gap-4',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-white" />
                  </div>
                )}
                <div
                  className={clsx(
                    'max-w-[70%] rounded-2xl px-4 py-3',
                    message.role === 'user'
                      ? 'bg-gray-100 text-gray-900'
                      : 'bg-white border border-gray-200'
                  )}
                >
                  {message.role === 'assistant' ? (
                    <div className="prose prose-sm max-w-none text-gray-900">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-900">{message.content}</p>
                  )}
                </div>
                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-gray-700">
                      {user.name ? user.name[0].toUpperCase() : 'U'}
                    </span>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-white animate-pulse" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="border-t border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask about accounts, payments, security, or any banking topic..."
            className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            rows={1}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={clsx(
              'absolute right-2 bottom-2 p-2 rounded-lg transition-colors',
              input.trim() && !isLoading
                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            )}
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </form>

      {/* Auth Modal - Show after 20 seconds for anonymous users */}
      {showAuthModal && user?.isAnonymous && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          title="Continue your conversation"
          subtitle="Sign up to save your chat history and continue where you left off."
        />
      )}
    </div>
  );
}
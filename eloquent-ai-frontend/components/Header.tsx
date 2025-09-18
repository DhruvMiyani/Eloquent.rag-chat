'use client';

import React, { useState } from 'react';
import { User, LogOut } from 'lucide-react';
import useStore from '@/store/useStore';
import AuthModal from './AuthModal';

export default function Header() {
  const { user, logout } = useStore();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <>
      <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-gray-900">Eloquent AI</h1>
            <span className="text-gray-500">- Financial Assistant</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <nav className="hidden md:flex items-center gap-6">
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Resources</a>
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Careers</a>
          </nav>

          {user && !user.isAnonymous ? (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <User className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {user.name || user.email}
                </span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <button
                    onClick={() => {
                      logout();
                      setShowUserMenu(false);
                    }}
                    className="flex items-center gap-2 px-4 py-2 hover:bg-gray-50 w-full text-left text-sm text-red-600"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : !user ? (
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowAuthModal(true)}
                className="px-4 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                Sign in
              </button>
              <button className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors">
                Request a demo
              </button>
            </div>
          ) : null}
        </div>
      </header>

      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </>
  );
}
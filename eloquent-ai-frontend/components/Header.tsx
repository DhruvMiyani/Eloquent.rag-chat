'use client';

import React, { useState } from 'react';
import AuthModal from './AuthModal';

export default function Header() {
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <>
      <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-6">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-gray-900">Eloquent AI</h1>
        </div>

        <div className="flex items-center gap-4">
          <nav className="hidden md:flex items-center gap-6">
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Resources</a>
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Careers</a>
          </nav>

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
        </div>
      </header>

      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </>
  );
}
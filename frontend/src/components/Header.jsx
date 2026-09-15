"use client";

import React, { useState, useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/navigation';

export default function Header() {
  const { user, logout } = useAuth() || {};
  const { isDark, toggleDarkMode } = useContext(ThemeContext);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    setIsLoggingOut(true);
    logout?.();
    router.push('/login');
  };

  return (
    <header className="p-4 flex justify-between items-center bg-[var(--panel-bg)] border-b border-[var(--border-color)] transition-colors duration-300">
      <div className="text-xl font-semibold text-[var(--text-main)]">PolicyPilot</div>
      <div className="flex items-center space-x-4">
        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-full bg-[var(--accent-color)] text-white hover:bg-[var(--accent-hover)] transition-colors"
          aria-label="Toggle dark mode"
        >
          {isDark ? '🌙' : '☀️'}
        </button>
        {user && (
          <button
            onClick={handleLogout}
            className="flex items-center px-3 py-1 bg-primary text-white rounded hover:bg-primary/80 transform transition-transform duration-200 focus:outline-none"
          >
            {isLoggingOut ? <LoadingSpinner /> : 'Logout'}
          </button>
        )}
      </div>
    </header>
  );
}

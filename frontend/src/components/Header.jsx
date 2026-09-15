'use client';

import React, { useState, useContext, useEffect, useRef } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

export default function Header() {
  const { user, logout, role } = useAuth() || {};
  const { isDark, toggleDarkMode } = useContext(ThemeContext);
  const [profileOpen, setProfileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const profileRef = useRef(null);

  useEffect(() => {
    setMounted(true);
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setProfileOpen(false);
    logout?.();
    router.push('/login');
  };

  const initials = user?.name
    ? user.name.slice(0, 2).toUpperCase()
    : user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : 'PP';

  return (
    <header
      className={`app-header${scrolled ? ' app-header--scrolled' : ''}`}
      id="main-app-header"
    >
      {/* Left: Brand & Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Link href="/dashboard" className="app-header-brand" id="header-brand-link">
          <div className="app-header-logo-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="currentColor" fillOpacity="0.15" />
              <path d="M9 12l2 2 4-4" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="app-header-brand-text">
            <span className="app-header-brand-name">PolicyPilot</span>
            <span className="app-header-brand-sub">Workspace</span>
          </div>
        </Link>

        <div className="app-header-breadcrumb">
          <span className="breadcrumb-slash">/</span>
          <span className="breadcrumb-current">
            {pathname === '/chatbot' ? 'Policy Assistant' : 'Operations Dashboard'}
          </span>
        </div>
      </div>

      {/* Center: Nav Links */}
      <nav className="app-header-nav" aria-label="Workspace navigation">
        <Link
          href="/dashboard"
          className={`app-header-nav-link${pathname === '/dashboard' ? ' active' : ''}`}
          id="header-nav-dashboard"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          Workspace
        </Link>
        <Link
          href="/store"
          className={`app-header-nav-link${pathname === '/store' ? ' active' : ''}`}
          id="header-nav-store"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M16 10a4 4 0 0 1-8 0" />
          </svg>
          Customer Store
        </Link>
        <Link
          href="/chatbot"
          className={`app-header-nav-link${pathname === '/chatbot' ? ' active' : ''}`}
          id="header-nav-chatbot"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          AI Chat
        </Link>
      </nav>

      {/* Right: Actions */}
      <div className="app-header-actions">
        {/* Status Indicator */}
        <div className="app-header-status-pill" title="MongoDB vector collection synced">
          <span className="landing-status-dot" />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#059669' }}>RAG Active</span>
        </div>

        {/* Theme Toggle */}
        {mounted && (
          <button
            onClick={toggleDarkMode}
            className="app-icon-btn"
            aria-label="Toggle dark mode"
            id="header-theme-toggle"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            )}
          </button>
        )}

        {/* Notifications */}
        <button
          className="app-icon-btn"
          aria-label="Notifications"
          id="header-notifications-btn"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="app-notification-dot" aria-hidden="true" />
        </button>

        <div className="app-header-divider" aria-hidden="true" />

        {/* Profile Dropdown */}
        <div className="app-profile-wrapper" ref={profileRef}>
          <button
            className="app-profile-btn"
            onClick={() => setProfileOpen((o) => !o)}
            aria-label="Profile menu"
            aria-expanded={profileOpen}
            id="header-profile-btn"
          >
            <div className="app-avatar" aria-hidden="true">{initials}</div>
            <div className="app-profile-info">
              <span className="app-profile-name">{user?.name || user?.email?.split('@')[0] || 'User'}</span>
              <span className="app-profile-role">{role || 'Member'}</span>
            </div>
            <svg
              className={`app-chevron${profileOpen ? ' rotated' : ''}`}
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {profileOpen && (
            <div className="app-profile-dropdown" id="header-profile-dropdown">
              <div className="app-profile-drop-header">
                <p className="drop-user-name">{user?.name || user?.email?.split('@')[0] || 'User'}</p>
                <p className="drop-user-email">{user?.email || 'user@organization.com'}</p>
                <span className="drop-user-role-badge">{role === 'admin' ? 'Administrator' : 'Policy Analyst'}</span>
              </div>
              <div className="app-profile-drop-divider" />
              <Link
                href="/dashboard"
                className="app-profile-drop-item"
                onClick={() => setProfileOpen(false)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
                Workspace Overview
              </Link>
              <Link
                href="/chatbot"
                className="app-profile-drop-item"
                onClick={() => setProfileOpen(false)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Policy Assistant
              </Link>
              <div className="app-profile-drop-divider" />
              <button
                className="app-profile-drop-item logout-item"
                onClick={handleLogout}
                id="header-logout-btn"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

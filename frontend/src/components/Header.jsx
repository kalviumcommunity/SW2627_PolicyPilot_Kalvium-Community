"use client";

import React, { useState, useContext, useEffect, useRef } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

const navLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: '⊞' },
  { href: '/chatbot', label: 'AI Chat', icon: '✦' },
];

export default function Header() {
  const { user, logout, role } = useAuth() || {};
  const { isDark, toggleDarkMode } = useContext(ThemeContext);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const profileRef = useRef(null);

  useEffect(() => {
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
    setIsLoggingOut(true);
    setProfileOpen(false);
    logout?.();
    router.push('/login');
  };

  const initials = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : 'PP';

  return (
    <header
      className={`app-header${scrolled ? ' app-header--scrolled' : ''}`}
      id="main-app-header"
    >
      {/* Left: Brand */}
      <Link href="/dashboard" className="app-header-brand" id="header-brand-link">
        <div className="app-header-logo-mark">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.5C17.25 22.15 21 17.25 21 12V7l-9-5z" fill="url(#shieldGrad)" />
            <defs>
              <linearGradient id="shieldGrad" x1="0" y1="0" x2="24" y2="24">
                <stop offset="0%" stopColor="#7c3aed" />
                <stop offset="100%" stopColor="#ec4899" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className="app-header-brand-text">
          <span className="app-header-brand-name">PolicyPilot</span>
          <span className="app-header-brand-sub">ShopVerse workspace</span>
        </div>
      </Link>

      {/* Center: Nav Links */}
      <nav className="app-header-nav" aria-label="App navigation">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`app-header-nav-link${pathname === link.href ? ' active' : ''}`}
            id={`header-nav-${link.label.toLowerCase().replace(/\s/g, '-')}`}
          >
            <span className="nav-link-icon">{link.icon}</span>
            {link.label}
          </Link>
        ))}
      </nav>

      {/* Right: Actions */}
      <div className="app-header-actions">
        {/* Theme Toggle */}
        <button
          onClick={toggleDarkMode}
          className="app-icon-btn"
          aria-label="Toggle dark mode"
          id="header-theme-toggle"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark
            ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          }
        </button>

        {/* Notifications */}
        <button
          className="app-icon-btn"
          aria-label="Notifications"
          id="header-notifications-btn"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span className="app-notification-dot" aria-hidden="true" />
        </button>

        {/* Divider */}
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
              <span className="app-profile-name">{user?.email?.split('@')[0] || 'User'}</span>
              <span className="app-profile-role">{role || 'member'}</span>
            </div>
            <svg
              className={`app-chevron${profileOpen ? ' rotated' : ''}`}
              width="12" height="12" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2.5"
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {profileOpen && (
            <div className="app-dropdown" id="header-profile-dropdown">
              <div className="app-dropdown-header">
                <div className="app-avatar app-avatar--lg">{initials}</div>
                <div>
                  <p className="app-dropdown-name">{user?.email?.split('@')[0] || 'User'}</p>
                  <p className="app-dropdown-email">{user?.email || ''}</p>
                </div>
              </div>
              <div className="app-dropdown-divider" />
              <button className="app-dropdown-item" id="dropdown-settings">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
                Settings
              </button>
              <button className="app-dropdown-item" id="dropdown-help">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                Help & Support
              </button>
              <div className="app-dropdown-divider" />
              <button
                onClick={handleLogout}
                className="app-dropdown-item app-dropdown-item--danger"
                id="header-logout-btn"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                {isLoggingOut ? 'Signing out…' : 'Sign out'}
              </button>
            </div>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="app-icon-btn app-hamburger"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle mobile menu"
          id="header-hamburger-btn"
        >
          {menuOpen
            ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          }
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="app-mobile-menu" id="header-mobile-menu">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`app-mobile-nav-link${pathname === link.href ? ' active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <span>{link.icon}</span>
              {link.label}
            </Link>
          ))}
          <div className="app-dropdown-divider" style={{ margin: '0.5rem 0' }} />
          <button onClick={handleLogout} className="app-mobile-nav-link" style={{ color: '#f87171', textAlign: 'left', width: '100%' }}>
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}

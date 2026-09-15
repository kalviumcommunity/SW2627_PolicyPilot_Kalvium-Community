'use client';

import React, { useState, useEffect, useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import Link from 'next/link';

const navLinks = [
  { label: 'E-Commerce Storefront', href: '/store' },
  { label: 'AI Order Tracking', href: '/store' },
  { label: 'Store Integrations', href: '/dashboard' },
  { label: 'RAG Architecture', href: '#pipeline' },
  { label: 'Admin Portal', href: '/admin' },
];

export default function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [mounted, setMounted] = useState(false);
  const { isDark, toggleDarkMode } = useContext(ThemeContext);

  useEffect(() => {
    setMounted(true);
    const onScroll = () => setScrolled(window.scrollY > 15);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.dispatchEvent(
        new CustomEvent('open-policy-chat-with-query', {
          detail: { query: searchQuery.trim() },
        })
      );
    }
  };

  const openChat = () => {
    window.dispatchEvent(new Event('open-policy-chat'));
  };

  return (
    <>
      <nav
        className={`landing-nav${scrolled ? ' landing-nav--scrolled' : ''}`}
        id="landing-navbar"
      >
        <div className="landing-nav-container">
          {/* Brand & Logo */}
          <Link href="/" className="landing-nav-logo" id="landing-logo-link">
            <div className="landing-nav-logo-mark">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="currentColor" fillOpacity="0.15" />
                <path d="M9 12l2 2 4-4" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="landing-nav-logo-copy">
              <span className="landing-nav-logo-text">PolicyPilot</span>
              <span className="landing-nav-badge-pill">Enterprise RAG</span>
            </div>
          </Link>

          {/* System Status Pill */}
          <div className="landing-nav-status-badge" title="FastAPI and MongoDB online">
            <span className="landing-status-dot" />
            <span className="landing-status-text">RAG Online</span>
          </div>

          {/* Navigation Links */}
          <div className="landing-nav-links" aria-label="PolicyPilot navigation">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="landing-nav-link"
                id={`landing-nav-${link.label.toLowerCase().replace(/[\s&:]+/g, '-')}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right Actions */}
          <div className="landing-nav-actions">
            {/* Search */}
            <form onSubmit={handleSearch} className="landing-nav-search" role="search">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                type="text"
                placeholder="Search policy index..."
                aria-label="Search policies"
                id="landing-search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <span className="landing-search-kbd">↵</span>
            </form>

            {/* Theme Toggle */}
            {mounted && (
              <button
                className="landing-nav-icon-btn"
                onClick={toggleDarkMode}
                aria-label="Toggle dark/light mode"
                id="landing-theme-toggle"
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

            {/* Quick Assistant Launcher */}
            <button
              className="landing-nav-icon-btn"
              onClick={openChat}
              aria-label="Open Policy Assistant"
              id="landing-assistant-quick-btn"
              title="Open Chat Assistant"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </button>

            <div className="landing-nav-divider" aria-hidden="true" />

            {/* Direct Link to E-Commerce Track Order */}
            <Link
              href="/store"
              style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                color: '#059669',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                padding: '0.45rem 0.85rem',
                borderRadius: '7px',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                whiteSpace: 'nowrap'
              }}
              id="landing-track-order-btn"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="1" y="3" width="15" height="13" />
                <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                <circle cx="5.5" cy="18.5" r="2.5" />
                <circle cx="18.5" cy="18.5" r="2.5" />
              </svg>
              Track Order
            </Link>

            {/* Launch Workspace CTA */}
            <Link href="/dashboard" className="landing-nav-cta" id="landing-cta-link">
              Launch Workspace
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          </div>
        </div>
      </nav>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="landing-mobile-menu" id="landing-mobile-menu">
          <form onSubmit={handleSearch} className="landing-mobile-search">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Search policy index..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="landing-mobile-link"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div style={{ height: '1px', background: 'var(--border-color)', margin: '0.6rem 0' }} />
          <Link href="/store" className="landing-mobile-link" onClick={() => setMobileOpen(false)} style={{ color: '#059669', fontWeight: 700 }}>
            Customer Store &amp; AI Order Tracking →
          </Link>
          <Link href="/admin" className="landing-mobile-link" onClick={() => setMobileOpen(false)}>
            Admin Console (PIN Key: 8899) →
          </Link>
          <Link href="/dashboard" className="landing-mobile-cta" onClick={() => setMobileOpen(false)}>
            Launch Workspace →
          </Link>
        </div>
      )}
    </>
  );
}

'use client';

import React from 'react';
import Link from 'next/link';

export default function HeroSection() {
  const openChat = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('open-policy-chat'));
    }
  };

  return (
    <section className="hero-section" id="hero">
      {/* Subtle background grid pattern */}
      <div className="hero-grid-pattern" aria-hidden="true" />

      <div className="hero-content">
        <div className="hero-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span>E-Commerce AI Order Tracking &amp; Policy Intelligence</span>
        </div>

        <h1 className="hero-title">
          Track Every Order &amp;<br />
          <span className="hero-gradient-text">Verify Policies</span><br />
          Through Grounded AI.
        </h1>

        <p className="hero-subtitle">
          Connect your e-commerce website to PolicyPilot in minutes. Let customers browse products, place orders, and track shipments live with an AI assistant grounded in your official return policies and vendor dispatch SLAs.
        </p>

        <div className="hero-actions" style={{ display: 'flex', gap: '0.85rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link href="/store" className="btn-primary" id="hero-store-btn" style={{ background: '#059669', borderColor: '#059669' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
            Customer Store &amp; AI Tracking
          </Link>

          <Link href="/dashboard" className="btn-primary" id="hero-workspace-btn">
            Connect Store &amp; Workspace
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>

          <Link href="/chatbot" className="btn-outline" id="hero-chatbot-btn" style={{ background: '#eef2ff', color: '#4f46e5', borderColor: '#c7d2fe' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            AI Policy Chatbot
          </Link>

          <Link href="/admin" className="btn-outline" id="hero-admin-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            Admin Management
          </Link>
        </div>

        {/* Live System Metrics */}
        <div className="hero-stats">
          <div className="hero-stat-card">
            <div className="hero-stat-val">100%</div>
            <div className="hero-stat-label">Grounded with Citations [1][2]</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-val">&lt; 250ms</div>
            <div className="hero-stat-label">FastAPI Retrieval &amp; Query Cache</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-val">Two-Stage</div>
            <div className="hero-stat-label">Cross-Score Candidate Re-Ranking</div>
          </div>
          <div className="hero-stat-card">
            <div className="hero-stat-val">SSE</div>
            <div className="hero-stat-label">Real-Time Token Streaming</div>
          </div>
        </div>
      </div>
    </section>
  );
}

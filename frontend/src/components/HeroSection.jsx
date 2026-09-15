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
          <span>Enterprise Retrieval-Augmented Generation (RAG)</span>
        </div>

        <h1 className="hero-title">
          Fast, Grounded &amp;<br />
          <span className="hero-gradient-text">Citation-Backed</span><br />
          Policy Intelligence.
        </h1>

        <p className="hero-subtitle">
          Query internal organizational documentation, seller agreements, HR handbooks, and compliance frameworks with zero ambiguity. Powered by FastAPI, ChromaDB vector storage, two-stage cross-scoring re-ranking, and strict hallucination guardrails.
        </p>

        <div className="hero-actions">
          <Link href="/dashboard" className="btn-primary" id="hero-workspace-btn">
            Launch Workspace
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
          <button className="btn-outline" onClick={openChat} id="hero-chat-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Ask Policy Assistant
          </button>
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

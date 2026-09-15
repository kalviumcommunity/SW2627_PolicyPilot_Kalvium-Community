'use client';

import React, { useState } from 'react';
import Link from 'next/link';

const footerSections = [
  {
    title: 'RAG Pipeline',
    links: [
      { label: 'Document Ingestion (PDF/MD/HTML)', href: '#pipeline' },
      { label: 'Token-Bounded Chunking', href: '#pipeline' },
      { label: 'ChromaDB Vector Embeddings', href: '#pipeline' },
      { label: 'Cosine Similarity Search', href: '#pipeline' },
      { label: 'Cross-Score Candidate Re-Ranking', href: '#pipeline' },
      { label: 'Hallucination Guardrails', href: '#guardrails' },
    ],
  },
  {
    title: 'Core Capabilities',
    links: [
      { label: 'Grounded RAG Pipeline', href: '#features' },
      { label: 'Inline Source Citations [1][2]', href: '#guardrails' },
      { label: 'Real-Time SSE Streaming (/query/stream)', href: '#features' },
      { label: 'SHA-256 Query Cache (15m TTL)', href: '#features' },
      { label: 'Structured JSON Logging', href: '#features' },
      { label: 'Token & Cost Usage Telemetry', href: '#features' },
    ],
  },
  {
    title: 'Workspace & API',
    links: [
      { label: 'Policy Operations Dashboard', href: '/dashboard' },
      { label: 'Interactive Streaming Assistant', href: '/chatbot' },
      { label: 'FastAPI Backend Swagger Docs', href: 'http://localhost:8000/docs', external: true },
      { label: 'Admin Policy Management', href: '/admin' },
      { label: 'ChromaDB Vector Collections', href: '/dashboard' },
      { label: 'SSE Endpoint Specification', href: '#features' },
    ],
  },
  {
    title: 'Enterprise & Security',
    links: [
      { label: 'Hallucination Refusal Thresholds', href: '#guardrails' },
      { label: 'Zero-Unverified Claims Policy', href: '#guardrails' },
      { label: 'PII & Secret Redaction Logs', href: '#features' },
      { label: 'Role-Based Access Control (RBAC)', href: '/login' },
      { label: 'Data Isolation & Memory Safety', href: '#guardrails' },
      { label: 'Audit Trail & Request IDs', href: '#features' },
    ],
  },
];

const telemetryItems = [
  { label: 'FastAPI Backend', status: 'Online (Port 8000)', color: '#059669' },
  { label: 'ChromaDB Vector Store', status: 'Persistent & Synced', color: '#4f46e5' },
  { label: 'Query Cache', status: 'SHA-256 · 15m TTL Active', color: '#d97706' },
  { label: 'SSE Streaming', status: 'Active (/query/stream)', color: '#0284c7' },
  { label: 'Guardrail Engine', status: '0.65 Gate Enforced', color: '#db2777' },
];

export default function LandingFooter() {
  const [subscribed, setSubscribed] = useState(false);
  const [email, setEmail] = useState('');

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail('');
    }
  };

  return (
    <footer className="landing-footer" id="landing-footer">
      {/* Newsletter / Policy updates strip */}
      <div className="landing-footer-newsletter">
        <div className="landing-footer-newsletter-inner">
          <div className="landing-footer-newsletter-text">
            <div className="landing-footer-pill">Release Notifications</div>
            <h3>Enterprise Policy &amp; RAG System Updates</h3>
            <p>
              Receive notifications when new organizational compliance policies, vector index updates, or model guardrails are deployed.
            </p>
          </div>
          <form className="landing-footer-form" onSubmit={handleSubscribe}>
            {subscribed ? (
              <div className="landing-footer-subscribed">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>Subscribed to PolicyPilot updates</span>
              </div>
            ) : (
              <div className="landing-footer-input-wrap">
                <input
                  type="email"
                  placeholder="Enter your enterprise email..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  aria-label="Email for policy updates"
                  id="footer-email-input"
                />
                <button type="submit" id="footer-subscribe-btn">
                  Subscribe
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* Main Grid */}
      <div className="landing-footer-main">
        {/* Brand Column */}
        <div className="landing-footer-brand-col">
          <Link href="/" className="landing-footer-logo">
            <div className="landing-footer-logo-mark">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="currentColor" fillOpacity="0.15" />
                <path d="M9 12l2 2 4-4" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span className="landing-footer-logo-text">PolicyPilot</span>
          </Link>
          <p className="landing-footer-desc">
            Enterprise-grade Retrieval-Augmented Generation (RAG) platform providing fast, accurate, and citation-grounded answers to internal organizational policy and documentation questions.
          </p>

          <div className="landing-footer-meta-tags">
            <span className="landing-meta-tag">FastAPI Backend</span>
            <span className="landing-meta-tag">ChromaDB Vector</span>
            <span className="landing-meta-tag">Cross Re-Ranking</span>
            <span className="landing-meta-tag">Grounded Citations</span>
          </div>
        </div>

        {/* 4 Link Columns */}
        {footerSections.map((col) => (
          <div key={col.title} className="landing-footer-col">
            <h4 className="landing-footer-col-title">{col.title}</h4>
            <ul className="landing-footer-links">
              {col.links.map((link) => (
                <li key={link.label}>
                  {link.external ? (
                    <a
                      href={link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="landing-footer-link"
                    >
                      {link.label}
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: '4px', verticalAlign: 'middle' }}>
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    </a>
                  ) : link.href.startsWith('/') ? (
                    <Link href={link.href} className="landing-footer-link">
                      {link.label}
                    </Link>
                  ) : (
                    <a href={link.href} className="landing-footer-link">
                      {link.label}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Live System Telemetry Strip */}
      <div className="landing-footer-telemetry">
        <div className="landing-telemetry-title">System Telemetry:</div>
        <div className="landing-telemetry-items">
          {telemetryItems.map((item) => (
            <div key={item.label} className="landing-telemetry-item">
              <span className="landing-telemetry-dot" style={{ backgroundColor: item.color }} />
              <strong>{item.label}:</strong>
              <span>{item.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="landing-footer-bottom">
        <div className="landing-footer-bottom-inner">
          <p className="landing-footer-copy">
            © {new Date().getFullYear()} <strong>PolicyPilot</strong>. Enterprise RAG Platform. All rights reserved. Kalvium Community Project SW2627.
          </p>
          <div className="landing-footer-legal">
            <a href="#guardrails">Security &amp; Guardrails</a>
            <span className="landing-footer-dot-sep">•</span>
            <a href="#pipeline">Citation Framework</a>
            <span className="landing-footer-dot-sep">•</span>
            <Link href="/dashboard">Operations Workspace</Link>
            <span className="landing-footer-dot-sep">•</span>
            <Link href="/login">Portal Access</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

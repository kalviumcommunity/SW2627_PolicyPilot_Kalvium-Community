'use client';

import React from 'react';

const pillars = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
    title: 'Pre-Generation Guardrails',
    desc: 'When retrieved evidence similarity fails the confidence bar (score < 0.65), PolicyPilot safely refuses rather than synthesizing ungrounded claims.',
    metric: '0.65',
    metricLabel: 'Strict Confidence Gate',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
      </svg>
    ),
    title: 'Strict Grounded Answers',
    desc: 'The generation prompt enforces strict adherence to retrieved text chunks. Any claim not present in the verified evidence is rejected by the prompt engine.',
    metric: '100%',
    metricLabel: 'Fact-Grounded Syntheses',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    title: 'Sub-Millisecond Query Cache',
    desc: 'Frequent policy questions (e.g. return windows, shipping SLAs) hit our SHA-256 in-memory cache directly, returning verified responses in under 1ms.',
    metric: '0.4ms',
    metricLabel: 'Cache Hit Latency',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
    title: 'Secret & PII Redaction',
    desc: 'Observability logs automatically redact tokens, API credentials, and personally identifiable employee data before writing to structured JSON logs.',
    metric: 'UUID',
    metricLabel: 'Per-Request Audit Tracing',
  },
];

const quotes = [
  {
    author: 'Compliance Lead',
    role: 'Operations & Legal Affairs',
    quote: 'PolicyPilot cut policy dispute resolution time by 80%. Having instant, clickable citations back to the exact PDF page gives the entire team total confidence.',
  },
  {
    author: 'Head of Marketplace Operations',
    role: 'Seller & Partner Management',
    quote: 'Support agents now quote exact agreement clauses with precise dates and SLAs instead of relying on memory or outdated wiki pages.',
  },
];

export default function TrustSection() {
  return (
    <section className="section" id="guardrails">
      <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 3rem' }}>
        <div className="section-label" style={{ justifyContent: 'center' }}>Enterprise Trust &amp; Reliability</div>
        <h2 className="section-title">Zero Guesswork.<br />Total Auditability.</h2>
        <p className="section-desc" style={{ margin: '0 auto' }}>
          Built from the ground up for organizations where a wrong answer is unacceptable. Every retrieval is scored, every claim is cited, and every low-confidence query is safely refused.
        </p>
      </div>

      {/* 4 Pillars Grid */}
      <div className="guardrails-grid">
        {pillars.map((pillar) => (
          <div key={pillar.title} className="guardrail-card">
            <div className="guardrail-icon-row">
              <div className="guardrail-icon">{pillar.icon}</div>
              <div className="guardrail-metric-pill">
                <strong>{pillar.metric}</strong>
                <small>{pillar.metricLabel}</small>
              </div>
            </div>
            <h3 className="guardrail-title">{pillar.title}</h3>
            <p className="guardrail-desc">{pillar.desc}</p>
          </div>
        ))}
      </div>

      {/* Enterprise Validation Quotes */}
      <div className="guardrails-quotes-row">
        {quotes.map((q, idx) => (
          <div key={idx} className="guardrail-quote-card">
            <div className="quote-badge">Grounded Verification</div>
            <p className="quote-text">"{q.quote}"</p>
            <div className="quote-meta">
              <strong>{q.author}</strong>
              <span>{q.role}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

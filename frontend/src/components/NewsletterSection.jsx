'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email) setSubmitted(true);
  };

  const openChat = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('open-policy-chat'));
    }
  };

  return (
    <section className="newsletter-section" id="cta-workspace">
      <div className="newsletter-card">
        <div className="section-label" style={{ justifyContent: 'center', display: 'flex', textAlign: 'center' }}>
          Enterprise Deployment
        </div>
        <h2 className="newsletter-title">
          Empower Your Organization With<br />Grounded Policy Intelligence
        </h2>
        <p className="newsletter-subtitle">
          Eliminate ambiguity in customer support, marketplace operations, and internal compliance with verified citations and sub-second retrieval.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '2.5rem' }}>
          <Link href="/dashboard" className="btn-primary" style={{ padding: '0.85rem 2rem', fontSize: '0.95rem' }}>
            Launch Policy Workspace
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
          <button onClick={openChat} className="btn-outline" style={{ padding: '0.85rem 1.75rem', fontSize: '0.95rem' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Ask Policy Assistant
          </button>
        </div>

        {submitted ? (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.75rem',
              background: 'rgba(16,185,129,0.1)',
              border: '1px solid rgba(16,185,129,0.25)',
              borderRadius: '9999px',
              color: '#059669',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Subscribed to PolicyPilot updates and release notes.</span>
          </div>
        ) : (
          <form className="newsletter-form" onSubmit={handleSubmit} id="newsletter-form">
            <input
              type="email"
              placeholder="Enter your organizational email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              id="newsletter-email"
            />
            <button type="submit" id="newsletter-submit-btn">
              Get Release Notes
            </button>
          </form>
        )}
      </div>
    </section>
  );
}

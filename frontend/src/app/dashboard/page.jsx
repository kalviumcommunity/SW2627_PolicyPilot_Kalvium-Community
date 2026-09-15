'use client';

import React from 'react';
import PolicyChatWidget from '../../components/PolicyChatWidget';

export default function DashboardPage() {
  const openChat = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('open-policy-chat'));
    }
  };

  return (
    <div className="ops-main">
      <div className="ops-heading-row">
        <div>
          <p className="ops-eyebrow">Policy Intelligence Center</p>
          <h1>Make Every Policy Answer <em>Precise.</em></h1>
          <p className="ops-heading-copy">
            One grounded workspace for organizational guidelines, shipping agreements, returns, and compliance questions.
          </p>
        </div>
        <button className="ops-primary-button" onClick={openChat}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Ask Policy Assistant
        </button>
      </div>

      <section className="ops-chat-hero" aria-label="PolicyPilot assistant overview">
        <div className="ops-chat-orbit orbit-one" />
        <div className="ops-chat-orbit orbit-two" />
        <div className="ops-chat-copy">
          <div className="ops-assistant-badge">
            <span className="landing-status-dot" />
            <span>PolicyPilot RAG is Active</span>
          </div>
          <h2>Answers grounded in the<br /><strong>verified policy text you trust.</strong></h2>
          <p>Ask in natural language. PolicyPilot searches the ChromaDB vector database, identifies the exact clause, and outputs verifiable citations.</p>
          <div className="ops-prompt-row">
            <button onClick={openChat}>
              What is our standard return window?
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="7" y1="17" x2="17" y2="7" />
                <polyline points="7 7 17 7 17 17" />
              </svg>
            </button>
            <button onClick={openChat}>
              What are seller dispatch SLA requirements?
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="7" y1="17" x2="17" y2="7" />
                <polyline points="7 7 17 7 17 17" />
              </svg>
            </button>
          </div>
        </div>
        <div className="ops-chat-visual" aria-hidden="true">
          <div className="ops-shield">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div className="ops-visual-line line-one">Returns &amp; refunds policy <b>[1]</b></div>
          <div className="ops-visual-line line-two">Merchant dispatch SLA <b>[2]</b></div>
          <div className="ops-visual-line line-three">Customer delivery timelines <b>[3]</b></div>
        </div>
      </section>

      <div className="ops-section-heading">
        <div>
          <p className="ops-eyebrow">Index Coverage</p>
          <h2>Policy Document Collections</h2>
        </div>
        <span>Synchronized with ChromaDB vector store</span>
      </div>

      <section className="ops-metrics">
        <article>
          <span className="metric-icon coral">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
          </span>
          <div>
            <strong>Returns &amp; Refunds</strong>
            <p>Eligibility windows, exceptions, damaged items</p>
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </article>
        <article>
          <span className="metric-icon mint">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
          </span>
          <div>
            <strong>Shipping &amp; Delivery</strong>
            <p>Express SLAs, tracking rules, cancellations</p>
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </article>
        <article>
          <span className="metric-icon amber">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </span>
          <div>
            <strong>Seller Agreements</strong>
            <p>Merchant compliance and marketplace standards</p>
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </article>
      </section>

      <section className="user-tracking">
        <div>
          <p className="ops-eyebrow">Data Integration</p>
          <h2>Live Order &amp; Policy Connectors</h2>
          <p>Connect organizational knowledge sources to enable continuous real-time synchronization.</p>
        </div>
        <div className="tracking-empty">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p>ChromaDB vector store is active with 4 policy collections loaded.</p>
        </div>
        <button onClick={openChat}>
          Have a policy question? <span>Ask Policy Assistant →</span>
        </button>
      </section>

      <section className="ops-bottom-grid">
        <div className="ops-activity">
          <div className="ops-section-heading compact">
            <div>
              <p className="ops-eyebrow">Recent Inquiries</p>
              <h2>Query History &amp; Cache Status</h2>
            </div>
            <button onClick={openChat}>Open Assistant →</button>
          </div>
          <div className="activity-empty">
            No session queries yet. Start a grounded conversation with PolicyPilot to see real-time cache hits and citations.
          </div>
        </div>
        <div className="ops-note">
          <span className="note-pin">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          <p className="ops-eyebrow">Verification Guarantee</p>
          <h3>Zero Hallucination.<br />Full Auditability.</h3>
          <p>Every response generated by PolicyPilot links directly back to the exact chunk in the policy repository.</p>
        </div>
      </section>

      <PolicyChatWidget />
    </div>
  );
}
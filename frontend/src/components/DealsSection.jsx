'use client';

import React, { useState } from 'react';

const featureHighlights = [
  {
    id: 'citations',
    tag: 'Truth & Verification',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    ),
    title: 'Source Citations & Excerpt Mapping',
    desc: 'Every factual claim in the generated answer is mapped directly to inline citation markers [1], [2] linked to source documents, chunk IDs, and exact text excerpts.',
    code: `// Verified Citation Response Structure
{
  "answer": "Sellers must dispatch items within 48 hours [1]...",
  "citations": [
    {
      "citation_id": 1,
      "source": "seller_agreement_v2.pdf",
      "page": 4,
      "chunk_id": "chunk_sa_0042",
      "excerpt": "Merchant Dispatch SLAs: All verified sellers shall dispatch...",
      "similarity_score": 0.942
    }
  ]
}`,
    stats: '100% Verifiable',
  },
  {
    id: 'streaming',
    tag: 'Low-Latency Streaming',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    title: 'Real-Time SSE Streaming (/query/stream)',
    desc: 'Server-Sent Events (SSE) streaming endpoint emitting real-time token events and finalized citation payloads directly to the Next.js React frontend.',
    code: `POST /query/stream
Content-Type: text/event-stream

event: token
data: {"token": "Refunds "}

event: token
data: {"token": "are processed within 5 business days [1]."}

event: citations
data: {"citations": [{"id": 1, "source": "returns_policy.md"}]}`,
    stats: '< 80ms Time-to-First-Token',
  },
  {
    id: 'cache',
    tag: 'Query Caching',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
        <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
        <line x1="6" y1="6" x2="6.01" y2="6" />
        <line x1="6" y1="18" x2="6.01" y2="18" />
      </svg>
    ),
    title: 'SHA-256 In-Memory Query Cache',
    desc: 'In-memory caching service using SHA-256 query key hashing with a 15-minute sliding TTL, hit/miss metrics tracking, and sub-millisecond response for repeated inquiries.',
    code: `// Cache Key Hashing & Instant Resolution
def get_cached_response(query: str, collection: str):
    cache_key = hashlib.sha256(f"{collection}:{query.strip().lower()}".encode()).hexdigest()
    if cache_key in memory_cache:
        metrics.increment("cache_hit")
        return memory_cache[cache_key] # 0.4ms latency
    metrics.increment("cache_miss")`,
    stats: '94% Cache Speedup',
  },
  {
    id: 'telemetry',
    tag: 'Observability & Telemetry',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
    title: 'Structured JSON Logging & TikToken Tracking',
    desc: 'Structured JSON-formatted logs with unique UUID request_id tracking, secret/PII redaction, real-time token counting via tiktoken, and latency measurement.',
    code: `// Observability & Cost Tracking Payload
{
  "request_id": "8f3b4c10-982a-4c22-b91c-fa32190d7e55",
  "timestamp": "2026-09-15T10:07:00Z",
  "prompt_tokens": 842,
  "completion_tokens": 168,
  "total_tokens": 1010,
  "estimated_cost_usd": 0.00151,
  "latency_ms": 234.8,
  "guardrail_status": "PASSED"
}`,
    stats: 'Full Observability',
  },
];

export default function DealsSection() {
  const [activeTab, setActiveTab] = useState('citations');
  const activeFeature = featureHighlights.find((f) => f.id === activeTab) || featureHighlights[0];

  return (
    <section className="section" id="features">
      <div className="section-label">Enterprise Capabilities</div>
      <h2 className="section-title">Engineered for Accuracy,<br />Speed &amp; Transparency</h2>
      <p className="section-desc">
        PolicyPilot eliminates the risks of hallucination through rigorous evidence verification, instant caching, and transparent source tracing.
      </p>

      {/* Tab Selectors */}
      <div className="features-tab-row">
        {featureHighlights.map((f) => (
          <button
            key={f.id}
            className={`features-tab-btn ${activeTab === f.id ? 'is-active' : ''}`}
            onClick={() => setActiveTab(f.id)}
            id={`feature-tab-${f.id}`}
          >
            <span className="features-tab-icon">{f.icon}</span>
            <span>{f.title}</span>
          </button>
        ))}
      </div>

      {/* Feature Showcase Detail Card */}
      <div className="feature-detail-card" id={`feature-detail-${activeFeature.id}`}>
        <div className="feature-detail-content">
          <div className="feature-detail-tag">
            <span>{activeFeature.icon}</span>
            <span>{activeFeature.tag}</span>
          </div>
          <h3 className="feature-detail-title">{activeFeature.title}</h3>
          <p className="feature-detail-desc">{activeFeature.desc}</p>
          <div className="feature-detail-badge">
            <strong>Key Benefit:</strong> {activeFeature.stats}
          </div>
          <div className="feature-detail-action">
            <a href="/dashboard" className="btn-primary" style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}>
              Inspect in Workspace →
            </a>
          </div>
        </div>

        <div className="feature-detail-code">
          <div className="code-header">
            <div className="code-dots">
              <span className="dot red" />
              <span className="dot yellow" />
              <span className="dot green" />
            </div>
            <span className="code-filename">spec_{activeFeature.id}.py</span>
          </div>
          <pre className="code-block">
            <code>{activeFeature.code}</code>
          </pre>
        </div>
      </div>
    </section>
  );
}

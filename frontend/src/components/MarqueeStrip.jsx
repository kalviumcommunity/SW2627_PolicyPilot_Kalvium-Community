'use client';

import React from 'react';

const capabilities = [
  'Multi-Format Ingestion (PDF, MD, HTML, Plain Text)',
  'Token-Bounded Chunking with Context Overlap',
  'OpenAI Embeddings & Persistent ChromaDB',
  'Hybrid Vector Cosine Similarity & Metadata Filtering',
  'Two-Stage Cross-Scoring Candidate Re-Ranking',
  'Strict Hallucination Guardrails & Refusals (0.65 Threshold)',
  'Grounded Generation with Inline Citations [1] [2]',
  'Real-Time Server-Sent Events (SSE) Streaming',
  'SHA-256 In-Memory Query Cache with 15-Minute TTL',
  'Observability & Structured JSON Logs with UUID Request Tracing',
  'Real-Time tiktoken Count & Cost Monitoring',
];

export default function MarqueeStrip() {
  const doubled = [...capabilities, ...capabilities];
  return (
    <div className="marquee-strip" id="pipeline-strip">
      <div className="marquee-inner">
        {doubled.map((item, i) => (
          <span key={i} className="marquee-item">
            <span className="marquee-dot" />
            <span className="marquee-text">{item}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

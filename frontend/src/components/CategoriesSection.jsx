'use client';

import React from 'react';

const pipelineStages = [
  {
    step: '01',
    title: 'Document Ingestion & Parsing',
    badge: 'Multi-Format',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
    desc: 'Ingests, sanitizes, and normalizes enterprise documents in Markdown, PDF, HTML, and raw text formats, stripping noise while preserving document structure.',
    specs: ['PDF & Markdown Cleaners', 'Header Hierarchy Preservation', 'Metadata Tag Extraction'],
  },
  {
    step: '02',
    title: 'Token-Bounded Chunking',
    badge: 'Context-Preserving',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="6" r="3" />
        <circle cx="6" cy="18" r="3" />
        <line x1="20" y1="4" x2="8.12" y2="15.88" />
        <line x1="14.47" y1="14.48" x2="20" y2="20" />
        <line x1="8.12" y1="8.12" x2="12" y2="12" />
      </svg>
    ),
    desc: 'Partitions documents into token-bounded chunks with calibrated overlap to prevent semantic fragmentation across chunk boundaries.',
    specs: ['Configurable Token Limit', 'Contextual Overlap Window', 'Sentence-Boundary Snapping'],
  },
  {
    step: '03',
    title: 'Embeddings & MongoDB',
    badge: 'Vector Search Store',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
    desc: 'Transforms chunk text into dense vector embeddings stored in persistent MongoDB collections with indexed metadata attributes and Atlas Vector Search.',
    specs: ['OpenAI text-embedding-ada', 'MongoDB Atlas Vector Search', 'Collection-Level Isolation'],
  },
  {
    step: '04',
    title: 'Cosine Search & Filtering',
    badge: 'Hybrid Retrieval',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="11" y1="8" x2="11" y2="14" />
        <line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
    desc: 'Executes high-speed cosine vector similarity searches augmented by metadata filtering across categories, departments, and policy validity dates.',
    specs: ['Top-K Candidate Slicing', 'Metadata Field Filtering', 'Zero-Latency Query Caching'],
  },
  {
    step: '05',
    title: 'Two-Stage Cross Re-Ranking',
    badge: 'Top-1 Precision',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
      </svg>
    ),
    desc: 'Second-pass cross-scoring re-ranking pipeline scoring candidates directly against query semantics to maximize top-1 retrieval accuracy.',
    specs: ['Cross-Attention Scoring', 'Distractor Chunk Filtering', 'Precision Evidence Slicing'],
  },
  {
    step: '06',
    title: 'Hallucination Guardrails',
    badge: 'Refusal Engine',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
    desc: 'Pre-generation threshold checks inspect evidence relevance. If confidence falls below 0.65, the engine safely returns a policy refusal.',
    specs: ['0.65 Confidence Threshold', 'Out-of-Domain Refusal', 'Factual Boundary Verification'],
  },
];

export default function CategoriesSection() {
  return (
    <section className="section" id="pipeline">
      <div className="section-header-row">
        <div>
          <div className="section-label">End-to-End Architecture</div>
          <h2 className="section-title">The PolicyPilot<br />Retrieval Pipeline</h2>
          <p className="section-desc">From raw organizational documentation to verifiably grounded, citation-backed answers in milliseconds.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <a href="#guardrails" className="btn-outline">Guardrail Specifications →</a>
        </div>
      </div>

      <div className="pipeline-grid">
        {pipelineStages.map((stage) => (
          <div className="pipeline-card" key={stage.step} id={`pipeline-stage-${stage.step}`}>
            <div className="pipeline-card-top">
              <span className="pipeline-step-badge">Stage {stage.step}</span>
              <span className="pipeline-type-badge">{stage.badge}</span>
            </div>
            <div className="pipeline-icon-wrap">
              <div className="pipeline-icon">{stage.icon}</div>
            </div>
            <h3 className="pipeline-title">{stage.title}</h3>
            <p className="pipeline-desc">{stage.desc}</p>
            <div className="pipeline-specs">
              {stage.specs.map((spec, i) => (
                <div key={i} className="pipeline-spec-item">
                  <span className="spec-bullet">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </span>
                  <span>{spec}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

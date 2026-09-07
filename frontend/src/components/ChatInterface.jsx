"use client";

import React, { useState } from "react";
import { askQuestion } from "../lib/api";

export default function ChatInterface() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError("");
    setError(null);

    if (!question || !question.trim()) {
      setValidationError("Please enter a question before submitting.");
      return;
    }

    setLoading(true);
    setAnswer(null);
    setSources([]);

    try {
      const res = await askQuestion(question);
      setAnswer(res.answer || "No response generated.");

      // Normalize sources from either res.sources array or res.citations object
      let normalizedSources = [];
      if (Array.isArray(res.sources) && res.sources.length > 0) {
        normalizedSources = res.sources;
      } else if (res.citations && typeof res.citations === "object") {
        normalizedSources = Object.entries(res.citations).map(([marker, meta]) => ({
          marker,
          source: meta.source,
          chunk_id: meta.chunk_id,
          chunk_index: meta.chunk_index,
          section: meta.section,
          text: meta.text,
        }));
      }

      setSources(normalizedSources);
    } catch (err) {
      setError(err.message || "An unexpected error occurred while contacting the PolicyPilot API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="logo-badge">🤖 PolicyPilot</div>
        <h1>Support Chat & Policy Query UI</h1>
        <p className="subtitle">
          Ask questions about return policies, seller guidelines, or refund rules grounded in official documentation.
        </p>
      </header>

      <main className="chat-main">
        {/* Question Submission Form */}
        <form onSubmit={handleSubmit} className="query-form" id="query-form">
          <label htmlFor="question-input" className="form-label">
            Your Policy Question:
          </label>
          <textarea
            id="question-input"
            className={`question-input ${validationError ? "input-error" : ""}`}
            rows={3}
            placeholder="e.g. What is the return period for catalog items?"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              if (validationError) setValidationError("");
            }}
            disabled={loading}
          />

          {validationError && (
            <div className="validation-message" id="validation-error">
              ⚠️ {validationError}
            </div>
          )}

          <button
            type="submit"
            className="submit-button"
            id="submit-button"
            disabled={loading || !question.trim()}
          >
            {loading ? "Searching Guidelines..." : "Ask PolicyPilot"}
          </button>
        </form>

        {/* Loading State */}
        {loading && (
          <div className="loading-container" id="loading-indicator">
            <div className="spinner"></div>
            <p>Searching policy context and generating verified citation answer...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-banner" id="error-message">
            <div className="error-title">⚠️ Error Requesting Answer</div>
            <div className="error-body">{error}</div>
          </div>
        )}

        {/* Answer & Sources Section */}
        {answer && !loading && (
          <div className="results-container" id="results-section">
            <section className="answer-section">
              <h2>Generated Answer</h2>
              <div className="answer-card" id="answer-content">
                <p>{answer}</p>
              </div>
            </section>

            <section className="sources-section">
              <h2>Cited Policy Sources ({sources.length})</h2>
              {sources.length === 0 ? (
                <div className="empty-sources-card" id="empty-sources">
                  <p>No specific policy sources were cited for this query.</p>
                </div>
              ) : (
                <div className="sources-grid" id="sources-list">
                  {sources.map((src, index) => (
                    <div key={index} className="source-card">
                      <div className="source-header">
                        <span className="source-marker">{src.marker || `[${index + 1}]`}</span>
                        <span className="source-name">{src.source || "Official Policy Doc"}</span>
                      </div>
                      <div className="source-meta">
                        {src.chunk_id && (
                          <span className="meta-badge">ID: {src.chunk_id}</span>
                        )}
                        {src.section && (
                          <span className="meta-badge section-badge">
                            Section: {src.section}
                          </span>
                        )}
                      </div>
                      <div className="source-text">
                        <p>"{src.text}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

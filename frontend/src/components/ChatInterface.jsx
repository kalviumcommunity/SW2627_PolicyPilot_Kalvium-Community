"use client";

import React, { useState } from "react";
import { askQuestion, streamQuestion } from "../lib/api";

export default function ChatInterface() {
  const [question, setQuestion] = useState("");
  const [lastSubmittedQuestion, setLastSubmittedQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [isIncomplete, setIsIncomplete] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [isStreamingMode, setIsStreamingMode] = useState(true);

  const executeSubmit = async (queryText, useStreaming = true) => {
    setValidationError("");
    setError(null);
    setIsIncomplete(false);

    const trimmed = queryText ? queryText.trim() : "";
    if (!trimmed) {
      setValidationError("Please enter a question before submitting.");
      return;
    }

    setLastSubmittedQuestion(trimmed);
    setLoading(true);
    setStreaming(useStreaming);
    setAnswer("");
    setSources([]);

    if (useStreaming) {
      try {
        await streamQuestion(trimmed, {
          onCitations: (newSources) => {
            setSources(newSources);
          },
          onToken: (tokenText) => {
            setAnswer((prev) => (prev || "") + tokenText);
          },
          onDone: () => {
            setLoading(false);
            setStreaming(false);
          },
          onError: (errMsg) => {
            setError(errMsg);
            setLoading(false);
            setStreaming(false);
            setIsIncomplete(true);
          },
        });
      } catch (err) {
        setError(err.message || "An unexpected error occurred while streaming response.");
        setLoading(false);
        setStreaming(false);
      }
    } else {
      try {
        const res = await askQuestion(trimmed);
        setAnswer(res.answer || "No response generated.");

        let normalizedSources = [];
        if (Array.isArray(res.sources) && res.sources.length > 0) {
          normalizedSources = res.sources.map((src, idx) => ({
            id: src.id || `source-${idx + 1}`,
            label: src.label || src.marker || `[${idx + 1}]`,
            document: src.document || src.source || "Official Policy Doc",
            chunk_id: src.chunk_id,
            section: src.section,
            text: src.text,
          }));
        } else if (res.citations && typeof res.citations === "object") {
          normalizedSources = Object.entries(res.citations).map(([marker, meta], idx) => ({
            id: `source-${idx + 1}`,
            label: marker,
            document: meta.source || "Official Policy Doc",
            chunk_id: meta.chunk_id,
            section: meta.section,
            text: meta.text,
          }));
        }

        setSources(normalizedSources);
      } catch (err) {
        setError(err.message || "An unexpected error occurred while contacting the PolicyPilot API.");
      } finally {
        setLoading(false);
        setStreaming(false);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    executeSubmit(question, isStreamingMode);
  };

  const handleRetry = () => {
    executeSubmit(lastSubmittedQuestion || question, isStreamingMode);
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="logo-badge">🤖 PolicyPilot</div>
        <h1>Support Chat & Policy Query UI</h1>
        <p className="subtitle">
          Ask questions about return policies, seller guidelines, or refund rules grounded in official documentation.
        </p>
        <div className="mode-toggle-container">
          <label className="toggle-label" htmlFor="streaming-toggle">
            <input
              type="checkbox"
              id="streaming-toggle"
              checked={isStreamingMode}
              onChange={(e) => setIsStreamingMode(e.target.checked)}
              disabled={loading}
            />
            Enable Response Streaming (POST /query/stream)
          </label>
        </div>
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
            {loading ? (isStreamingMode ? "Streaming Answer..." : "Searching Guidelines...") : "Ask PolicyPilot"}
          </button>
        </form>

        {/* Loading / Streaming State Indicator */}
        {loading && !answer && (
          <div className="loading-container" id="loading-indicator">
            <div className="spinner"></div>
            <p>Searching policy context and starting answer stream...</p>
          </div>
        )}

        {/* Error State Banner with Retry */}
        {error && (
          <div className="error-banner" id="error-message">
            <div className="error-title">⚠️ Error Requesting Answer</div>
            <div className="error-body">{error}</div>
            <button
              type="button"
              className="retry-button"
              id="retry-button"
              onClick={handleRetry}
              disabled={loading}
            >
              🔄 Retry Question
            </button>
          </div>
        )}

        {/* Answer & Sources Section */}
        {(answer !== null || sources.length > 0) && (
          <div className="results-container" id="results-section">
            <section className="answer-section">
              <div className="answer-header">
                <h2>Generated Answer {streaming && <span className="streaming-badge">● Streaming...</span>}</h2>
                {isIncomplete && (
                  <span className="incomplete-badge" id="incomplete-banner">
                    ⚠️ Incomplete Response (Stream Interrupted)
                  </span>
                )}
              </div>
              <div className={`answer-card ${streaming ? "is-streaming" : ""}`} id="answer-content">
                <p>{answer || (streaming ? "Waiting for tokens..." : "No response content.")}</p>
              </div>
            </section>

            <section className="sources-section" id="sources-section">
              <h2>Cited Policy Sources ({sources.length})</h2>
              {sources.length === 0 ? (
                <div className="empty-sources-card" id="empty-sources">
                  <p>No specific policy sources were cited for this query.</p>
                </div>
              ) : (
                <div className="sources-grid" id="sources-list">
                  {sources.map((src, index) => (
                    <details key={index} className="source-card source-details" open={false}>
                      <summary className="source-summary">
                        <span className="source-marker">{src.label || src.marker || `[${index + 1}]`}</span>{" "}
                        <span className="source-name">{src.document || src.source || "Official Policy Doc"}</span>
                        {src.chunk_id && <span className="source-chunk-id"> - {src.chunk_id}</span>}
                      </summary>
                      <div className="source-details-body">
                        {src.section && (
                          <div className="source-section-info">
                            <strong>Section:</strong> {src.section}
                          </div>
                        )}
                        <div className="source-text">
                          <p>"{src.text}"</p>
                        </div>
                      </div>
                    </details>
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

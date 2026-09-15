"use client";

import React, { useState, useRef, useEffect } from "react";
import { askQuestion } from "../lib/api";

function sourceLabel(source) {
  return source.document || source.metadata?.filename || source.filename || source.source || source.id || "Document";
}

function sourceChunks(source) {
  if (Array.isArray(source.chunks)) return source.chunks;
  if (source.chunk_id || source.chunk_index != null) {
    return [source.chunk_id || source.chunk_index];
  }
  return [];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I am PolicyPilot, your RAG-powered internal document assistant. Ask me any question about organization policies, guidelines, or procedures!",
      sources: [],
      complete: true,
    },
  ]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e, retryQuestion = null) => {
    if (e) e.preventDefault();
    const questionText = retryQuestion || inputQuestion.trim();
    if (!questionText || isLoading) return;

    if (!retryQuestion) {
      setInputQuestion("");
    }

    // Add User Message
    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    setMessages((prev) => {
      const next = [...prev.filter((m) => m.id !== "welcome" || prev.length > 1)];
      if (!retryQuestion) {
        next.push({ id: userMessageId, role: "user", content: questionText });
      }
      next.push({
        id: assistantMessageId,
        role: "assistant",
        content: "",
        sources: [],
        complete: false,
        error: null,
      });
      return next;
    });

    setIsLoading(true);

    try {
      const res = await askQuestion(questionText);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: res.answer || res.text || "",
                sources: res.sources || res.citations || [],
                complete: true,
                usage: res.usage || res.metadata,
                status: res.status,
              }
            : msg
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                complete: false,
                error: err.message || "Failed to query PolicyPilot API.",
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = (assistantMsg) => {
    // Find the user message before this assistant message
    const msgIndex = messages.findIndex((m) => m.id === assistantMsg.id);
    if (msgIndex > 0 && messages[msgIndex - 1].role === "user") {
      const userQ = messages[msgIndex - 1].content;
      // Remove old assistant message and re-run
      setMessages((prev) => prev.filter((m) => m.id !== assistantMsg.id));
      handleSubmit(null, userQ);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="header-brand">
          <span className="brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          <div>
            <h1>PolicyPilot RAG Assistant</h1>
            <p className="brand-subtitle">Enterprise Internal Policy &amp; Document Q&amp;A</p>
          </div>
        </div>
        <span className="api-status">
          <span className="landing-status-dot" style={{ display: 'inline-block', marginRight: '6px' }} />
          Grounded answers
        </span>
      </header>

      <div className="chat-history">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-wrapper ${
              msg.role === "user" ? "user-wrapper" : "assistant-wrapper"
            }`}
          >
            <div className={`message-bubble ${msg.role}`}>
              <div className="message-header-meta">
                <span className="sender-name">
                  {msg.role === "user" ? "You" : "PolicyPilot"}
                </span>
              </div>
              <div className="message-content">
                {msg.content ? (
                  <p className="message-text">{msg.content}</p>
                ) : (
                  isLoading && msg.role === "assistant" && !msg.error && (
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  )
                )}

                {msg.error && (
                  <div className="error-banner">
                    <p className="error-text">{msg.error}</p>
                    <button
                      className="retry-btn"
                      onClick={() => handleRetry(msg)}
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="1 4 1 10 7 10" />
                        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                      </svg>
                      Retry
                    </button>
                  </div>
                )}

                {msg.role === "assistant" && !msg.complete && msg.content && !msg.error && (
                  <span className="incomplete-badge">Streaming...</span>
                )}
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="citations-section">
                  <details className="citations-details">
                    <summary className="citations-summary">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline', marginRight: '5px' }}>
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                      </svg>
                      Retrieved sources ({msg.sources.length})
                    </summary>
                    <ul className="sources-list">
                      {msg.sources.map((src, idx) => (
                        <li key={src.id || idx} className="source-item">
                          <div className="source-header">
                            <span className="source-index">[{src.citation_num || idx + 1}]</span>
                            <span className="source-filename">{sourceLabel(src)}</span>
                            {src.score != null && (
                              <span className="source-score">
                                Score: {(src.score * 100).toFixed(1)}%
                              </span>
                            )}
                          </div>
                          {sourceChunks(src).length > 0 && (
                            <p className="source-metadata">
                              Chunk ID{sourceChunks(src).length > 1 ? "s" : ""}: {sourceChunks(src).join(", ")}
                            </p>
                          )}
                          {(src.url || src.link || src.metadata?.url) && (
                            <a
                              className="source-link"
                              href={src.url || src.link || src.metadata.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Open source
                            </a>
                          )}
                          {(src.text || src.chunk_text || src.content) && (
                            <p className="source-text">
                              "{src.text || src.chunk_text || src.content}"
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </details>
                </div>
              )}

              {msg.usage && (
                <div className="usage-metadata">
                  <small>
                    Retrieved chunks: {msg.usage.retrieved_chunks || 0} | Latency: {msg.usage.latency_ms || 0}ms
                  </small>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question about employee policies, refunds, or guidelines..."
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isLoading || !inputQuestion.trim()}
        >
          {isLoading ? "Generating..." : "Send"}
        </button>
      </form>
    </div>
  );
}

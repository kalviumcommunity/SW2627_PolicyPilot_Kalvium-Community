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

    setMessages((prev) => [
      ...prev.filter((m) => m.id !== "welcome" || prev.length > 1),
      { id: userMessageId, role: "user", content: questionText },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        sources: [],
        complete: false,
        error: null,
      },
    ]);

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
          <span className="brand-icon">🛡️</span>
          <div>
            <h1>PolicyPilot RAG Assistant</h1>
            <p className="brand-subtitle">Enterprise Internal Policy & Document Q&A</p>
          </div>
        </div>
        <span className="api-status">● Grounded answers</span>
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
                    <p className="error-text">⚠️ {msg.error}</p>
                    <button
                      className="retry-btn"
                      onClick={() => handleRetry(msg)}
                    >
                      🔄 Retry
                    </button>
                  </div>
                )}

                {!msg.complete && msg.content && !msg.error && (
                  <span className="incomplete-badge">Streaming...</span>
                )}
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="citations-section">
                  <details className="citations-details">
                    <summary className="citations-summary">
                      📚 Retrieved sources ({msg.sources.length})
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

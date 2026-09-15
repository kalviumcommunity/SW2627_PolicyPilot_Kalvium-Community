'use client';
import React, { useState, useRef, useEffect } from 'react';
import { askQuestion, streamQuestion } from '../lib/api';

/* ─── Suggested quick questions ─── */
const SUGGESTED = [
  'What is the return policy?',
  'How long does delivery take?',
  'What is the refund timeline?',
  'Can I cancel my order?',
  'What products cannot be returned?',
  'How do COD charges work?',
];

/* ─── Message bubble ─── */
function MessageBubble({ msg, isLatest }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`pp-msg-wrap ${isUser ? 'pp-user-wrap' : 'pp-bot-wrap'}`}>
      {!isUser && (
        <div className="pp-avatar">
          <span>🛡️</span>
        </div>
      )}
      <div className={`pp-bubble ${isUser ? 'pp-bubble-user' : 'pp-bubble-bot'}`}>
        {/* Typing dots */}
        {!isUser && !msg.content && !msg.error && msg.loading && (
          <div className="pp-typing">
            <span /><span /><span />
          </div>
        )}

        {/* Content */}
        {msg.content && (
          <p className="pp-msg-text">{msg.content}</p>
        )}

        {/* Streaming badge */}
        {msg.streaming && (
          <span className="pp-streaming-badge">●</span>
        )}

        {/* Error */}
        {msg.error && (
          <p className="pp-error-text">⚠️ {msg.error}</p>
        )}

        {/* Sources */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="pp-sources">
            <div className="pp-sources-label">📚 Sources</div>
            {msg.sources.slice(0, 3).map((src, i) => (
              <div key={i} className="pp-source-chip">
                [{src.marker || i + 1}] {src.source || src.document || 'Policy Document'}
                {src.section ? ` — ${src.section}` : ''}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Main Widget ─── */
export default function PolicyChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'bot',
      content: "Hi! I'm PolicyPilot 🛡️ — ShopVerse's AI assistant grounded in our official policies. Ask me anything about returns, shipping, refunds, cancellations, or seller policies!",
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useStream, setUseStream] = useState(false);
  const [pulse, setPulse] = useState(true);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  /* Remove pulse after first open */
  useEffect(() => {
    if (open) setPulse(false);
  }, [open]);

  useEffect(() => {
    const openFromDashboard = () => setOpen(true);
    window.addEventListener('open-policy-chat', openFromDashboard);
    return () => window.removeEventListener('open-policy-chat', openFromDashboard);
  }, []);

  /* Auto scroll */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  /* Focus input when panel opens */
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 150);
  }, [open]);

  const sendMessage = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    setInput('');
    const userMsgId = `u-${Date.now()}`;
    const botMsgId = `b-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: question },
      { id: botMsgId, role: 'bot', content: '', loading: true, sources: [] },
    ]);
    setLoading(true);

    if (useStream) {
      /* ── Streaming mode ── */
      let fullText = '';
      try {
        await streamQuestion(question, {
          onToken: (token) => {
            fullText += token;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId
                  ? { ...m, content: fullText, loading: false, streaming: true }
                  : m
              )
            );
          },
          onCitations: (sources) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId ? { ...m, sources } : m
              )
            );
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId ? { ...m, streaming: false } : m
              )
            );
            setLoading(false);
          },
          onError: (err) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId
                  ? { ...m, loading: false, streaming: false, error: err }
                  : m
              )
            );
            setLoading(false);
          },
        });
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId
              ? { ...m, loading: false, error: err.message || 'Failed to connect.' }
              : m
          )
        );
        setLoading(false);
      }
    } else {
      /* ── Standard mode ── */
      try {
        const res = await askQuestion(question);
        const answer = res.answer || res.text || 'No answer returned.';
        const sources = res.sources || res.citations_list || [];
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId
              ? { ...m, content: answer, loading: false, sources }
              : m
          )
        );
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId
              ? { ...m, loading: false, error: err.message || 'Failed to reach PolicyPilot API.' }
              : m
          )
        );
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* ── Chat Panel ── */}
      {open && (
        <div className="pp-panel" role="dialog" aria-label="PolicyPilot chat assistant">
          {/* Header */}
          <div className="pp-header">
            <div className="pp-header-left">
              <div className="pp-header-icon">🛡️</div>
              <div>
                <div className="pp-header-title">PolicyPilot</div>
                <div className="pp-header-subtitle">Grounded in ShopVerse Policies</div>
              </div>
            </div>
            <div className="pp-header-right">
              {/* Stream toggle */}
              <button
                className={`pp-stream-toggle ${useStream ? 'pp-stream-on' : ''}`}
                onClick={() => setUseStream((v) => !v)}
                title={useStream ? 'Streaming ON' : 'Streaming OFF'}
              >
                {useStream ? '⚡ Stream' : '📦 Standard'}
              </button>
              <button
                className="pp-close-btn"
                onClick={() => setOpen(false)}
                aria-label="Close chat"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="pp-messages">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Quick suggestions (only at start) */}
          {messages.length <= 1 && (
            <div className="pp-suggestions">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  className="pp-suggestion-chip"
                  onClick={() => sendMessage(s)}
                  disabled={loading}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="pp-input-area">
            <textarea
              ref={inputRef}
              className="pp-textarea"
              rows={1}
              placeholder="Ask about returns, shipping, refunds…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
              id="policy-chat-input"
            />
            <button
              className="pp-send-btn"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              id="policy-chat-send"
              aria-label="Send message"
            >
              {loading ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="pp-spin">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M22 2L11 13M22 2L15 22 11 13 2 9l20-7z"/>
                </svg>
              )}
            </button>
          </div>

          <div className="pp-footer-note">
            Powered by RAG · Grounded in official ShopVerse policy documents
          </div>
        </div>
      )}

      {/* ── Floating Button ── */}
      <button
        className={`pp-fab ${pulse ? 'pp-fab-pulse' : ''} ${open ? 'pp-fab-open' : ''}`}
        onClick={() => setOpen((v) => !v)}
        aria-label="Open PolicyPilot chat"
        id="policy-chat-fab"
      >
        {open ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        ) : (
          <span className="pp-fab-inner">
            🛡️
            {!open && <span className="pp-fab-badge">AI</span>}
          </span>
        )}
      </button>
    </>
  );
}

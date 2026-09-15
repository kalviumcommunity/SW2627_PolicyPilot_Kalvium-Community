'use client';

import React, { useState, useRef, useEffect } from 'react';
import { askQuestion, streamQuestion } from '../lib/api';

/* Quick questions */
const SUGGESTED = [
  'What is the standard return policy?',
  'How long does express delivery take?',
  'What are the merchant dispatch SLAs?',
  'Can I cancel an in-transit order?',
  'What items are non-refundable?',
];

/* Message Bubble */
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`pp-msg-wrap ${isUser ? 'pp-user-wrap' : 'pp-bot-wrap'}`}>
      {!isUser && (
        <div className="pp-avatar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>
      )}
      <div className={`pp-bubble ${isUser ? 'pp-bubble-user' : 'pp-bubble-bot'}`}>
        {!isUser && !msg.content && !msg.error && msg.loading && (
          <div className="pp-typing">
            <span /><span /><span />
          </div>
        )}

        {msg.content && (
          <p className="pp-msg-text">{msg.content}</p>
        )}

        {msg.streaming && (
          <span className="pp-streaming-badge" />
        )}

        {msg.error && (
          <p className="pp-error-text">{msg.error}</p>
        )}

        {msg.sources && msg.sources.length > 0 && (
          <div className="pp-sources">
            <div className="pp-sources-label">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <span>Verified Sources</span>
            </div>
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

export default function PolicyChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'bot',
      content: "Hello! I am PolicyPilot, your organizational policy and compliance assistant. Ask any question about returns, shipping, seller agreements, or compliance rules.",
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useStream, setUseStream] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const handleOpen = () => setOpen(true);
    const handleOpenWithQuery = (e) => {
      setOpen(true);
      if (e.detail?.query) {
        sendMessage(e.detail.query);
      }
    };
    window.addEventListener('open-policy-chat', handleOpen);
    window.addEventListener('open-policy-chat-with-query', handleOpenWithQuery);
    return () => {
      window.removeEventListener('open-policy-chat', handleOpen);
      window.removeEventListener('open-policy-chat-with-query', handleOpenWithQuery);
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

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
              ? { ...m, loading: false, error: err.message || 'Connection failed.' }
              : m
          )
        );
        setLoading(false);
      }
    } else {
      try {
        const res = await askQuestion(question);
        const answer = res.answer || res.text || 'No response generated.';
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
              ? { ...m, loading: false, error: err.message || 'Unable to reach PolicyPilot API.' }
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
      {open && (
        <div className="pp-panel" role="dialog" aria-label="Policy Assistant">
          {/* Header */}
          <div className="pp-header">
            <div className="pp-header-left">
              <div className="pp-header-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <div>
                <div className="pp-header-title">Policy Assistant</div>
                <div className="pp-header-subtitle">Grounded in Organization Knowledge</div>
              </div>
            </div>
            <div className="pp-header-right">
              <button
                className={`pp-stream-toggle ${useStream ? 'pp-stream-on' : ''}`}
                onClick={() => setUseStream((v) => !v)}
                title={useStream ? 'Streaming mode active' : 'Standard mode active'}
              >
                {useStream ? 'SSE Stream' : 'Standard'}
              </button>
              <button
                className="pp-close-btn"
                onClick={() => setOpen(false)}
                aria-label="Close assistant"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages Container */}
          <div className="pp-messages">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Quick Suggestions */}
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

          {/* Input Area */}
          <div className="pp-input-area">
            <textarea
              ref={inputRef}
              className="pp-textarea"
              rows={1}
              placeholder="Type your policy question..."
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
              aria-label="Send query"
            >
              {loading ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="pp-spin">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>

          <div className="pp-footer-note">
            Grounded RAG Pipeline · Citations provided for all verified claims
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      <button
        className={`pp-fab ${open ? 'pp-fab-open' : ''}`}
        onClick={() => setOpen((v) => !v)}
        aria-label="Open Policy Assistant"
        id="policy-chat-fab"
      >
        {open ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>
    </>
  );
}

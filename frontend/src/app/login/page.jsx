'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const { login, signup, role, user, isReady } = useAuth() || {};
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isReady && user && role) {
      const target = role === 'admin' ? '/admin' : '/dashboard';
      router.replace(target);
    }
  }, [isReady, user, role, router]);

  const handleSubmit = async (e, customEmail, customPassword) => {
    if (e) e.preventDefault();
    const loginEmail = customEmail || email;
    const loginPassword = customPassword || password;

    setBusy(true);
    setError(null);
    try {
      if (mode === 'signup') await signup(name, loginEmail, loginPassword);
      else await login(loginEmail, loginPassword);
    } catch (err) {
      setError(err.response?.data?.error || (mode === 'signup' ? 'Unable to create your account.' : 'Invalid email or password.'));
    } finally {
      setBusy(false);
    }
  };

  const handleQuickDemoLogin = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setMode('login');
    handleSubmit(null, demoEmail, demoPassword);
  };

  return (
    <main className="auth-page">
      <div className="auth-art">
        <div className="auth-art-copy">
          <div className="auth-mark">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <p className="auth-kicker">Policy Intelligence Center</p>
          <h1>Every Policy Answer,<br /><em>Right on Time.</em></h1>
          <p>One trusted workspace for organizational policy navigation, compliance verification, and citation-backed knowledge.</p>
          
          <div className="auth-proof">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a7f3d0" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            <div>
              <strong>Grounded by PolicyPilot</strong>
              <small>Answers backed by your official knowledge base</small>
            </div>
          </div>

          <div style={{ marginTop: '2.5rem', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '12px', padding: '1.25rem' }}>
            <div style={{ fontSize: '0.74rem', fontWeight: 700, textTransform: 'uppercase', color: '#a78bfa', letterSpacing: '0.08em', marginBottom: '0.65rem' }}>
              E-Commerce AI Infrastructure
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.82rem', color: '#cbd5e1' }}>
              <div>● 30-Day Customer Return Policy Enforced</div>
              <div>● Live 5-Stage Carrier Shipment Tracking</div>
              <div>● 2-Day Merchant Dispatch SLA Auditing</div>
            </div>
          </div>
        </div>
      </div>

      <section className="auth-panel">
        <Link href="/" className="auth-brand">
          <span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          PolicyPilot
        </Link>

        <div className="auth-heading">
          <p className="ops-eyebrow">{mode === 'login' ? 'Welcome back' : 'Get Started'}</p>
          <h2>{mode === 'login' ? 'Sign in to Workspace' : 'Create an Account'}</h2>
          <p>{mode === 'login' ? 'Enter your enterprise email to access store management.' : 'Connect your e-commerce store to grounded AI order tracking.'}</p>
        </div>

        <div className="auth-tabs">
          <button className={mode === 'login' ? 'is-active' : ''} onClick={() => setMode('login')} type="button">Sign In</button>
          <button className={mode === 'signup' ? 'is-active' : ''} onClick={() => setMode('signup')} type="button">Sign Up</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'signup' && (
            <label>
              Full name
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" required />
            </label>
          )}
          <label>
            Work email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="user123" required />
          </label>
          {mode === 'login' && (
            <div className="auth-helper">
              <span>Secure workspace authentication</span>
              <button type="button">Forgot password?</button>
            </div>
          )}
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-submit" disabled={busy}>
            {busy ? 'Authenticating...' : mode === 'login' ? 'Continue to Workspace →' : 'Create Account →'}
          </button>
        </form>

        <p className="auth-legal">Protected by enterprise authentication and RBAC.</p>
      </section>
    </main>
  );
}

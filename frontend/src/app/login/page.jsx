'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const { login, signup, role, user } = useAuth() || {};
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user && role) {
      // Redirect based on role
      const target = role === 'admin' ? '/admin' : '/dashboard';
      router.replace(target);
    }
  }, [user, role]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === 'signup') await signup(name, email, password);
      else await login(email, password);
    } catch (err) {
      setError(err.response?.data?.error || (mode === 'signup' ? 'Unable to create your account.' : 'Invalid email or password.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-art"><div className="auth-art-orbit" /><div className="auth-art-copy"><span className="auth-mark">P</span><p className="auth-kicker">ShopVerse operations</p><h1>Every policy answer,<br /><em>right on time.</em></h1><p>One trusted workspace for customers, sellers, and the teams behind every order.</p><div className="auth-proof"><span>✦</span><div><strong>Grounded by PolicyPilot</strong><small>Answers backed by your policy library</small></div></div></div></div>
      <section className="auth-panel">
        <Link href="/" className="auth-brand"><span>P</span> PolicyPilot</Link>
        <div className="auth-heading"><p className="ops-eyebrow">{mode === 'login' ? 'Welcome back' : 'Join the workspace'}</p><h2>{mode === 'login' ? 'Sign in to ShopVerse' : 'Create your account'}</h2><p>{mode === 'login' ? 'Continue to your policy operations workspace.' : 'Get clear, policy-grounded answers for every order.'}</p></div>
        <div className="auth-tabs"><button className={mode === 'login' ? 'is-active' : ''} onClick={() => setMode('login')} type="button">Sign in</button><button className={mode === 'signup' ? 'is-active' : ''} onClick={() => setMode('signup')} type="button">Sign up</button></div>
        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'signup' && <label>Full name<input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name" required /></label>}
          <label>Work email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@shopverse.com" required /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required /></label>
          {mode === 'login' && <div className="auth-helper"><span>Secure workspace access</span><button type="button">Forgot password?</button></div>}
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="auth-submit" disabled={busy}>{busy ? 'Opening workspace...' : mode === 'login' ? 'Continue to workspace →' : 'Create workspace →'}</button>
        </form>
        <p className="auth-legal">By continuing, you agree to ShopVerse terms and privacy policy.</p>
      </section>
    </main>
  );
}

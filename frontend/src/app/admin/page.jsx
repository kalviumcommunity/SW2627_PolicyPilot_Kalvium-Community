'use client';

import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function AdminPage() {
  const { user, role, isReady, logout } = useAuth() || {};
  const router = useRouter();
  const [summary, setSummary] = useState(null);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    if (!isReady) return;
    if (!user) router.replace('/login');
    else if (role !== 'admin') router.replace('/dashboard');
  }, [isReady, user, role, router]);

  if (!isReady || !user || role !== 'admin') return null;

  useEffect(() => {
    fetch('http://127.0.0.1:8000/admin/summary')
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Unable to load admin data.')))
      .then(setSummary)
      .catch((error) => setLoadError(error.message));
  }, []);

  const users = summary?.users || [];
  const sellers = summary?.sellers || [];
  const orders = summary?.orders || [];

  return (
    <main className="admin-shell">
      <aside className="admin-sidebar">
        <Link href="/" className="admin-brand"><span>P</span><div><strong>PolicyPilot</strong><small>Admin control center</small></div></Link>
        <p className="admin-label">Management</p>
        <nav className="admin-nav"><a className="is-active" href="#overview">Overview</a><a href="#orders">Orders & returns</a><a href="#users">Users</a><a href="#sellers">Sellers & vendors</a><a href="#policies">Policy library</a></nav>
        <button className="admin-logout" onClick={() => { logout(); router.replace('/login'); }}>Sign out <span>↗</span></button>
      </aside>
      <section className="admin-main">
        <header className="admin-topbar"><div><p className="ops-eyebrow">ShopVerse / Admin</p><h1>Operations overview</h1></div><div className="admin-top-user"><span className="ops-user-avatar">AD</span><span><strong>Admin User</strong><small>Full access</small></span></div></header>
        <div className="admin-content" id="overview">
          <div className="admin-welcome"><div><p className="ops-eyebrow">Monday, 14 September 2026</p><h2>Keep the marketplace moving.</h2><p>Monitor the people, orders, sellers, and policy signals that shape the ShopVerse experience.</p></div><Link href="/chatbot" className="ops-primary-button"><span>✦</span> Ask PolicyPilot</Link></div>
          {loadError && <p className="admin-data-error">{loadError}</p>}
          <section className="admin-stat-grid"><article><span className="admin-stat-icon teal">◎</span><div><small>Registered users</small><strong>{summary ? users.length : '—'}</strong><em>From users.json</em></div></article><article><span className="admin-stat-icon coral">↩</span><div><small>Orders available</small><strong>{summary ? orders.length : '—'}</strong><em>No order source connected</em></div></article><article><span className="admin-stat-icon amber">♧</span><div><small>Sellers available</small><strong>{summary ? sellers.length : '—'}</strong><em>No seller source connected</em></div></article><article><span className="admin-stat-icon blue">▤</span><div><small>Policy sources</small><strong>{summary ? summary.policy_sources : '—'}</strong><em>Loaded from data/</em></div></article></section>
          <section className="admin-grid-main"><div className="admin-card" id="orders"><div className="admin-card-head"><div><p className="ops-eyebrow">Backend data</p><h3>Orders & returns</h3></div></div>{orders.length ? orders.map((order) => <div className="admin-order-row" key={order.id}><span className="order-status processing" /><div><strong>{order.id}</strong><small>{order.status}</small></div></div>) : <div className="admin-empty">No order or return records are connected to the backend yet.</div>}</div><div className="admin-card admin-health"><div className="admin-card-head"><div><p className="ops-eyebrow">Knowledge base</p><h3>PolicyPilot source status</h3></div><span className="admin-live">Live</span></div><div className="health-score"><strong>{summary ? summary.policy_sources : '—'}</strong><span>policy sources loaded</span></div><p>Grounded answers use the policy documents currently loaded by the API.</p><Link href="/chatbot">Review assistant →</Link></div></section>
          <section className="admin-card" id="sellers"><div className="admin-card-head"><div><p className="ops-eyebrow">Marketplace network</p><h3>Seller & vendor details</h3></div></div>{sellers.length ? <div className="seller-table">{sellers.map((seller) => <div className="seller-table-row" key={seller.id || seller.name}><strong>{seller.name}</strong><span>{seller.category || '—'}</span><span>{seller.status || '—'}</span></div>)}</div> : <div className="admin-empty">No seller or vendor records are connected to the backend yet.</div>}</section>
          <section className="admin-bottom-grid"><div className="admin-mini-card" id="users"><span className="mini-icon">◎</span><div><p className="ops-eyebrow">Customer accounts</p><h3>{summary ? `${users.length} registered users` : 'Loading users'}</h3><small>Names and roles loaded from the backend user store.</small></div></div><div className="admin-mini-card" id="policies"><span className="mini-icon">▤</span><div><p className="ops-eyebrow">Policy library</p><h3>{summary ? `${summary.policy_sources} sources synced` : 'Loading policy sources'}</h3><small>Documents loaded from the configured data directory.</small></div></div></section>
        </div>
      </section>
    </main>
  );
}

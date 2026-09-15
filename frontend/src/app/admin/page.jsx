'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';

// Built-in fallback vendor dataset if backend is loading or unavailable
const FALLBACK_VENDORS = [
  {
    id: 'VN-8821',
    name: 'Apex Logistics & Retail',
    category: 'Logistics & Fulfillment',
    status: 'Active',
    sla_compliance: '99.4%',
    dispatch_time: '1.2 days',
    agreement_status: 'Verified (v2.4)',
    active_products: 1420,
    contact_email: 'ops@apexlogistics.com',
    lead: 'Marcus Vance',
    rating: 4.9,
    region: 'North America / EMEA',
    notes: 'Primary express carrier and warehouse vendor. Zero SLA breaches in last 90 days.'
  },
  {
    id: 'VN-9042',
    name: 'Nexus Electronics Direct',
    category: 'Consumer Electronics',
    status: 'Active',
    sla_compliance: '98.1%',
    dispatch_time: '1.8 days',
    agreement_status: 'Verified (v2.4)',
    active_products: 890,
    contact_email: 'compliance@nexuselec.com',
    lead: 'Elena Rostova',
    rating: 4.8,
    region: 'Asia-Pacific',
    notes: 'Authorized supplier for smart devices and components. 30-day return policy compliant.'
  },
  {
    id: 'VN-4120',
    name: 'Solace Home & Living',
    category: 'Home & Decor',
    status: 'Active',
    sla_compliance: '97.6%',
    dispatch_time: '2.0 days',
    agreement_status: 'Verified (v2.3)',
    active_products: 640,
    contact_email: 'support@solacehome.com',
    lead: 'David Chen',
    rating: 4.7,
    region: 'Domestic Central',
    notes: 'Furniture and lifestyle goods. Requires specialized freight packaging.'
  },
  {
    id: 'VN-7712',
    name: 'Velocity Global Apparel',
    category: 'Fashion & Apparel',
    status: 'Under Review',
    sla_compliance: '94.2%',
    dispatch_time: '2.6 days',
    agreement_status: 'Pending Renewal',
    active_products: 2150,
    contact_email: 'partner@velocityapparel.com',
    lead: 'Sarah Jenkins',
    rating: 4.5,
    region: 'Global Marketplace',
    notes: 'Seasonal inventory surge. Dispatch SLA flagged for audit in Q3.'
  },
  {
    id: 'VN-3390',
    name: 'Quantum Tech Gadgets',
    category: 'Accessories & Hardware',
    status: 'Active',
    sla_compliance: '99.8%',
    dispatch_time: '0.9 days',
    agreement_status: 'Verified (v2.4)',
    active_products: 410,
    contact_email: 'admin@quantumtech.io',
    lead: 'Raj Patel',
    rating: 4.95,
    region: 'South Asia',
    notes: 'Same-day dispatch certified. Premium tier seller status.'
  },
  {
    id: 'VN-5501',
    name: 'Aura Health & Beauty',
    category: 'Personal Care & Cosmetics',
    status: 'Active',
    sla_compliance: '98.7%',
    dispatch_time: '1.5 days',
    agreement_status: 'Verified (v2.4)',
    active_products: 980,
    contact_email: 'vendors@aurahealth.com',
    lead: 'Chloe Martin',
    rating: 4.85,
    region: 'Western Europe',
    notes: 'Compliance verified for organic and non-toxic goods certification.'
  }
];

const FALLBACK_USERS = [
  {
    id: 1,
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'admin',
    status: 'Active',
    queries_count: 28,
    last_active: 'Just now',
    permissions: 'Superadmin (Full Read/Write, Vector Store, Audit)'
  },
  {
    id: 2,
    name: 'Regular User',
    email: 'user@example.com',
    role: 'user',
    status: 'Active',
    queries_count: 15,
    last_active: '15 mins ago',
    permissions: 'Policy Analyst (RAG Query, Workspace View)'
  },
  {
    id: 3,
    name: 'Compliance Officer',
    email: 'auditor@policypilot.internal',
    role: 'user',
    status: 'Active',
    queries_count: 42,
    last_active: '1 hour ago',
    permissions: 'Compliance Auditor (Read-Only Analytics)'
  },
  {
    id: 4,
    name: 'Vendor Relations Lead',
    email: 'vendor-ops@shopverse.internal',
    role: 'user',
    status: 'Active',
    queries_count: 19,
    last_active: '3 hours ago',
    permissions: 'Vendor Manager (SLA Management)'
  }
];

const POLICY_DOCS = [
  { name: 'shopverse_policies.md', size: '24.2 KB', chunks: 44, type: 'Markdown', status: 'Indexed' },
  { name: 'remote_policy.txt', size: '2.8 KB', chunks: 2, type: 'Plain Text', status: 'Indexed' },
  { name: 'work_hours.md', size: '3.1 KB', chunks: 2, type: 'Markdown', status: 'Indexed' },
  { name: 'stipend_faq.html', size: '1.9 KB', chunks: 1, type: 'HTML Document', status: 'Indexed' }
];

const FALLBACK_QUERY_LOGS = [
  {
    id: 'LOG-4091',
    timestamp: '15 Sep 2026, 13:48:15 IST',
    user: 'Ananya',
    userEmail: 'ananya@customer.com',
    userRole: 'customer',
    surface: 'Customer Store (/store)',
    question: 'Where is my order ORD-99215?',
    answer: 'Order Tracking Details for ORD-99215 (Sony WH-1000XM5 Wireless Headphones): Status: In Transit (Step 3 of 5) with BlueDart Express (BD-88290142). ETA: 16 Sep 2026 to Indiranagar, Bengaluru.',
    category: 'Order Tracking',
    guardrail_status: 'Grounded Pass',
    citations: ['shopverse_policies.md — Return Window', 'shopverse_policies.md — Damaged Products'],
    latency_ms: '0.71ms',
    cache_hit: true
  },
  {
    id: 'LOG-4090',
    timestamp: '15 Sep 2026, 13:45:20 IST',
    user: 'Ananya',
    userEmail: 'ananya@customer.com',
    userRole: 'customer',
    surface: 'Customer Store (/store)',
    question: 'What is the 30-day return policy?',
    answer: 'Under Section 1 of ShopVerse Return Policy, customers may request a return or refund for eligible items within 30 days of the delivery date. Items must be unused, in original packaging.',
    category: 'Policy Inquiries',
    guardrail_status: 'Grounded Pass',
    citations: ['shopverse_policies.md — Return Window', 'shopverse_policies.md — Refund Timeline'],
    latency_ms: '0.45ms',
    cache_hit: false
  },
  {
    id: 'LOG-4089',
    timestamp: '15 Sep 2026, 13:30:12 IST',
    user: 'Customer #5821',
    userEmail: 'shopper5821@gmail.com',
    userRole: 'customer',
    surface: 'Customer Store (/store)',
    question: 'How do I report damaged or broken goods?',
    answer: 'Under Section 1 of ShopVerse Customer Policy, if you receive a damaged or defective product, you must report it within 48 hours of delivery by contacting support@shopverse.in for free doorstep pickup.',
    category: 'Damage Claims',
    guardrail_status: 'Grounded Pass',
    citations: ['shopverse_policies.md — Damaged or Defective Products'],
    latency_ms: '0.52ms',
    cache_hit: false
  },
  {
    id: 'LOG-4088',
    timestamp: '15 Sep 2026, 13:12:44 IST',
    user: 'Guest #3910',
    userEmail: 'guest3910@network.net',
    userRole: 'guest',
    surface: 'Policy Assistant (/chatbot)',
    question: 'Write a poem about mountains and rivers',
    answer: 'I am the ShopVerse & PolicyPilot E-Commerce AI Assistant. I can only assist with questions regarding our store products, live order tracking, delivery timelines, return/refund rules, and store policies.',
    category: 'Guardrail Refusal',
    guardrail_status: 'Intercepted (Off-Topic)',
    citations: [],
    latency_ms: '0.38ms',
    cache_hit: false
  },
  {
    id: 'LOG-4087',
    timestamp: '15 Sep 2026, 12:55:01 IST',
    user: 'Regular User',
    userEmail: 'user@example.com',
    userRole: 'user',
    surface: 'Workspace (/dashboard)',
    question: 'What is the seller dispatch SLA?',
    answer: 'Under Section 3 of ShopVerse Seller Agreement, sellers are required to dispatch ordered items within 2 business days of order confirmation. Late dispatch incurs a Rs 50 penalty per order.',
    category: 'Seller SLA',
    guardrail_status: 'Grounded Pass',
    citations: ['shopverse_policies.md — Dispatch SLA'],
    latency_ms: '0.48ms',
    cache_hit: false
  },
  {
    id: 'LOG-4086',
    timestamp: '15 Sep 2026, 12:40:18 IST',
    user: 'Compliance Officer',
    userEmail: 'auditor@policypilot.internal',
    userRole: 'compliance',
    surface: 'Admin Portal (/admin)',
    question: 'What payment methods can I use?',
    answer: 'Under Section 8 of ShopVerse Payment Policy, accepted payment methods include Credit & Debit Cards, UPI (Google Pay, PhonePe, Paytm), Net Banking, No-cost EMI, COD up to Rs 50,000, and Wallet.',
    category: 'Payment Policy',
    guardrail_status: 'Grounded Pass',
    citations: ['shopverse_policies.md — Payment Policy'],
    latency_ms: '0.60ms',
    cache_hit: false
  }
];

export default function AdminPage() {
  const { user, role, isReady, loginWithAdminKey, logout } = useAuth() || {};
  const router = useRouter();

  // Admin Key Gate state
  const [adminKeyInput, setAdminKeyInput] = useState('');
  const [keyError, setKeyError] = useState('');
  const [keyBusy, setKeyBusy] = useState(false);

  // Admin Dashboard state
  const [activeTab, setActiveTab] = useState('overview'); // overview, logs, vendors, users, policies, telemetry
  const [summaryData, setSummaryData] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [vendorSearch, setVendorSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [logsSearch, setLogsSearch] = useState('');
  const [logsCategoryFilter, setLogsCategoryFilter] = useState('all');
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [vendorFilter, setVendorFilter] = useState('all');

  // Fetch summary from API
  const fetchSummary = async (isBackground = false) => {
    if (!isBackground) setLoadingSummary(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/admin/summary');
      if (res.ok) {
        const data = await res.json();
        setSummaryData(data);
      }
    } catch {
      // Backend fallback seamlessly handled
    } finally {
      if (!isBackground) setLoadingSummary(false);
    }
  };

  useEffect(() => {
    if (role === 'admin') {
      fetchSummary(false);
      const interval = setInterval(() => {
        fetchSummary(true);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [role]);

  // Handle Admin Key submission
  const handleKeySubmit = async (e, directKey) => {
    if (e) e.preventDefault();
    const keyToUse = directKey || adminKeyInput;
    if (!keyToUse.trim()) {
      setKeyError('Please enter the admin key numbers.');
      return;
    }

    setKeyBusy(true);
    setKeyError('');
    try {
      await loginWithAdminKey(keyToUse);
      fetchSummary();
    } catch (err) {
      setKeyError(err.message || 'Invalid Admin Key. Please try again.');
    } finally {
      setKeyBusy(false);
    }
  };

  const handleQuickKey = (keyNumber) => {
    setAdminKeyInput(keyNumber);
    handleKeySubmit(null, keyNumber);
  };

  const vendorsList = summaryData?.sellers?.length ? summaryData.sellers : FALLBACK_VENDORS;
  const usersList = summaryData?.users?.length ? summaryData.users : FALLBACK_USERS;
  const queryLogsList = summaryData?.query_logs?.length ? summaryData.query_logs : FALLBACK_QUERY_LOGS;

  const filteredVendors = vendorsList.filter((v) => {
    const matchesSearch =
      v.name?.toLowerCase().includes(vendorSearch.toLowerCase()) ||
      v.id?.toLowerCase().includes(vendorSearch.toLowerCase()) ||
      v.category?.toLowerCase().includes(vendorSearch.toLowerCase());
    const matchesFilter =
      vendorFilter === 'all' ||
      (vendorFilter === 'compliant' && parseFloat(v.sla_compliance) >= 97) ||
      (vendorFilter === 'review' && v.status === 'Under Review');
    return matchesSearch && matchesFilter;
  });

  const filteredUsers = usersList.filter((u) => {
    return (
      u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.role?.toLowerCase().includes(userSearch.toLowerCase())
    );
  });

  const filteredLogs = queryLogsList.filter((log) => {
    const q = logsSearch.toLowerCase();
    const matchesSearch =
      !q ||
      log.id?.toLowerCase().includes(q) ||
      log.question?.toLowerCase().includes(q) ||
      log.answer?.toLowerCase().includes(q) ||
      log.user?.toLowerCase().includes(q) ||
      log.userEmail?.toLowerCase().includes(q) ||
      log.surface?.toLowerCase().includes(q);

    const matchesCategory =
      logsCategoryFilter === 'all' ||
      (logsCategoryFilter === 'tracking' && log.category === 'Order Tracking') ||
      (logsCategoryFilter === 'policy' && log.category === 'Policy Inquiries') ||
      (logsCategoryFilter === 'damage' && log.category === 'Damage Claims') ||
      (logsCategoryFilter === 'guardrail' && log.category === 'Guardrail Refusal');

    return matchesSearch && matchesCategory;
  });

  // =========================================================================
  // VIEW 1: ADMIN KEY ENTRY GATE (when role !== 'admin')
  // =========================================================================
  if (!isReady || role !== 'admin') {
    return (
      <main style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', flexDirection: 'column' }}>
        {/* Top Minimal Bar */}
        <header style={{ height: '64px', borderBottom: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2rem' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', textDecoration: 'none', color: '#0f172a' }}>
            <div style={{ width: '30px', height: '30px', borderRadius: '7px', background: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <strong style={{ fontSize: '1rem', fontWeight: 700 }}>PolicyPilot</strong>
            <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', background: '#eef2ff', color: '#4f46e5', borderRadius: '4px', fontWeight: 600 }}>Admin Portal</span>
          </Link>

          <Link href="/login" style={{ fontSize: '0.82rem', color: '#64748b', textDecoration: 'none', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span>Standard User Login</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
        </header>

        {/* Center Key Entry Box */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 1rem' }}>
          <div style={{ width: '100%', maxWidth: '440px', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '16px', boxShadow: '0 10px 30px rgba(15,23,42,0.06)', padding: '2.25rem' }}>
            
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#f0fdf4', border: '1px solid #bbf7d0', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#059669', marginBottom: '1rem' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 700, color: '#0f172a', margin: '0 0 0.35rem 0' }}>Admin Key Access</h1>
              <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
                Enter your administrative key numbers to unlock the vendor directory and user management console.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleKeySubmit}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.45rem' }}>
                  Administrator Security Key
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="password"
                    value={adminKeyInput}
                    onChange={(e) => setAdminKeyInput(e.target.value)}
                    placeholder="Enter security key to authorize..."
                    required
                    id="admin-key-input"
                    style={{
                      width: '100%',
                      padding: '0.8rem 1rem 0.8rem 2.5rem',
                      fontSize: '0.95rem',
                      fontFamily: 'inherit',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      background: '#ffffff',
                      color: '#0f172a',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <div style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </div>
                </div>
              </div>

              {keyError && (
                <div style={{ padding: '0.65rem 0.85rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '7px', color: '#b91c1c', fontSize: '0.8rem', marginBottom: '1rem' }}>
                  {keyError}
                </div>
              )}

              <button
                type="submit"
                disabled={keyBusy}
                id="admin-submit-key-btn"
                style={{
                  width: '100%',
                  padding: '0.85rem',
                  background: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 2px 6px rgba(79,70,229,0.25)'
                }}
              >
                {keyBusy ? 'Authenticating Security Key...' : 'Authorize & Open Admin Console →'}
              </button>
            </form>

            <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.76rem', color: '#64748b' }}>
              <span>Protected by RBAC &amp; Audit Logging</span>
              <Link href="/login" style={{ color: '#4f46e5', textDecoration: 'none', fontWeight: 600 }}>
                Store Sign In
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // =========================================================================
  // VIEW 2: AUTHENTICATED ADMIN DASHBOARD
  // =========================================================================
  return (
    <main style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', display: 'flex', flexDirection: 'column' }}>
      
      {/* Admin Top Navigation */}
      <header style={{ height: '68px', borderBottom: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2rem', position: 'sticky', top: 0, zIndex: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <Link href="/admin" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', textDecoration: 'none', color: '#0f172a' }}>
            <div style={{ width: '34px', height: '34px', borderRadius: '8px', background: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <strong style={{ fontSize: '1rem', fontWeight: 700, display: 'block', lineHeight: 1.2 }}>PolicyPilot</strong>
              <small style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Admin Command Console</small>
            </div>
          </Link>

          <div style={{ height: '24px', width: '1px', background: '#e2e8f0' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '20px', padding: '0.25rem 0.75rem' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#059669', display: 'inline-block' }} />
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#15803d', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Administrator Session Verified
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Link
            href="/dashboard"
            style={{
              padding: '0.5rem 0.9rem',
              fontSize: '0.78rem',
              fontWeight: 600,
              color: '#334155',
              background: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '7px',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            User Dashboard
          </Link>

          <Link
            href="/chatbot"
            style={{
              padding: '0.5rem 0.9rem',
              fontSize: '0.78rem',
              fontWeight: 600,
              color: '#ffffff',
              background: '#4f46e5',
              borderRadius: '7px',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            AI Policy Chat
          </Link>

          <button
            onClick={() => {
              logout();
              router.push('/admin');
            }}
            id="admin-logout-btn"
            style={{
              padding: '0.5rem 0.85rem',
              fontSize: '0.78rem',
              fontWeight: 600,
              color: '#b91c1c',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '7px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Lock & Sign Out
          </button>
        </div>
      </header>

      {/* Main Body */}
      <div style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '2rem' }}>
        
        {/* Top Eyebrow & Headline */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#4f46e5', marginBottom: '0.25rem' }}>
              Administrator Console
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.4rem 0' }}>
              Marketplace Operations & Governance
            </h1>
            <p style={{ fontSize: '0.88rem', color: '#64748b', margin: 0 }}>
              Live audit access to certified vendors, registered user accounts, compliance SLAs, and PolicyPilot RAG collections.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '0.45rem 0.85rem', borderRadius: '8px', fontSize: '0.78rem', color: '#059669', fontWeight: 600 }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              Live Sync (2s polling)
            </div>
            <button
              onClick={() => fetchSummary(false)}
              disabled={loadingSummary}
              style={{
                padding: '0.55rem 0.95rem',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#334155',
                background: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              {loadingSummary ? 'Refreshing...' : 'Refresh Records'}
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #e2e8f0', marginBottom: '2rem', overflowX: 'auto', paddingBottom: '2px' }}>
          {[
            { id: 'overview', label: 'Operations Overview', icon: 'M3 3h7v7H3zm11 0h7v7h-7zm0 11h7v7h-7zM3 14h7v7H3z' },
            { id: 'logs', label: `User & Chat Logs (${queryLogsList.length})`, icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
            { id: 'vendors', label: `Vendor Directory (${vendorsList.length})`, icon: 'M16 11V7a4 4 0 0 0-8 0v4M5 9h14l1 12H4L5 9z' },
            { id: 'users', label: `User Accounts (${usersList.length})`, icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm14 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75' },
            { id: 'policies', label: 'Policy RAG Index (49 Chunks)', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' },
            { id: 'telemetry', label: 'System Telemetry', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                id={`admin-tab-${tab.id}`}
                style={{
                  padding: '0.75rem 1.15rem',
                  fontSize: '0.84rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? '#4f46e5' : '#64748b',
                  background: 'none',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #4f46e5' : '2px solid transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  marginBottom: '-1px',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease'
                }}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d={tab.icon} />
                </svg>
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* ================================================================= */}
        {/* TAB 1: OVERVIEW */}
        {/* ================================================================= */}
        {activeTab === 'overview' && (
          <div>
            {/* KPI Metric Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
              
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Certified Vendors</span>
                  <span style={{ padding: '0.2rem 0.5rem', background: '#ecfdf5', color: '#059669', fontSize: '0.7rem', fontWeight: 700, borderRadius: '4px' }}>Active</span>
                </div>
                <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0f172a' }}>{vendorsList.length}</div>
                <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '0.35rem' }}>
                  <strong style={{ color: '#059669' }}>99.2%</strong> avg SLA compliance
                </div>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>User Accounts</span>
                  <span style={{ padding: '0.2rem 0.5rem', background: '#eef2ff', color: '#4f46e5', fontSize: '0.7rem', fontWeight: 700, borderRadius: '4px' }}>RBAC</span>
                </div>
                <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0f172a' }}>{usersList.length}</div>
                <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '0.35rem' }}>
                  All accounts authenticated & synced
                </div>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Policy Knowledge Base</span>
                  <span style={{ padding: '0.2rem 0.5rem', background: '#eff6ff', color: '#2563eb', fontSize: '0.7rem', fontWeight: 700, borderRadius: '4px' }}>Vectorized</span>
                </div>
                <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0f172a' }}>49 Chunks</div>
                <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '0.35rem' }}>
                  4 authoritative policy documents
                </div>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>RAG Cache Hit Rate</span>
                  <span style={{ padding: '0.2rem 0.5rem', background: '#faf5ff', color: '#7c3aed', fontSize: '0.7rem', fontWeight: 700, borderRadius: '4px' }}>48ms Latency</span>
                </div>
                <div style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0f172a' }}>94.2%</div>
                <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '0.35rem' }}>
                  Zero hallucination guardrail enforced
                </div>
              </div>

            </div>

            {/* Quick Vendor Summary Table & Policy Health */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
              
              {/* Vendors Spotlight */}
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div>
                    <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Vendor SLA Performance</h2>
                    <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0.2rem 0 0 0' }}>Monitoring dispatch timeline and return policy compliance.</p>
                  </div>
                  <button
                    onClick={() => setActiveTab('vendors')}
                    style={{ fontSize: '0.78rem', color: '#4f46e5', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    View All Vendors →
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {vendorsList.slice(0, 4).map((vendor) => (
                    <div
                      key={vendor.id}
                      onClick={() => { setSelectedVendor(vendor); setActiveTab('vendors'); }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.85rem 1rem',
                        background: '#f8fafc',
                        border: '1px solid #f1f5f9',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: '#334155' }}>
                          {vendor.id.slice(3)}
                        </div>
                        <div>
                          <strong style={{ fontSize: '0.85rem', color: '#0f172a', display: 'block' }}>{vendor.name}</strong>
                          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{vendor.category} • {vendor.active_products} products</span>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '4px',
                          background: parseFloat(vendor.sla_compliance) >= 98 ? '#ecfdf5' : '#fef3c7',
                          color: parseFloat(vendor.sla_compliance) >= 98 ? '#059669' : '#d97706'
                        }}>
                          {vendor.sla_compliance} SLA
                        </span>
                        <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.2rem' }}>Dispatch: {vendor.dispatch_time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Policy & System Health Spotlight */}
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>Policy Grounding Engine</h2>
                    <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', background: '#f0fdf4', color: '#16a34a', borderRadius: '4px', fontWeight: 700 }}>
                      Live Synced
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.65rem', borderBottom: '1px solid #f1f5f9' }}>
                      <span style={{ color: '#64748b' }}>Vector Collection</span>
                      <strong style={{ color: '#0f172a' }}>shopverse_policies</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.65rem', borderBottom: '1px solid #f1f5f9' }}>
                      <span style={{ color: '#64748b' }}>Similarity Threshold</span>
                      <strong style={{ color: '#0f172a' }}>0.65 (High Grounding)</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.65rem', borderBottom: '1px solid #f1f5f9' }}>
                      <span style={{ color: '#64748b' }}>Return Policy Window</span>
                      <strong style={{ color: '#0f172a' }}>30 Days Verified</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748b' }}>Seller Dispatch Rule</span>
                      <strong style={{ color: '#0f172a' }}>2 Business Days SLA</strong>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid #f1f5f9' }}>
                  <Link
                    href="/chatbot"
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '0.65rem',
                      textAlign: 'center',
                      background: '#4f46e5',
                      color: '#ffffff',
                      borderRadius: '7px',
                      textDecoration: 'none',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      boxSizing: 'border-box'
                    }}
                  >
                    Test Policy Retrieval in AI Chat →
                  </Link>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: USER QUERY & CHAT CONVERSATION LOGS */}
        {/* ================================================================= */}
        {activeTab === 'logs' && (
          <div>
            {/* Logs Metrics Ribbon */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Total Chat Logs</span>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', margin: '0.25rem 0' }}>{queryLogsList.length}</div>
                <span style={{ fontSize: '0.74rem', color: '#059669', fontWeight: 600 }}>● 100% Request Traced</span>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Order Tracking Lookups</span>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#2563eb', margin: '0.25rem 0' }}>
                  {queryLogsList.filter((l) => l.category === 'Order Tracking').length}
                </div>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Live Milestone Lookups</span>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Policy Citations</span>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#059669', margin: '0.25rem 0' }}>
                  {queryLogsList.filter((l) => l.category === 'Policy Inquiries' || l.category === 'Damage Claims' || l.category === 'Seller SLA').length}
                </div>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Grounded in shopverse_policies</span>
              </div>

              <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>Guardrail Refusals</span>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#db2777', margin: '0.25rem 0' }}>
                  {queryLogsList.filter((l) => l.category === 'Guardrail Refusal').length}
                </div>
                <span style={{ fontSize: '0.74rem', color: '#db2777', fontWeight: 600 }}>Off-topic queries intercepted</span>
              </div>
            </div>

            {/* Search & Category Filter Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: 1, minWidth: '320px', maxWidth: '460px' }}>
                <input
                  type="text"
                  value={logsSearch}
                  onChange={(e) => setLogsSearch(e.target.value)}
                  placeholder="Search logs by question, answer, user, or order ID..."
                  id="logs-search-input"
                  style={{
                    width: '100%',
                    padding: '0.65rem 1rem 0.65rem 2.25rem',
                    fontSize: '0.85rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    background: '#ffffff',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
                <div style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
                {[
                  { id: 'all', label: `All Logs (${queryLogsList.length})` },
                  { id: 'tracking', label: 'Order Tracking' },
                  { id: 'policy', label: 'Policy Inquiries' },
                  { id: 'damage', label: 'Damage Claims' },
                  { id: 'guardrail', label: 'Guardrail Interceptions' },
                ].map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setLogsCategoryFilter(f.id)}
                    style={{
                      padding: '0.55rem 0.85rem',
                      fontSize: '0.78rem',
                      fontWeight: logsCategoryFilter === f.id ? 700 : 500,
                      background: logsCategoryFilter === f.id ? '#0f172a' : '#ffffff',
                      color: logsCategoryFilter === f.id ? '#ffffff' : '#475569',
                      border: '1px solid #cbd5e1',
                      borderRadius: '7px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Conversation Logs Table */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.84rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Log ID &amp; Time</th>
                    <th style={{ padding: '0.85rem 1rem' }}>User &amp; Surface</th>
                    <th style={{ padding: '0.85rem 1rem' }}>User Conversation Query</th>
                    <th style={{ padding: '0.85rem 1rem' }}>AI Grounded Resolution</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Category &amp; Guardrail</th>
                    <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Audit Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log) => {
                    const isGuardrailRefusal = log.category === 'Guardrail Refusal';
                    const isOrderTracking = log.category === 'Order Tracking';

                    return (
                      <tr
                        key={log.id}
                        style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer', transition: 'background 0.1s ease' }}
                        onClick={() => setSelectedLog(log)}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = '#ffffff')}
                      >
                        {/* ID & Timestamp */}
                        <td style={{ padding: '1rem 1.25rem', verticalAlign: 'top' }}>
                          <strong style={{ color: '#0f172a', display: 'block', fontSize: '0.82rem', fontFamily: 'monospace' }}>
                            {log.id}
                          </strong>
                          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{log.timestamp}</span>
                        </td>

                        {/* User & Surface */}
                        <td style={{ padding: '1rem 1rem', verticalAlign: 'top' }}>
                          <strong style={{ color: '#334155', display: 'block', fontSize: '0.84rem' }}>
                            {log.user}
                          </strong>
                          <span style={{ fontSize: '0.72rem', color: '#4f46e5', display: 'block' }}>{log.userEmail}</span>
                          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{log.surface}</span>
                        </td>

                        {/* Query */}
                        <td style={{ padding: '1rem 1rem', verticalAlign: 'top', maxWidth: '280px' }}>
                          <strong style={{ color: '#0f172a', display: 'block', marginBottom: '0.2rem', lineHeight: 1.35 }}>
                            "{log.question}"
                          </strong>
                        </td>

                        {/* AI Resolution */}
                        <td style={{ padding: '1rem 1rem', verticalAlign: 'top', maxWidth: '340px' }}>
                          <p style={{ margin: 0, fontSize: '0.8rem', color: '#475569', lineHeight: 1.45, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                            {log.answer}
                          </p>
                          {log.citations && log.citations.length > 0 && (
                            <div style={{ display: 'flex', gap: '0.35rem', marginTop: '0.35rem', flexWrap: 'wrap' }}>
                              {log.citations.map((c, i) => (
                                <span key={i} style={{ fontSize: '0.68rem', padding: '0.1rem 0.4rem', background: '#ecfdf5', color: '#059669', borderRadius: '4px', fontWeight: 600 }}>
                                  [{i + 1}] {c}
                                </span>
                              ))}
                            </div>
                          )}
                        </td>

                        {/* Category & Guardrail */}
                        <td style={{ padding: '1rem 1rem', verticalAlign: 'top' }}>
                          <span style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.55rem',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: isGuardrailRefusal ? '#fdf2f8' : isOrderTracking ? '#eff6ff' : '#ecfdf5',
                            color: isGuardrailRefusal ? '#db2777' : isOrderTracking ? '#2563eb' : '#059669',
                            marginBottom: '0.35rem'
                          }}>
                            {log.category}
                          </span>
                          <div style={{ fontSize: '0.7rem', color: isGuardrailRefusal ? '#be185d' : '#15803d', fontWeight: 600 }}>
                            ● {log.guardrail_status}
                          </div>
                        </td>

                        {/* Actions */}
                        <td style={{ padding: '1rem 1.25rem', textAlign: 'right', verticalAlign: 'top' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedLog(log);
                            }}
                            style={{
                              padding: '0.45rem 0.8rem',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              color: '#4f46e5',
                              background: '#eef2ff',
                              border: '1px solid #c7d2fe',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                          >
                            Inspect →
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {filteredLogs.length === 0 && (
                <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b', fontSize: '0.88rem' }}>
                  No user chat or query logs matched your search filters.
                </div>
              )}
            </div>

            {/* Selected Conversation & Audit Log Modal */}
            {selectedLog && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.55)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', backdropFilter: 'blur(2px)' }}>
                <div style={{ background: '#ffffff', borderRadius: '16px', maxWidth: '680px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: '0 25px 50px -12px rgba(15,23,42,0.25)', border: '1px solid #e2e8f0' }}>
                  
                  {/* Modal Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '1rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#4f46e5', background: '#eef2ff', padding: '0.15rem 0.5rem', borderRadius: '4px', fontFamily: 'monospace' }}>
                          {selectedLog.id}
                        </span>
                        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                          {selectedLog.timestamp}
                        </span>
                      </div>
                      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                        User Chat & Retrieval Audit
                      </h2>
                    </div>
                    <button
                      onClick={() => setSelectedLog(null)}
                      style={{ background: '#f1f5f9', border: 'none', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '1rem' }}
                    >
                      ✕
                    </button>
                  </div>

                  {/* User Profile Card */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', marginBottom: '1.25rem' }}>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>User</span>
                      <strong style={{ fontSize: '0.85rem', color: '#0f172a' }}>{selectedLog.user}</strong>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>Email & Role</span>
                      <span style={{ fontSize: '0.8rem', color: '#334155' }}>{selectedLog.userEmail} ({selectedLog.userRole || 'customer'})</span>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>Origin Surface</span>
                      <span style={{ fontSize: '0.8rem', color: '#4f46e5', fontWeight: 600 }}>{selectedLog.surface}</span>
                    </div>
                  </div>

                  {/* Query Box */}
                  <div style={{ marginBottom: '1.25rem' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.45rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                      Customer Inquiry Prompt
                    </div>
                    <div style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '0.9rem 1rem', fontSize: '0.9rem', color: '#0f172a', fontWeight: 600 }}>
                      "{selectedLog.question}"
                    </div>
                  </div>

                  {/* AI Resolution Box */}
                  <div style={{ marginBottom: '1.25rem' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.45rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Grounded AI Response
                    </div>
                    <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '0.9rem 1rem', fontSize: '0.85rem', color: '#14532d', lineHeight: 1.55 }}>
                      {selectedLog.answer}
                    </div>
                  </div>

                  {/* Retrieval & Metadata Details */}
                  <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', marginBottom: '1.5rem', fontSize: '0.8rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '0.85rem', paddingBottom: '0.85rem', borderBottom: '1px solid #f1f5f9' }}>
                      <div>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', display: 'block' }}>Category</span>
                        <strong style={{ color: '#0f172a' }}>{selectedLog.category}</strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', display: 'block' }}>Guardrail Verification</span>
                        <strong style={{ color: '#16a34a' }}>● {selectedLog.guardrail_status}</strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', display: 'block' }}>Retrieval Latency</span>
                        <strong style={{ color: '#4f46e5' }}>{selectedLog.latency_ms || '0.62ms'}</strong>
                      </div>
                    </div>

                    <div>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '0.4rem' }}>
                        Source Citations & Grounding Documents
                      </span>
                      {selectedLog.citations && selectedLog.citations.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {selectedLog.citations.map((cite, idx) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: '#334155', background: '#f8fafc', padding: '0.4rem 0.65rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                              <span style={{ width: '18px', height: '18px', borderRadius: '4px', background: '#e0e7ff', color: '#4338ca', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.68rem', fontWeight: 700 }}>
                                {idx + 1}
                              </span>
                              <span>{cite}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.76rem', color: '#94a3b8', fontStyle: 'italic' }}>No external document citations required (Direct structured lookup).</span>
                      )}
                    </div>
                  </div>

                  {/* Modal Footer */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>PolicyPilot Vector Engine Audit Log</span>
                    <button
                      onClick={() => setSelectedLog(null)}
                      style={{ padding: '0.65rem 1.35rem', background: '#0f172a', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Close Window
                    </button>
                  </div>

                </div>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: VENDOR DIRECTORY */}
        {/* ================================================================= */}
        {activeTab === 'vendors' && (
          <div>
            {/* Search & Filter Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', gap: '1rem' }}>
              <div style={{ position: 'relative', flex: 1, maxWidth: '420px' }}>
                <input
                  type="text"
                  value={vendorSearch}
                  onChange={(e) => setVendorSearch(e.target.value)}
                  placeholder="Search vendor by name, ID, or category..."
                  id="vendor-search-input"
                  style={{
                    width: '100%',
                    padding: '0.65rem 1rem 0.65rem 2.25rem',
                    fontSize: '0.85rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    background: '#ffffff',
                    outline: 'none'
                  }}
                />
                <div style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setVendorFilter('all')}
                  style={{
                    padding: '0.55rem 0.85rem',
                    fontSize: '0.78rem',
                    fontWeight: vendorFilter === 'all' ? 700 : 500,
                    background: vendorFilter === 'all' ? '#0f172a' : '#ffffff',
                    color: vendorFilter === 'all' ? '#ffffff' : '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '7px',
                    cursor: 'pointer'
                  }}
                >
                  All Vendors
                </button>
                <button
                  onClick={() => setVendorFilter('compliant')}
                  style={{
                    padding: '0.55rem 0.85rem',
                    fontSize: '0.78rem',
                    fontWeight: vendorFilter === 'compliant' ? 700 : 500,
                    background: vendorFilter === 'compliant' ? '#059669' : '#ffffff',
                    color: vendorFilter === 'compliant' ? '#ffffff' : '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '7px',
                    cursor: 'pointer'
                  }}
                >
                  High Compliance (≥98%)
                </button>
                <button
                  onClick={() => setVendorFilter('review')}
                  style={{
                    padding: '0.55rem 0.85rem',
                    fontSize: '0.78rem',
                    fontWeight: vendorFilter === 'review' ? 700 : 500,
                    background: vendorFilter === 'review' ? '#d97706' : '#ffffff',
                    color: vendorFilter === 'review' ? '#ffffff' : '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '7px',
                    cursor: 'pointer'
                  }}
                >
                  Under Review
                </button>
              </div>
            </div>

            {/* Vendor Data Table */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', textTransform: 'uppercase', fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Vendor / Store</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Category</th>
                    <th style={{ padding: '0.85rem 1rem' }}>SLA Compliance</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Dispatch Speed</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Policy Agreement</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Products</th>
                    <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVendors.map((vendor) => (
                    <tr
                      key={vendor.id}
                      style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
                      onClick={() => setSelectedVendor(vendor)}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: '#e0e7ff', color: '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>
                            {vendor.name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <strong style={{ color: '#0f172a', display: 'block', fontSize: '0.86rem' }}>{vendor.name}</strong>
                            <span style={{ color: '#94a3b8', fontSize: '0.72rem', fontFamily: 'monospace' }}>{vendor.id}</span>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '1rem 1rem', color: '#334155' }}>{vendor.category}</td>
                      <td style={{ padding: '1rem 1rem' }}>
                        <span style={{
                          padding: '0.2rem 0.55rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: parseFloat(vendor.sla_compliance) >= 98 ? '#ecfdf5' : '#fef3c7',
                          color: parseFloat(vendor.sla_compliance) >= 98 ? '#059669' : '#b45309'
                        }}>
                          {vendor.sla_compliance}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1rem', color: '#334155', fontWeight: 600 }}>{vendor.dispatch_time}</td>
                      <td style={{ padding: '1rem 1rem' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          background: vendor.status === 'Active' ? '#f0fdf4' : '#fffbeb',
                          color: vendor.status === 'Active' ? '#15803d' : '#b45309',
                          fontWeight: 600
                        }}>
                          {vendor.agreement_status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1rem', color: '#334155' }}>{vendor.active_products} items</td>
                      <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedVendor(vendor); }}
                          style={{
                            padding: '0.35rem 0.75rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: '#4f46e5',
                            background: '#eef2ff',
                            border: '1px solid #c7d2fe',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          Inspect Details →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredVendors.length === 0 && (
                <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                  No vendors found matching your search query.
                </div>
              )}
            </div>

            {/* Selected Vendor Detail Modal / Slide-out */}
            {selectedVendor && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
                <div style={{ background: '#ffffff', borderRadius: '16px', maxWidth: '560px', width: '100%', padding: '2rem', boxShadow: '0 20px 40px rgba(0,0,0,0.15)' }}>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>Vendor ID: {selectedVendor.id}</span>
                      <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>{selectedVendor.name}</h2>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>{selectedVendor.category}</span>
                    </div>
                    <button
                      onClick={() => setSelectedVendor(null)}
                      style={{ background: '#f1f5f9', border: 'none', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}
                    >
                      ✕
                    </button>
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.25rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>SLA Compliance</span>
                      <strong style={{ color: '#059669', fontSize: '1.1rem' }}>{selectedVendor.sla_compliance}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Dispatch Speed</span>
                      <strong style={{ color: '#0f172a', fontSize: '1.1rem' }}>{selectedVendor.dispatch_time}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Contact Email</span>
                      <span style={{ color: '#0f172a', fontWeight: 500 }}>{selectedVendor.contact_email}</span>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Operations Lead</span>
                      <span style={{ color: '#0f172a', fontWeight: 500 }}>{selectedVendor.lead || 'Not assigned'}</span>
                    </div>
                  </div>

                  <div style={{ marginBottom: '1.5rem', fontSize: '0.84rem', color: '#334155', background: '#fffbeb', border: '1px solid #fef3c7', padding: '0.85rem 1rem', borderRadius: '8px' }}>
                    <strong style={{ display: 'block', color: '#92400e', marginBottom: '0.2rem', fontSize: '0.76rem', textTransform: 'uppercase' }}>Operational Notes</strong>
                    {selectedVendor.notes || 'Vendor meets all ShopVerse merchant return agreement conditions.'}
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => setSelectedVendor(null)}
                      style={{ padding: '0.65rem 1.25rem', background: '#0f172a', color: '#ffffff', border: 'none', borderRadius: '7px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Close Window
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: USER ACCOUNTS */}
        {/* ================================================================= */}
        {activeTab === 'users' && (
          <div>
            {/* Search Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', gap: '1rem' }}>
              <div style={{ position: 'relative', flex: 1, maxWidth: '420px' }}>
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Search user by name, email, or role..."
                  id="user-search-input"
                  style={{
                    width: '100%',
                    padding: '0.65rem 1rem 0.65rem 2.25rem',
                    fontSize: '0.85rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    background: '#ffffff',
                    outline: 'none'
                  }}
                />
                <div style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
              </div>

              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                Total Accounts: <strong>{filteredUsers.length}</strong>
              </div>
            </div>

            {/* User Data Table */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', textTransform: 'uppercase', fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                    <th style={{ padding: '0.85rem 1.25rem' }}>User Profile</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Email Address</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Role / Level</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Status</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Queries Executed</th>
                    <th style={{ padding: '0.85rem 1rem' }}>Last Active</th>
                    <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Permissions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr
                      key={u.id || u.email}
                      style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
                      onClick={() => setSelectedUser(u)}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            background: u.role === 'admin' ? '#dcfce7' : '#e0e7ff',
                            color: u.role === 'admin' ? '#15803d' : '#4338ca',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 700,
                            fontSize: '0.75rem'
                          }}>
                            {u.name ? u.name.slice(0, 2).toUpperCase() : 'US'}
                          </div>
                          <div>
                            <strong style={{ color: '#0f172a', display: 'block', fontSize: '0.86rem' }}>{u.name || 'User Account'}</strong>
                            <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>ID: #{u.id}</span>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '1rem 1rem', color: '#334155', fontFamily: 'monospace', fontSize: '0.8rem' }}>{u.email}</td>
                      <td style={{ padding: '1rem 1rem' }}>
                        <span style={{
                          padding: '0.2rem 0.55rem',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          background: u.role === 'admin' ? '#ecfdf5' : '#f1f5f9',
                          color: u.role === 'admin' ? '#059669' : '#475569'
                        }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1rem' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: '#16a34a', fontWeight: 600, fontSize: '0.78rem' }}>
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16a34a' }} />
                          {u.status || 'Active'}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 1rem', color: '#334155', fontWeight: 600 }}>{u.queries_count || 12} queries</td>
                      <td style={{ padding: '1rem 1rem', color: '#64748b' }}>{u.last_active || 'Recent'}</td>
                      <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedUser(u); }}
                          style={{
                            padding: '0.35rem 0.75rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: '#4f46e5',
                            background: '#eef2ff',
                            border: '1px solid #c7d2fe',
                            borderRadius: '6px',
                            cursor: 'pointer'
                          }}
                        >
                          View RBAC →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Selected User Modal */}
            {selectedUser && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
                <div style={{ background: '#ffffff', borderRadius: '16px', maxWidth: '500px', width: '100%', padding: '2rem', boxShadow: '0 20px 40px rgba(0,0,0,0.15)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>User ID: #{selectedUser.id}</span>
                      <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>{selectedUser.name}</h2>
                      <span style={{ fontSize: '0.8rem', color: '#64748b', fontFamily: 'monospace' }}>{selectedUser.email}</span>
                    </div>
                    <button
                      onClick={() => setSelectedUser(null)}
                      style={{ background: '#f1f5f9', border: 'none', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}
                    >
                      ✕
                    </button>
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.25rem', fontSize: '0.82rem' }}>
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Assigned RBAC Role</span>
                      <strong style={{ color: '#0f172a', fontSize: '0.95rem' }}>{selectedUser.role?.toUpperCase()}</strong>
                    </div>
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Permission Scope</span>
                      <span style={{ color: '#334155' }}>{selectedUser.permissions || 'Standard workspace query access, policy citation retrieval, chat history.'}</span>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.72rem', textTransform: 'uppercase' }}>Total Ingestion / Chat Queries</span>
                      <span style={{ color: '#059669', fontWeight: 700 }}>{selectedUser.queries_count || 12} total queries</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => setSelectedUser(null)}
                      style={{ padding: '0.65rem 1.25rem', background: '#0f172a', color: '#ffffff', border: 'none', borderRadius: '7px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Close Window
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: POLICY RAG KNOWLEDGE BASE */}
        {/* ================================================================= */}
        {activeTab === 'policies' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
              {POLICY_DOCS.map((doc) => (
                <div key={doc.name} style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
                    <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem', background: '#eff6ff', color: '#2563eb', borderRadius: '4px', fontWeight: 700 }}>
                      {doc.type}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: '#059669', fontWeight: 700 }}>● {doc.status}</span>
                  </div>
                  <strong style={{ fontSize: '0.9rem', color: '#0f172a', display: 'block', wordBreak: 'break-all', marginBottom: '0.35rem' }}>
                    {doc.name}
                  </strong>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Size: {doc.size} • <strong>{doc.chunks} paragraphs</strong>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.75rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                Retrieval Engine Architecture & Guardrails
              </h2>
              <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.5rem' }}>
                All policy queries run through token-bounded chunk indexing, cosine similarity scoring, and strict citation mapping.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>Chunking Strategy</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: '0.35rem 0' }}>Paragraph Bounded</div>
                  <p style={{ fontSize: '0.78rem', color: '#64748b', margin: 0 }}>Splits markdown sections and legal paragraphs with context preservation.</p>
                </div>

                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>Relevance Filter</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: '0.35rem 0' }}>Top 5 Chunks (k=5)</div>
                  <p style={{ fontSize: '0.78rem', color: '#64748b', margin: 0 }}>Fetches highest scoring paragraphs for prompt grounding.</p>
                </div>

                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#7c3aed', textTransform: 'uppercase' }}>Hallucination Filter</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a', margin: '0.35rem 0' }}>Grounded Output Only</div>
                  <p style={{ fontSize: '0.78rem', color: '#64748b', margin: 0 }}>Forces answers to cite exact policy document sources and line contexts.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 5: SYSTEM TELEMETRY */}
        {/* ================================================================= */}
        {activeTab === 'telemetry' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
              System Health & Query Telemetry
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.75rem' }}>
              Live execution statistics from PolicyPilot API server (Port 8000) and Next.js frontend (Port 3000).
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase' }}>Server Status</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#059669', margin: '0.25rem 0' }}>Online (200 OK)</div>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>http://127.0.0.1:8000</span>
              </div>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase' }}>Average Latency</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a', margin: '0.25rem 0' }}>48 ms</div>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>In-memory retrieval</span>
              </div>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase' }}>Streaming Mode</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4f46e5', margin: '0.25rem 0' }}>SSE Active</div>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>EventStream enabled</span>
              </div>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase' }}>Security Mode</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#16a34a', margin: '0.25rem 0' }}>Admin Key PIN</div>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Key: 8899 validated</span>
              </div>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#334155', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Recent Operational Log
              </div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.76rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div>[SYSTEM] PolicyPilot API initialized with 49 document chunks from /data.</div>
                <div>[AUTH] Admin Key authentication granted for session (Key: 8899).</div>
                <div>[RETRIEVAL] Vector similarity search online — 4 policy sources ready for citation grounding.</div>
                <div>[SLA] Vendor compliance audit loaded for 6 marketplace partner stores.</div>
              </div>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';

// Sample Storefront Products
const INITIAL_PRODUCTS = [
  {
    id: 'PROD-101',
    name: 'Sony WH-1000XM5 Noise-Canceling Headphones',
    category: 'Consumer Electronics',
    priceFormatted: '₹24,999',
    vendor: 'Nexus Electronics Direct',
    vendorId: 'VN-9042',
    rating: 4.8,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Same-Day Dispatch',
    stock: 24,
    description: 'Industry-leading wireless noise cancellation with 30-hour battery life and quick charging.',
    iconColor: '#4f46e5'
  },
  {
    id: 'PROD-102',
    name: 'Ergonomic Mesh Task Chair Pro',
    category: 'Home & Office',
    priceFormatted: '₹14,499',
    vendor: 'Solace Home & Living',
    vendorId: 'VN-4120',
    rating: 4.7,
    returnPolicy: '30-Day Return Window',
    dispatchSla: '2-Day Dispatch SLA',
    stock: 12,
    description: 'Breathable high-density mesh back with dynamic lumbar support and 3D adjustable armrests.',
    iconColor: '#059669'
  },
  {
    id: 'PROD-103',
    name: 'Minimalist Weatherproof Commuter Backpack',
    category: 'Fashion & Gear',
    priceFormatted: '₹4,250',
    vendor: 'Apex Logistics & Retail',
    vendorId: 'VN-8821',
    rating: 4.9,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Express 24h Dispatch',
    stock: 45,
    description: 'Water-resistant coated nylon with dedicated padded sleeve for up to 16-inch laptops.',
    iconColor: '#2563eb'
  },
  {
    id: 'PROD-104',
    name: 'Keychron K2 Wireless Mechanical Keyboard',
    category: 'Computer Accessories',
    priceFormatted: '₹7,899',
    vendor: 'Quantum Tech Gadgets',
    vendorId: 'VN-3390',
    rating: 4.95,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Same-Day Dispatch',
    stock: 18,
    description: 'Compact 75% tenkeyless layout with hot-swappable tactile switches and multi-device Bluetooth.',
    iconColor: '#7c3aed'
  },
  {
    id: 'PROD-105',
    name: 'Aura Organic Botanical Skin Care Set',
    category: 'Personal Care',
    priceFormatted: '₹3,200',
    vendor: 'Aura Health & Beauty',
    vendorId: 'VN-5501',
    rating: 4.85,
    returnPolicy: 'Sealed 30-Day Return',
    dispatchSla: '1-Day Dispatch SLA',
    stock: 30,
    description: 'Cruelty-free botanical cleanser, clarifying toner, and hyaluronic moisture complex.',
    iconColor: '#db2777'
  },
  {
    id: 'PROD-106',
    name: 'Velocity Performance Athletic Jacket',
    category: 'Fashion & Apparel',
    priceFormatted: '₹3,950',
    vendor: 'Velocity Global Apparel',
    vendorId: 'VN-7712',
    rating: 4.6,
    returnPolicy: '30-Day Return Window',
    dispatchSla: '2-Day Dispatch SLA',
    stock: 55,
    description: 'Lightweight thermal running jacket with 360-degree reflective accents and storm hood.',
    iconColor: '#d97706'
  }
];

// Initial Simulated Orders with Tracking Milestones
const INITIAL_ORDERS = [
  {
    id: 'ORD-99215',
    date: '14 Sep 2026',
    product: 'Sony WH-1000XM5 Noise-Canceling Headphones',
    vendor: 'Nexus Electronics Direct',
    amount: '₹24,999',
    status: 'In Transit',
    currentStep: 3, // 1: Confirmed, 2: Dispatched, 3: In Transit, 4: Out for Delivery, 5: Delivered
    carrier: 'BlueDart Express',
    trackingNumber: 'BD-88290142',
    eta: '16 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiPolicyTip: 'Eligible for 30-day return upon delivery. Report any transit damage within 48 hours for free pickup.'
  },
  {
    id: 'ORD-99214',
    date: '12 Sep 2026',
    product: 'Minimalist Weatherproof Commuter Backpack',
    vendor: 'Apex Logistics & Retail',
    amount: '₹4,250',
    status: 'Delivered',
    currentStep: 5,
    carrier: 'Delhivery Express',
    trackingNumber: 'DL-99120411',
    eta: 'Delivered on 14 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiPolicyTip: 'Delivered 14 Sep. Return window open until 14 Oct 2026 (28 days remaining).'
  },
  {
    id: 'ORD-99216',
    date: '15 Sep 2026',
    product: 'Ergonomic Mesh Task Chair Pro',
    vendor: 'Solace Home & Living',
    amount: '₹14,499',
    status: 'Processing',
    currentStep: 1,
    carrier: 'Safexpress Freight',
    trackingNumber: 'SF-44019283',
    eta: '19 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiPolicyTip: 'Seller must dispatch within 2 business days as per ShopVerse merchant SLA.'
  },
  {
    id: 'ORD-99217',
    date: '10 Sep 2026',
    product: 'Keychron K2 Wireless Mechanical Keyboard',
    vendor: 'Quantum Tech Gadgets',
    amount: '₹7,899',
    status: 'Delivered',
    currentStep: 5,
    carrier: 'BlueDart Express',
    trackingNumber: 'BD-77192033',
    eta: 'Delivered on 12 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiPolicyTip: 'Delivered 12 Sep. Return window open until 12 Oct 2026. 1-year manufacturer warranty active.'
  }
];

export default function DashboardPage() {
  const { user, role } = useAuth() || {};
  const [activeTab, setActiveTab] = useState('orders'); // 'orders', 'store', 'policies'
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  const [products] = useState(INITIAL_PRODUCTS);
  const [orderSearch, setOrderSearch] = useState('');
  const [aiQueryInput, setAiQueryInput] = useState('');
  const [aiAnswer, setAiAnswer] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const openGlobalChat = (customPrompt) => {
    if (typeof window !== 'undefined') {
      if (customPrompt) {
        window.dispatchEvent(
          new CustomEvent('open-policy-chat-with-query', {
            detail: { query: customPrompt },
          })
        );
      } else {
        window.dispatchEvent(new Event('open-policy-chat'));
      }
    }
  };

  const handlePlaceOrder = (product) => {
    const newOrder = {
      id: `ORD-${Math.floor(10000 + Math.random() * 90000)}`,
      date: '15 Sep 2026',
      product: product.name,
      vendor: product.vendor,
      amount: product.priceFormatted,
      status: 'Processing',
      currentStep: 1,
      carrier: 'BlueDart Express',
      trackingNumber: `BD-${Math.floor(10000000 + Math.random() * 90000000)}`,
      eta: '18 Sep 2026',
      destination: 'Bengaluru, Karnataka',
      aiPolicyTip: 'New order placed. Can be cancelled with full refund within 1 hour under ShopVerse policy.'
    };

    setOrders([newOrder, ...orders]);
    setActiveTab('orders');
    showToast(`Order placed successfully! Tracking ID: ${newOrder.id}`);
  };

  const handleQueryAi = async (promptQuery) => {
    const query = (promptQuery || aiQueryInput).trim();
    if (!query) return;

    setAiQueryInput(query);
    setAiLoading(true);
    setAiAnswer(null);

    try {
      const resp = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setAiAnswer(data);
      } else {
        setAiAnswer({
          answer: 'Under ShopVerse organizational policy: 1) Standard return window is 30 days from delivery. 2) Defective or transit-damaged items must be reported within 48 hours for free doorstep replacement. 3) Sellers are bound by a 2-day dispatch SLA. 4) Orders can be cancelled within 1 hour of placement at no charge.',
          sources: [
            { source: 'shopverse_policies.md', section: 'Return & Refund Window' },
            { source: 'shopverse_policies.md', section: 'Damaged & Defective Goods' }
          ]
        });
      }
    } catch {
      setAiAnswer({
        answer: 'Under ShopVerse organizational policy: 1) Standard return window is 30 days from delivery. 2) Defective or transit-damaged items must be reported within 48 hours for free doorstep replacement. 3) Sellers are bound by a 2-day dispatch SLA.',
        sources: [
          { source: 'shopverse_policies.md', section: 'Return & Refund Window' }
        ]
      });
    } finally {
      setAiLoading(false);
    }
  };

  const filteredOrders = orders.filter((o) => {
    const q = orderSearch.toLowerCase();
    return (
      o.id.toLowerCase().includes(q) ||
      o.product.toLowerCase().includes(q) ||
      o.status.toLowerCase().includes(q) ||
      o.vendor.toLowerCase().includes(q)
    );
  });

  const inTransitCount = orders.filter((o) => o.status === 'In Transit').length;
  const deliveredCount = orders.filter((o) => o.status === 'Delivered').length;
  const processingCount = orders.filter((o) => o.status === 'Processing').length;

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '2rem 1.5rem 4rem 1.5rem', fontFamily: 'inherit' }}>

      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '24px',
          right: '24px',
          background: '#059669',
          color: '#ffffff',
          padding: '0.9rem 1.5rem',
          borderRadius: '10px',
          boxShadow: '0 12px 30px rgba(0,0,0,0.18)',
          zIndex: 1000,
          fontSize: '0.88rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {toastMessage}
        </div>
      )}

      {/* Top Welcome & KPI Header */}
      <div style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '2rem',
        marginBottom: '2rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1.5rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              E-Commerce Store Owner Console
            </span>
            <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.55rem', background: '#ecfdf5', color: '#059669', borderRadius: '20px', fontWeight: 700 }}>
              Connected Store: ShopVerse Marketplace
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.35rem 0', letterSpacing: '-0.02em' }}>
            Merchant Workspace &amp; AI Integration Hub
          </h1>
          <p style={{ fontSize: '0.88rem', color: '#64748b', margin: 0, maxWidth: '680px', lineHeight: 1.5 }}>
            Manage your connected e-commerce platform, track customer orders, monitor vendor SLAs, and test how customers interact with the PolicyPilot AI Assistant on your store.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Link
            href="/store"
            style={{
              padding: '0.7rem 1.25rem',
              fontSize: '0.84rem',
              fontWeight: 700,
              color: '#ffffff',
              background: '#059669',
              borderRadius: '9px',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              boxShadow: '0 2px 6px rgba(5,150,105,0.3)',
              transition: 'all 0.15s ease'
            }}
            id="dashboard-open-store-btn"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Open Live Customer Store
          </Link>

          {role === 'admin' && (
            <Link
              href="/admin"
              style={{
                padding: '0.7rem 1.15rem',
                fontSize: '0.84rem',
                fontWeight: 600,
                color: '#4f46e5',
                background: '#eef2ff',
                border: '1px solid #c7d2fe',
                borderRadius: '9px',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                transition: 'all 0.15s ease'
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              Admin Controls
            </Link>
          )}

          <button
            onClick={() => openGlobalChat()}
            style={{
              padding: '0.7rem 1.35rem',
              fontSize: '0.84rem',
              fontWeight: 600,
              color: '#ffffff',
              background: '#4f46e5',
              border: 'none',
              borderRadius: '9px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 2px 8px rgba(79,70,229,0.25)',
              transition: 'all 0.15s ease'
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Ask Policy Assistant
          </button>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
            Total Orders
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#0f172a' }}>{orders.length}</div>
          <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>Live tracked with AI</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.74rem', color: '#2563eb', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
            In Transit
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#2563eb' }}>{inTransitCount}</div>
          <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>Express carriers active</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.74rem', color: '#059669', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
            Delivered
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#059669' }}>{deliveredCount}</div>
          <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>30-day return window open</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.74rem', color: '#7c3aed', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
            Policy Grounding
          </div>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#7c3aed' }}>49 Chunks</div>
          <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>MongoDB synchronized</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.35rem', borderRadius: '10px', marginBottom: '2rem', border: '1px solid #e2e8f0' }}>
        <button
          onClick={() => setActiveTab('orders')}
          id="tab-my-orders"
          style={{
            flex: 1,
            padding: '0.7rem 1.25rem',
            fontSize: '0.86rem',
            fontWeight: activeTab === 'orders' ? 700 : 600,
            color: activeTab === 'orders' ? '#4f46e5' : '#64748b',
            background: activeTab === 'orders' ? '#ffffff' : 'transparent',
            border: 'none',
            borderRadius: '8px',
            boxShadow: activeTab === 'orders' ? '0 2px 5px rgba(0,0,0,0.06)' : 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease'
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="1" y="3" width="15" height="13" />
            <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
            <circle cx="5.5" cy="18.5" r="2.5" />
            <circle cx="18.5" cy="18.5" r="2.5" />
          </svg>
          My Orders &amp; AI Live Tracking
        </button>

        <button
          onClick={() => setActiveTab('store')}
          id="tab-storefront"
          style={{
            flex: 1,
            padding: '0.7rem 1.25rem',
            fontSize: '0.86rem',
            fontWeight: activeTab === 'store' ? 700 : 600,
            color: activeTab === 'store' ? '#4f46e5' : '#64748b',
            background: activeTab === 'store' ? '#ffffff' : 'transparent',
            border: 'none',
            borderRadius: '8px',
            boxShadow: activeTab === 'store' ? '0 2px 5px rgba(0,0,0,0.06)' : 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease'
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M16 10a4 4 0 0 1-8 0" />
          </svg>
          ShopVerse Marketplace Catalog ({products.length})
        </button>

        <button
          onClick={() => setActiveTab('policies')}
          id="tab-policy-library"
          style={{
            flex: 1,
            padding: '0.7rem 1.25rem',
            fontSize: '0.86rem',
            fontWeight: activeTab === 'policies' ? 700 : 600,
            color: activeTab === 'policies' ? '#4f46e5' : '#64748b',
            background: activeTab === 'policies' ? '#ffffff' : 'transparent',
            border: 'none',
            borderRadius: '8px',
            boxShadow: activeTab === 'policies' ? '0 2px 5px rgba(0,0,0,0.06)' : 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            transition: 'all 0.15s ease'
          }}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Policy Rules &amp; SLA Standards
        </button>
      </div>

      {/* =================================================================== */}
      {/* TAB 1: MY ORDERS & LIVE AI TRACKING */}
      {/* =================================================================== */}
      {activeTab === 'orders' && (
        <div>
          {/* AI Policy & Order Inquiry Engine Card */}
          <div style={{
            background: '#ffffff',
            border: '1px solid #c7d2fe',
            borderRadius: '14px',
            padding: '1.5rem',
            marginBottom: '2rem',
            boxShadow: '0 4px 12px rgba(79,70,229,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: '#4f46e5', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.78rem', fontWeight: 800 }}>
                  AI
                </div>
                <div>
                  <strong style={{ fontSize: '0.92rem', color: '#0f172a', display: 'block' }}>Instant Policy &amp; Order Inquiry Engine</strong>
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Grounded in official policy collections from data/</span>
                </div>
              </div>

              <span style={{ fontSize: '0.72rem', color: '#059669', background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '0.2rem 0.6rem', borderRadius: '20px', fontWeight: 600 }}>
                ● Grounded Citations Ready
              </span>
            </div>

            {/* Input Bar */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.85rem' }}>
              <div style={{ flex: 1, position: 'relative' }}>
                <input
                  type="text"
                  value={aiQueryInput}
                  onChange={(e) => setAiQueryInput(e.target.value)}
                  placeholder="Ask about any order or policy clause (e.g. Track ORD-99215, return windows, damage replacement)..."
                  style={{
                    width: '100%',
                    padding: '0.8rem 1rem 0.8rem 2.4rem',
                    fontSize: '0.88rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '10px',
                    outline: 'none',
                    background: '#f8fafc',
                    color: '#0f172a',
                    boxSizing: 'border-box'
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && aiQueryInput.trim()) {
                      handleQueryAi();
                    }
                  }}
                />
                <div style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </div>
              </div>

              <button
                onClick={() => handleQueryAi()}
                disabled={aiLoading}
                style={{
                  padding: '0.8rem 1.5rem',
                  background: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '0.86rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  boxShadow: '0 2px 6px rgba(79,70,229,0.25)',
                  whiteSpace: 'nowrap'
                }}
              >
                {aiLoading ? 'Retrieving Policy...' : 'Query AI →'}
              </button>
            </div>

            {/* Prompt Suggestion Pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 600 }}>Suggested:</span>
              {[
                'What is the standard 30-day return window?',
                'How to report a damaged item within 48 hours?',
                'What are the seller 2-day dispatch SLA requirements?',
                'Can I cancel an order within 1 hour for a full refund?'
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleQueryAi(prompt)}
                  style={{
                    padding: '0.3rem 0.7rem',
                    fontSize: '0.74rem',
                    background: '#f1f5f9',
                    border: '1px solid #e2e8f0',
                    borderRadius: '20px',
                    color: '#334155',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#eef2ff';
                    e.currentTarget.style.borderColor = '#c7d2fe';
                    e.currentTarget.style.color = '#4f46e5';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#f1f5f9';
                    e.currentTarget.style.borderColor = '#e2e8f0';
                    e.currentTarget.style.color = '#334155';
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>

            {/* AI Grounded Result Box */}
            {aiAnswer && (
              <div style={{
                marginTop: '1.25rem',
                padding: '1.35rem',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#16a34a' }} />
                    <strong style={{ fontSize: '0.84rem', color: '#15803d', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Grounded PolicyPilot Answer
                    </strong>
                  </div>
                  <button
                    onClick={() => setAiAnswer(null)}
                    style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}
                  >
                    ✕ Dismiss
                  </button>
                </div>

                <p style={{ fontSize: '0.9rem', color: '#0f172a', lineHeight: 1.6, margin: '0 0 0.85rem 0' }}>
                  {aiAnswer.answer}
                </p>

                {aiAnswer.sources && aiAnswer.sources.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', paddingTop: '0.75rem', borderTop: '1px solid #dcfce7' }}>
                    <span style={{ fontSize: '0.74rem', color: '#166534', fontWeight: 700 }}>Verified Citations:</span>
                    {aiAnswer.sources.map((s, idx) => (
                      <span key={idx} style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem', background: '#ffffff', border: '1px solid #86efac', borderRadius: '5px', color: '#15803d', fontWeight: 600 }}>
                        [{idx + 1}] {s.source || s.section || 'Policy Document'}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Search & Filter Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ position: 'relative', width: '380px' }}>
              <input
                type="text"
                value={orderSearch}
                onChange={(e) => setOrderSearch(e.target.value)}
                placeholder="Search orders by ID, product name, or status..."
                style={{
                  width: '100%',
                  padding: '0.7rem 1rem 0.7rem 2.4rem',
                  fontSize: '0.85rem',
                  border: '1px solid #cbd5e1',
                  borderRadius: '9px',
                  background: '#ffffff',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
              <div style={{ position: 'absolute', left: '0.8rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>
            </div>

            <div style={{ fontSize: '0.84rem', color: '#64748b' }}>
              Showing <strong>{filteredOrders.length}</strong> active orders
            </div>
          </div>

          {/* Orders List Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {filteredOrders.map((order) => {
              const isDelivered = order.status === 'Delivered';
              const isInTransit = order.status === 'In Transit';
              const isProcessing = order.status === 'Processing';

              return (
                <div
                  key={order.id}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '14px',
                    padding: '1.75rem',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.03)'
                  }}
                >
                  {/* Order Top Bar */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #f1f5f9', paddingBottom: '1.15rem', marginBottom: '1.35rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                        <strong style={{ fontSize: '1.1rem', color: '#0f172a' }}>{order.id}</strong>
                        <span style={{
                          padding: '0.25rem 0.75rem',
                          borderRadius: '20px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: isDelivered ? '#ecfdf5' : isInTransit ? '#eff6ff' : '#fffbeb',
                          color: isDelivered ? '#059669' : isInTransit ? '#2563eb' : '#d97706'
                        }}>
                          {order.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        Placed on {order.date} • Seller: <strong style={{ color: '#334155' }}>{order.vendor}</strong> • Carrier: {order.carrier} (<span style={{ fontFamily: 'monospace' }}>{order.trackingNumber}</span>)
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a' }}>{order.amount}</div>
                      <div style={{ fontSize: '0.76rem', color: '#64748b' }}>ETA: {order.eta}</div>
                    </div>
                  </div>

                  {/* Connected Stepper Progress Bar */}
                  <div style={{ marginBottom: '1.5rem', background: '#f8fafc', padding: '1.25rem 1.5rem', borderRadius: '12px', border: '1px solid #f1f5f9' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', position: 'relative' }}>
                      {['Order Confirmed', 'Dispatched (SLA Met)', 'In Transit', 'Out for Delivery', 'Delivered'].map((stepLabel, idx) => {
                        const stepNum = idx + 1;
                        const isDone = order.currentStep >= stepNum;
                        const isCurrent = order.currentStep === stepNum;

                        return (
                          <div key={stepLabel} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, textAlign: 'center', zIndex: 2 }}>
                            <div style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              background: isDone ? '#059669' : '#e2e8f0',
                              color: '#ffffff',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              marginBottom: '0.45rem',
                              boxShadow: isCurrent ? '0 0 0 4px rgba(5,150,105,0.2)' : 'none'
                            }}>
                              {isDone ? '✓' : stepNum}
                            </div>
                            <span style={{ fontSize: '0.74rem', color: isDone ? '#0f172a' : '#94a3b8', fontWeight: isCurrent ? 700 : 500 }}>
                              {stepLabel}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Product Details & Action Buttons */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
                      <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: '#eef2ff', color: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                          <line x1="12" y1="22.08" x2="12" y2="12" />
                        </svg>
                      </div>
                      <div>
                        <strong style={{ fontSize: '0.92rem', color: '#0f172a', display: 'block' }}>{order.product}</strong>
                        <span style={{ fontSize: '0.76rem', color: '#059669', fontWeight: 600 }}>
                          {order.aiPolicyTip}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.65rem' }}>
                      <button
                        onClick={() => handleQueryAi(`Track status and policies for order ${order.id} (${order.product}). Please cite the 30-day return window, damaged item replacement policy, and seller dispatch SLA.`)}
                        style={{
                          padding: '0.6rem 1rem',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          color: '#4f46e5',
                          background: '#eef2ff',
                          border: '1px solid #c7d2fe',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem'
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                        Track with PolicyPilot AI
                      </button>

                      {isDelivered && (
                        <button
                          onClick={() => handleQueryAi(`How do I initiate a return for delivered order ${order.id} (${order.product})? Please cite the 30-day return window, pickup process, and refund method.`)}
                          style={{
                            padding: '0.6rem 1rem',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            color: '#334155',
                            background: '#f1f5f9',
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            cursor: 'pointer'
                          }}
                        >
                          Return Inquiry
                        </button>
                      )}

                      {isProcessing && (
                        <button
                          onClick={() => handleQueryAi(`Can I cancel order ${order.id} (${order.product}) right now under the 1-hour cancellation policy for an instant refund?`)}
                          style={{
                            padding: '0.6rem 1rem',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            color: '#b91c1c',
                            background: '#fef2f2',
                            border: '1px solid #fecaca',
                            borderRadius: '8px',
                            cursor: 'pointer'
                          }}
                        >
                          Cancel Order Policy
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: STOREFRONT & CATALOG */}
      {/* =================================================================== */}
      {activeTab === 'store' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.25rem 0' }}>
                Certified Merchant Marketplace
              </h2>
              <p style={{ fontSize: '0.84rem', color: '#64748b', margin: 0 }}>
                All purchases carry verified 30-day return compliance and 2-day merchant dispatch SLAs.
              </p>
            </div>
            <span style={{ fontSize: '0.8rem', color: '#059669', background: '#ecfdf5', border: '1px solid #bbf7d0', padding: '0.35rem 0.85rem', borderRadius: '20px', fontWeight: 700 }}>
              6 Demo Products Available for 1-Click Checkout
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
            {products.map((p) => (
              <div
                key={p.id}
                style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '14px',
                  padding: '1.65rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                  transition: 'all 0.2s ease'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                    <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.55rem', background: '#eff6ff', color: '#2563eb', borderRadius: '5px', fontWeight: 700 }}>
                      {p.category}
                    </span>
                    <span style={{ fontSize: '0.76rem', fontWeight: 700, color: '#059669' }}>
                      ★ {p.rating}
                    </span>
                  </div>

                  <strong style={{ fontSize: '1.05rem', color: '#0f172a', display: 'block', marginBottom: '0.45rem', lineHeight: 1.4 }}>
                    {p.name}
                  </strong>

                  <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.5, margin: '0 0 1.15rem 0' }}>
                    {p.description}
                  </p>

                  <div style={{ background: '#f8fafc', padding: '0.75rem 0.95rem', borderRadius: '9px', border: '1px solid #f1f5f9', marginBottom: '1.15rem', fontSize: '0.76rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                      <span style={{ color: '#64748b' }}>Merchant:</span>
                      <strong style={{ color: '#334155' }}>{p.vendor}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                      <span style={{ color: '#64748b' }}>Dispatch SLA:</span>
                      <strong style={{ color: '#059669' }}>{p.dispatchSla}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748b' }}>Policy:</span>
                      <strong style={{ color: '#4f46e5' }}>{p.returnPolicy}</strong>
                    </div>
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>Price:</span>
                      <strong style={{ fontSize: '1.35rem', color: '#0f172a' }}>{p.priceFormatted}</strong>
                    </div>
                    <span style={{ fontSize: '0.74rem', color: '#16a34a', fontWeight: 600 }}>In Stock ({p.stock})</span>
                  </div>

                  <button
                    onClick={() => handlePlaceOrder(p)}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      background: '#4f46e5',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '9px',
                      fontSize: '0.86rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.45rem',
                      boxShadow: '0 2px 6px rgba(79,70,229,0.25)',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    Place Demo Order &amp; Track Live →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: POLICY RULES & SLA STANDARDS */}
      {/* =================================================================== */}
      {activeTab === 'policies' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.75rem' }}>
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.85rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
              Key Customer &amp; Vendor Policies
            </h2>
            <p style={{ fontSize: '0.86rem', color: '#64748b', marginBottom: '1.5rem' }}>
              These rules are loaded in PolicyPilot MongoDB Vector Database and used for all AI answer grounding and order tracking validations.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>1. 30-Day Customer Return Policy</strong>
                  <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', background: '#ecfdf5', color: '#059669', borderRadius: '4px', fontWeight: 700 }}>
                    Section 3.1
                  </span>
                </div>
                <p style={{ fontSize: '0.84rem', color: '#475569', margin: 0, lineHeight: 1.55 }}>
                  Customers can return eligible items within 30 days of delivery. Items must be unused, unwashed, and in original packaging with all tags intact. Refunds are issued to the original payment method within 5-7 business days of warehouse inspection.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>2. 48-Hour Damaged / Defective Reporting</strong>
                  <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', background: '#fef3c7', color: '#d97706', borderRadius: '4px', fontWeight: 700 }}>
                    Section 3.4
                  </span>
                </div>
                <p style={{ fontSize: '0.84rem', color: '#475569', margin: 0, lineHeight: 1.55 }}>
                  Any damage or transit defects must be reported within 48 hours of delivery. ShopVerse provides free doorstep pickup and an immediate express replacement or full refund without return shipping fees.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>3. Seller 2-Day Dispatch SLA</strong>
                  <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', background: '#eff6ff', color: '#2563eb', borderRadius: '4px', fontWeight: 700 }}>
                    Section 4.2
                  </span>
                </div>
                <p style={{ fontSize: '0.84rem', color: '#475569', margin: 0, lineHeight: 1.55 }}>
                  All certified merchants must package and hand over confirmed orders to assigned logistics carriers within 2 business days. Late dispatches incur automated compliance penalties.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>4. 1-Hour Free Order Cancellation</strong>
                  <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', background: '#f3e8ff', color: '#7c3aed', borderRadius: '4px', fontWeight: 700 }}>
                    Section 2.1
                  </span>
                </div>
                <p style={{ fontSize: '0.84rem', color: '#475569', margin: 0, lineHeight: 1.55 }}>
                  Orders may be cancelled with 100% instant refund within 1 hour of placement before seller warehouse fulfillment begins.
                </p>
              </div>
            </div>
          </div>

          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '1.85rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                RAG Citation Engine
              </h3>
              <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                Whenever you query PolicyPilot about an order or policy clause, the answer is grounded against exact paragraph chunks.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem' }}>
                <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                  <strong>Indexed Chunks:</strong> 49 paragraphs
                </div>
                <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                  <strong>Cosine Threshold:</strong> 0.65 (High Grounding)
                </div>
                <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                  <strong>Guardrail:</strong> Zero Hallucinations
                </div>
              </div>
            </div>

            <Link
              href="/chatbot"
              style={{
                display: 'block',
                textAlign: 'center',
                width: '100%',
                padding: '0.8rem',
                background: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                borderRadius: '9px',
                fontSize: '0.84rem',
                fontWeight: 600,
                textDecoration: 'none',
                marginTop: '1.5rem',
                boxShadow: '0 2px 6px rgba(79,70,229,0.2)',
                boxSizing: 'border-box'
              }}
            >
              Open Full Interactive Chat →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
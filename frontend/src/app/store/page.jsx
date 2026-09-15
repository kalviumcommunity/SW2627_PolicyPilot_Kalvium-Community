'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

// Authentic E-Commerce Products
const STORE_PRODUCTS = [
  {
    id: 'PROD-101',
    name: 'Sony WH-1000XM5 Wireless Noise-Canceling Headphones',
    category: 'Consumer Electronics',
    price: 24999,
    priceFormatted: '₹24,999',
    vendor: 'Nexus Electronics Direct',
    rating: 4.8,
    reviewsCount: 342,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Same-Day Dispatch',
    stock: 24,
    description: 'Industry-leading wireless noise cancellation with 30-hour battery life and quick charging.'
  },
  {
    id: 'PROD-102',
    name: 'Ergonomic Mesh Task Chair Pro',
    category: 'Home & Office',
    price: 14499,
    priceFormatted: '₹14,499',
    vendor: 'Solace Home & Living',
    rating: 4.7,
    reviewsCount: 189,
    returnPolicy: '30-Day Return Window',
    dispatchSla: '2-Day Dispatch SLA',
    stock: 12,
    description: 'Breathable high-density mesh back with dynamic lumbar support and 3D adjustable armrests.'
  },
  {
    id: 'PROD-103',
    name: 'Minimalist Weatherproof Commuter Backpack',
    category: 'Fashion & Gear',
    price: 4250,
    priceFormatted: '₹4,250',
    vendor: 'Apex Logistics & Retail',
    rating: 4.9,
    reviewsCount: 512,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Express 24h Dispatch',
    stock: 45,
    description: 'Water-resistant coated ballistic nylon with dedicated padded sleeve for up to 16-inch laptops.'
  },
  {
    id: 'PROD-104',
    name: 'Keychron K2 Wireless Mechanical Keyboard',
    category: 'Computer Accessories',
    price: 7899,
    priceFormatted: '₹7,899',
    vendor: 'Quantum Tech Gadgets',
    rating: 4.95,
    reviewsCount: 420,
    returnPolicy: '30-Day Return Window',
    dispatchSla: 'Same-Day Dispatch',
    stock: 18,
    description: 'Compact 75% tenkeyless mechanical layout with hot-swappable switches and Bluetooth 5.1.'
  },
  {
    id: 'PROD-105',
    name: 'Aura Organic Botanical Skin Care Set',
    category: 'Personal Care',
    price: 3200,
    priceFormatted: '₹3,200',
    vendor: 'Aura Health & Beauty',
    rating: 4.85,
    reviewsCount: 260,
    returnPolicy: 'Sealed 30-Day Return',
    dispatchSla: '1-Day Dispatch SLA',
    stock: 30,
    description: 'Certified organic botanical cleanser, clarifying toner, and hydrating hyaluronic moisture complex.'
  },
  {
    id: 'PROD-106',
    name: 'Velocity Performance Athletic Running Jacket',
    category: 'Fashion & Apparel',
    price: 3950,
    priceFormatted: '₹3,950',
    vendor: 'Velocity Global Apparel',
    rating: 4.6,
    reviewsCount: 145,
    returnPolicy: '30-Day Return Window',
    dispatchSla: '2-Day Dispatch SLA',
    stock: 55,
    description: 'Lightweight thermal running jacket with 360-degree reflective accents and storm-proof hood.'
  }
];

// Initial Customer Orders
const INITIAL_ORDERS = [
  {
    id: 'ORD-99215',
    date: '14 Sep 2026',
    customerName: 'Ananya',
    product: 'Sony WH-1000XM5 Wireless Noise-Canceling Headphones',
    vendor: 'Nexus Electronics Direct',
    amount: '₹24,999',
    status: 'In Transit',
    currentStep: 3, // 1: Confirmed, 2: Dispatched, 3: In Transit, 4: Out for Delivery, 5: Delivered
    carrier: 'BlueDart Express',
    trackingNumber: 'BD-88290142',
    eta: '16 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiTip: 'Eligible for 30-day return upon delivery. Report any transit damage within 48 hours for free pickup.'
  },
  {
    id: 'ORD-99214',
    date: '12 Sep 2026',
    customerName: 'Ananya',
    product: 'Minimalist Weatherproof Commuter Backpack',
    vendor: 'Apex Logistics & Retail',
    amount: '₹4,250',
    status: 'Delivered',
    currentStep: 5,
    carrier: 'Delhivery Express',
    trackingNumber: 'DL-99120411',
    eta: 'Delivered on 14 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiTip: 'Delivered 14 Sep. Return window open until 14 Oct 2026 (28 days remaining).'
  },
  {
    id: 'ORD-99216',
    date: '15 Sep 2026',
    customerName: 'Ananya',
    product: 'Ergonomic Mesh Task Chair Pro',
    vendor: 'Solace Home & Living',
    amount: '₹14,499',
    status: 'Processing',
    currentStep: 1,
    carrier: 'Safexpress Freight',
    trackingNumber: 'SF-44019283',
    eta: '19 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiTip: 'Seller must dispatch within 2 business days as per ShopVerse merchant SLA.'
  },
  {
    id: 'ORD-99217',
    date: '10 Sep 2026',
    customerName: 'Ananya',
    product: 'Keychron K2 Wireless Mechanical Keyboard',
    vendor: 'Quantum Tech Gadgets',
    amount: '₹7,899',
    status: 'Delivered',
    currentStep: 5,
    carrier: 'BlueDart Express',
    trackingNumber: 'BD-77192033',
    eta: 'Delivered on 12 Sep 2026',
    destination: 'Bengaluru, Karnataka',
    aiTip: 'Delivered 12 Sep. Return window open until 12 Oct 2026. 1-year manufacturer warranty active.'
  }
];

export default function CustomerStorePage() {
  const [activeTab, setActiveTab] = useState('catalog'); // 'catalog', 'tracking', 'policies'
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  const [products] = useState(STORE_PRODUCTS);
  const [cart, setCart] = useState([]);
  const [productForCheckout, setProductForCheckout] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Customer Auth state
  const [customerUser, setCustomerUser] = useState({
    name: 'Ananya',
    email: 'ananya@customer.com',
    address: '102 MG Road, Indiranagar, Bengaluru, KA 560038',
    phone: '+91 98765 43210'
  });
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupAddress, setSignupAddress] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  // Customer AI chat & order inquiry state
  const [orderQuery, setOrderQuery] = useState('');
  const [aiAnswer, setAiAnswer] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const handleCustomerLogin = (e) => {
    if (e) e.preventDefault();
    if (!loginEmail) {
      showToast('Please enter your customer email address.');
      return;
    }
    const cleanName = loginEmail.split('@')[0].replace(/[._-]/g, ' ');
    const formattedName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);
    
    const loggedUser = {
      name: formattedName || 'Valued Customer',
      email: loginEmail,
      address: '102 MG Road, Indiranagar, Bengaluru, KA 560038',
      phone: '+91 98765 43210'
    };

    setCustomerUser(loggedUser);
    setAuthModalOpen(false);
    showToast(`Signed in to ShopVerse as ${loggedUser.name}!`);
  };

  const handleCustomerSignup = (e) => {
    if (e) e.preventDefault();
    if (!signupName || !signupEmail) {
      showToast('Please fill in your name and email.');
      return;
    }

    const newUser = {
      name: signupName,
      email: signupEmail,
      address: signupAddress || '102 MG Road, Indiranagar, Bengaluru, KA 560038',
      phone: '+91 98765 43210'
    };

    setCustomerUser(newUser);
    setAuthModalOpen(false);
    showToast(`Customer account created for ${newUser.name}!`);
  };

  const handleCustomerLogout = () => {
    setCustomerUser(null);
    setProfileDropdownOpen(false);
    showToast('Signed out of customer account. Browsing as guest.');
  };

  const handleAddToCart = (product) => {
    setCart([...cart, product]);
    showToast(`Added ${product.name} to your cart!`);
  };

  const handleInitiateBuy = (product) => {
    if (!customerUser) {
      setProductForCheckout(product);
      setAuthModalOpen(true);
      showToast('Please sign in or create an account to place your order.');
    } else {
      setProductForCheckout(product);
    }
  };

  const handleConfirmOrder = () => {
    if (!productForCheckout) return;

    const newOrder = {
      id: `ORD-${Math.floor(10000 + Math.random() * 90000)}`,
      date: '15 Sep 2026',
      customerName: customerUser?.name || 'Customer',
      product: productForCheckout.name,
      vendor: productForCheckout.vendor,
      amount: productForCheckout.priceFormatted,
      status: 'Processing',
      currentStep: 1,
      carrier: 'BlueDart Express',
      trackingNumber: `BD-${Math.floor(10000000 + Math.random() * 90000000)}`,
      eta: '18 Sep 2026',
      destination: customerUser?.address?.split(',')[2] || 'Bengaluru, Karnataka',
      aiTip: 'New order placed. Can be cancelled with full refund within 1 hour under ShopVerse policy.'
    };

    setOrders([newOrder, ...orders]);
    setProductForCheckout(null);
    setActiveTab('tracking');
    showToast(`Order #${newOrder.id} placed! Tracking live with AI below.`);
  };

  const handleQueryAi = async (customPrompt) => {
    const query = (customPrompt || orderQuery).trim();
    if (!query) return;

    setOrderQuery(query);
    setAiLoading(true);
    setAiAnswer(null);

    const qLower = query.toLowerCase();
    const currentUserName = customerUser?.name || 'Ananya';
    const currentUserEmail = customerUser?.email || 'ananya@customer.com';

    // 1. Check if the query matches an order in the live session state (including newly created ones)
    const matchedSessionOrder = orders.find((o) => {
      if (qLower.includes(o.id.toLowerCase())) return true;
      if (qLower.includes(o.trackingNumber.toLowerCase())) return true;
      const prodTokens = o.product.toLowerCase().split(' ').filter((w) => w.length > 4);
      return prodTokens.some((t) => qLower.includes(t)) && (qLower.includes('track') || qLower.includes('order') || qLower.includes('status') || qLower.includes('where'));
    });

    if (matchedSessionOrder) {
      const orderAnswer = `Order Tracking Details for ${matchedSessionOrder.id} (${matchedSessionOrder.product}):\n• Status: ${matchedSessionOrder.status} (Step ${matchedSessionOrder.currentStep} of 5)\n• Carrier: ${matchedSessionOrder.carrier} (Tracking #${matchedSessionOrder.trackingNumber})\n• Estimated Delivery: ${matchedSessionOrder.eta} to ${matchedSessionOrder.destination}\n• Order Amount: ${matchedSessionOrder.amount} • Vendor: ${matchedSessionOrder.vendor}\n• Policy Note: ${matchedSessionOrder.aiTip}`;
      const orderSources = [
        { source: 'shopverse_policies.md', section: 'Return & Refund Window' },
        { source: 'shopverse_policies.md', section: 'Damaged & Defective Goods' }
      ];

      setAiAnswer({
        answer: orderAnswer,
        sources: orderSources
      });
      setAiLoading(false);

      // Post directly to admin portal query logs
      try {
        fetch('http://127.0.0.1:8000/admin/log_conversation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: query,
            answer: orderAnswer,
            sources: orderSources,
            user_name: currentUserName,
            user_email: currentUserEmail,
            user_role: 'customer',
            surface: 'Customer Store (/store)'
          })
        }).catch(() => {});
      } catch {}
      return;
    }

    // 2. Query backend PolicyPilot API
    try {
      const resp = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          user_name: currentUserName,
          user_email: currentUserEmail,
          user_role: 'customer',
          surface: 'Customer Store (/store)'
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setAiAnswer(data);
      } else {
        // Fallback policy response
        const fallbackAns = 'Under ShopVerse customer policy: 1) Standard return window is 30 days from delivery. 2) Defective or transit-damaged items must be reported within 48 hours for free doorstep pickup and express replacement. 3) Sellers must dispatch orders within 2 business days.';
        const fallbackSources = [
          { source: 'shopverse_policies.md', section: 'Return & Refund Window' },
          { source: 'shopverse_policies.md', section: 'Damaged & Defective Goods' }
        ];
        setAiAnswer({
          answer: fallbackAns,
          sources: fallbackSources
        });
        fetch('http://127.0.0.1:8000/admin/log_conversation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: query,
            answer: fallbackAns,
            sources: fallbackSources,
            user_name: currentUserName,
            user_email: currentUserEmail,
            user_role: 'customer',
            surface: 'Customer Store (/store)'
          })
        }).catch(() => {});
      }
    } catch {
      // Offline fallback with domain check
      const isEcommerce = [
        'order', 'track', 'return', 'refund', 'damage', 'defect', 'cancel', 'shipping', 'delivery',
        'sla', 'dispatch', 'payment', 'cod', 'upi', 'product', 'sony', 'chair', 'backpack', 'keyboard'
      ].some((term) => qLower.includes(term));

      let fallbackAns = '';
      let fallbackSources = [];
      if (isEcommerce) {
        fallbackAns = 'Under ShopVerse customer policy: 1) Standard return window is 30 days from delivery. 2) Defective or transit-damaged items must be reported within 48 hours for free doorstep pickup and express replacement. 3) Sellers must dispatch orders within 2 business days.';
        fallbackSources = [{ source: 'shopverse_policies.md', section: 'Return & Refund Window' }];
      } else {
        fallbackAns = 'I am the ShopVerse & PolicyPilot E-Commerce AI Assistant. I can only assist with questions regarding our store products, live order tracking, delivery timelines, return/refund rules, damaged goods claims, and store merchant policies. Please ask a question related to your order or store policies.';
        fallbackSources = [];
      }

      setAiAnswer({
        answer: fallbackAns,
        sources: fallbackSources
      });

      fetch('http://127.0.0.1:8000/admin/log_conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          answer: fallbackAns,
          sources: fallbackSources,
          user_name: currentUserName,
          user_email: currentUserEmail,
          user_role: 'customer',
          surface: 'Customer Store (/store)'
        })
      }).catch(() => {});
    } finally {
      setAiLoading(false);
    }
  };

  const categories = ['All', 'Consumer Electronics', 'Home & Office', 'Fashion & Gear', 'Computer Accessories', 'Personal Care'];

  const filteredProducts = products.filter((p) => {
    const matchesCategory = selectedCategory === 'All' || p.category === selectedCategory;
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) || p.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const filteredOrders = orders.filter((o) => {
    const q = orderQuery.toLowerCase();
    return (
      o.id.toLowerCase().includes(q) ||
      o.product.toLowerCase().includes(q) ||
      o.status.toLowerCase().includes(q) ||
      o.vendor.toLowerCase().includes(q)
    );
  });

  const initials = customerUser?.name
    ? customerUser.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : 'G';

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', display: 'flex', flexDirection: 'column' }}>
      
      {/* Toast Alert */}
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

      {/* Top Store Utility Bar */}
      <div style={{ background: '#0f172a', color: '#94a3b8', fontSize: '0.76rem', padding: '0.45rem 2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <span>Free Express Delivery on orders above ₹499</span>
          <span>•</span>
          <span style={{ color: '#38bdf8' }}>30-Day Guaranteed Returns</span>
          <span>•</span>
          <span style={{ color: '#a7f3d0' }}>AI-Powered 24/7 Order Tracking</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link href="/" style={{ color: '#cbd5e1', textDecoration: 'none' }}>
            PolicyPilot Platform
          </Link>
          <span>•</span>
          <Link href="/dashboard" style={{ color: '#a78bfa', textDecoration: 'none', fontWeight: 600 }}>
            Merchant Store Console →
          </Link>
        </div>
      </div>

      {/* Main E-Commerce Header */}
      <header style={{ height: '76px', borderBottom: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2.5rem', position: 'sticky', top: 0, zIndex: 40 }}>
        
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => setActiveTab('catalog')}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <path d="M16 10a4 4 0 0 1-8 0" />
              </svg>
            </div>
            <div>
              <strong style={{ fontSize: '1.2rem', fontWeight: 800, display: 'block', lineHeight: 1.15, color: '#0f172a' }}>ShopVerse</strong>
              <small style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                AI-Enabled Marketplace
              </small>
            </div>
          </div>

          <div style={{ height: '24px', width: '1px', background: '#e2e8f0' }} />

          {/* Search Bar */}
          <div style={{ position: 'relative', width: '360px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products, headphones, backpacks..."
              style={{
                width: '100%',
                padding: '0.65rem 1rem 0.65rem 2.4rem',
                fontSize: '0.85rem',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                background: '#f8fafc',
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
        </div>

        {/* Navigation & Customer Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          
          <button
            onClick={() => setActiveTab('catalog')}
            style={{
              padding: '0.55rem 0.95rem',
              fontSize: '0.84rem',
              fontWeight: activeTab === 'catalog' ? 700 : 500,
              color: activeTab === 'catalog' ? '#4f46e5' : '#334155',
              background: activeTab === 'catalog' ? '#eef2ff' : 'transparent',
              border: 'none',
              borderRadius: '7px',
              cursor: 'pointer'
            }}
          >
            Storefront
          </button>

          <button
            onClick={() => setActiveTab('tracking')}
            style={{
              padding: '0.55rem 1rem',
              fontSize: '0.84rem',
              fontWeight: activeTab === 'tracking' ? 700 : 600,
              color: activeTab === 'tracking' ? '#ffffff' : '#059669',
              background: activeTab === 'tracking' ? '#059669' : '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem'
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="1" y="3" width="15" height="13" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
            Track Orders with AI ({orders.length})
          </button>

          <button
            onClick={() => setActiveTab('policies')}
            style={{
              padding: '0.55rem 0.95rem',
              fontSize: '0.84rem',
              fontWeight: activeTab === 'policies' ? 700 : 500,
              color: activeTab === 'policies' ? '#4f46e5' : '#334155',
              background: activeTab === 'policies' ? '#eef2ff' : 'transparent',
              border: 'none',
              borderRadius: '7px',
              cursor: 'pointer'
            }}
          >
            Store Policies
          </button>

          <div style={{ height: '20px', width: '1px', background: '#e2e8f0' }} />

          {/* Customer Authentication Profile Dropdown / Sign In Button */}
          {customerUser ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setProfileDropdownOpen((o) => !o)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '30px',
                  padding: '0.35rem 0.85rem 0.35rem 0.45rem',
                  cursor: 'pointer'
                }}
                id="customer-profile-btn"
              >
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#e0e7ff', color: '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.74rem' }}>
                  {initials}
                </div>
                <div style={{ textAlign: 'left' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#0f172a', display: 'block', lineHeight: 1.1 }}>{customerUser.name}</span>
                  <span style={{ fontSize: '0.66rem', color: '#059669', fontWeight: 600 }}>● Active Customer</span>
                </div>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: '4px', color: '#64748b' }}>
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {/* Profile Dropdown */}
              {profileDropdownOpen && (
                <div style={{
                  position: 'absolute',
                  right: 0,
                  top: '110%',
                  width: '260px',
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                  padding: '1rem',
                  zIndex: 100
                }}>
                  <div style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '0.65rem', marginBottom: '0.65rem' }}>
                    <strong style={{ fontSize: '0.86rem', color: '#0f172a', display: 'block' }}>{customerUser.name}</strong>
                    <span style={{ fontSize: '0.74rem', color: '#64748b' }}>{customerUser.email}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#475569', marginBottom: '0.75rem' }}>
                    <span style={{ fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: '0.2rem' }}>Saved Shipping Address:</span>
                    {customerUser.address}
                  </div>
                  <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <button
                      onClick={() => { setActiveTab('tracking'); setProfileDropdownOpen(false); }}
                      style={{ padding: '0.45rem', textAlign: 'left', background: 'none', border: 'none', fontSize: '0.78rem', color: '#4f46e5', fontWeight: 600, cursor: 'pointer' }}
                    >
                      View Order History ({orders.length}) →
                    </button>
                    <button
                      onClick={handleCustomerLogout}
                      style={{ padding: '0.45rem', textAlign: 'left', background: 'none', border: 'none', fontSize: '0.78rem', color: '#b91c1c', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Sign Out of Store
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => { setAuthMode('login'); setAuthModalOpen(true); }}
              id="customer-signin-btn"
              style={{
                padding: '0.55rem 1rem',
                background: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                boxShadow: '0 2px 5px rgba(79,70,229,0.25)'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              Customer Sign In
            </button>
          )}

          {/* Cart Counter */}
          <button
            onClick={() => setActiveTab('tracking')}
            style={{
              padding: '0.5rem 0.85rem',
              background: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: '#334155'
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
            Cart ({cart.length})
          </button>
        </div>
      </header>

      {/* Hero Store Promotional Banner */}
      {activeTab === 'catalog' && (
        <section style={{
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%)',
          color: '#ffffff',
          padding: '2.5rem 2.5rem',
          margin: '0',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 2 }}>
            <div style={{ maxWidth: '640px' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', padding: '0.2rem 0.65rem', background: 'rgba(255,255,255,0.15)', borderRadius: '20px', fontSize: '0.74rem', fontWeight: 600, marginBottom: '0.85rem' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#a7f3d0' }} />
                ShopVerse Customer Marketplace
              </div>
              <h1 style={{ fontSize: '2.2rem', fontWeight: 800, margin: '0 0 0.65rem 0', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                Quality Products. Guaranteed Return Windows. Grounded AI Tracking.
              </h1>
              <p style={{ fontSize: '0.92rem', color: '#c7d2fe', lineHeight: 1.55, margin: '0 0 1.5rem 0' }}>
                Order from verified merchants with strict 2-day dispatch SLAs, 30-day hassle-free return guarantees, and an intelligent AI assistant to track every milestone.
              </p>
              <div style={{ display: 'flex', gap: '0.85rem' }}>
                <button
                  onClick={() => setActiveTab('tracking')}
                  style={{
                    padding: '0.75rem 1.4rem',
                    background: '#059669',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '9px',
                    fontSize: '0.88rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    boxShadow: '0 4px 12px rgba(5,150,105,0.35)'
                  }}
                >
                  Track Existing Orders with AI →
                </button>
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.08)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '16px', padding: '1.5rem', width: '320px' }}>
              <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#a78bfa', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                Customer Purchase Protections
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#a7f3d0' }}>✓</span> 30-Day Return Window (Section 3.1)
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#a7f3d0' }}>✓</span> 48h Defective Item Replacement
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#a7f3d0' }}>✓</span> 2-Day Merchant Dispatch SLA
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: '#a7f3d0' }}>✓</span> 1-Hour Instant Free Cancellation
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Main Content Area */}
      <main style={{ maxWidth: '1280px', width: '100%', margin: '0 auto', padding: '2rem 1.5rem 4rem 1.5rem', flex: 1 }}>
        
        {/* =================================================================== */}
        {/* VIEW 1: TRADITIONAL PRODUCTS CATALOG */}
        {/* =================================================================== */}
        {activeTab === 'catalog' && (
          <div>
            {/* Category Pills */}
            <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem', marginBottom: '1.75rem' }}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '0.55rem 1.1rem',
                    fontSize: '0.82rem',
                    fontWeight: selectedCategory === cat ? 700 : 500,
                    background: selectedCategory === cat ? '#0f172a' : '#ffffff',
                    color: selectedCategory === cat ? '#ffffff' : '#475569',
                    border: '1px solid #cbd5e1',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Products Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.75rem' }}>
              {filteredProducts.map((p) => (
                <div
                  key={p.id}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '16px',
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
                        ★ {p.rating} ({p.reviewsCount})
                      </span>
                    </div>

                    <strong style={{ fontSize: '1.08rem', color: '#0f172a', display: 'block', marginBottom: '0.45rem', lineHeight: 1.35 }}>
                      {p.name}
                    </strong>

                    <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.5, margin: '0 0 1.15rem 0' }}>
                      {p.description}
                    </p>

                    <div style={{ background: '#f8fafc', padding: '0.75rem 0.95rem', borderRadius: '9px', border: '1px solid #f1f5f9', marginBottom: '1.25rem', fontSize: '0.76rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                        <span style={{ color: '#64748b' }}>Sold by:</span>
                        <strong style={{ color: '#334155' }}>{p.vendor}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                        <span style={{ color: '#64748b' }}>Dispatch SLA:</span>
                        <strong style={{ color: '#059669' }}>{p.dispatchSla}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#64748b' }}>Return Rule:</span>
                        <strong style={{ color: '#4f46e5' }}>{p.returnPolicy}</strong>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.15rem' }}>
                      <div>
                        <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>Special Price:</span>
                        <strong style={{ fontSize: '1.4rem', color: '#0f172a' }}>{p.priceFormatted}</strong>
                      </div>
                      <span style={{ fontSize: '0.74rem', color: '#16a34a', fontWeight: 600 }}>In Stock ({p.stock} units)</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
                      <button
                        onClick={() => handleAddToCart(p)}
                        style={{
                          padding: '0.7rem',
                          background: '#f1f5f9',
                          color: '#334155',
                          border: '1px solid #cbd5e1',
                          borderRadius: '8px',
                          fontSize: '0.82rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        Add to Cart
                      </button>

                      <button
                        onClick={() => handleInitiateBuy(p)}
                        style={{
                          padding: '0.7rem',
                          background: '#4f46e5',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '8px',
                          fontSize: '0.84rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          boxShadow: '0 2px 6px rgba(79,70,229,0.25)'
                        }}
                      >
                        Buy Now →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* VIEW 2: CUSTOMER ORDER TRACKING & AI RESOLUTION */}
        {/* =================================================================== */}
        {activeTab === 'tracking' && (
          <div>
            {/* Top AI Inquiry Box */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #c7d2fe',
              borderRadius: '16px',
              padding: '1.75rem',
              marginBottom: '2rem',
              boxShadow: '0 4px 15px rgba(79,70,229,0.06)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#4f46e5', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.84rem', fontWeight: 800 }}>
                    AI
                  </div>
                  <div>
                    <strong style={{ fontSize: '1rem', color: '#0f172a', display: 'block' }}>
                      ShopVerse AI Order Tracking &amp; Policy Assistant
                    </strong>
                    <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      Ask anything about your package status, 30-day return window, or damaged item replacement.
                    </span>
                  </div>
                </div>

                <span style={{ fontSize: '0.72rem', color: '#059669', background: '#ecfdf5', border: '1px solid #bbf7d0', padding: '0.25rem 0.65rem', borderRadius: '20px', fontWeight: 700 }}>
                  ● Grounded Policy Responses
                </span>
              </div>

              {/* Input Bar */}
              <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ flex: 1, position: 'relative' }}>
                  <input
                    type="text"
                    value={orderQuery}
                    onChange={(e) => setOrderQuery(e.target.value)}
                    placeholder="Enter Order ID or ask policy question (e.g. Track ORD-99215, return window, damage claim)..."
                    style={{
                      width: '100%',
                      padding: '0.85rem 1rem 0.85rem 2.5rem',
                      fontSize: '0.9rem',
                      border: '1px solid #cbd5e1',
                      borderRadius: '10px',
                      outline: 'none',
                      background: '#f8fafc',
                      color: '#0f172a',
                      boxSizing: 'border-box'
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && orderQuery.trim()) {
                        handleQueryAi();
                      }
                    }}
                  />
                  <div style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                  </div>
                </div>

                <button
                  onClick={() => handleQueryAi()}
                  disabled={aiLoading}
                  style={{
                    padding: '0.85rem 1.6rem',
                    background: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '0.88rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    boxShadow: '0 2px 8px rgba(79,70,229,0.25)',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {aiLoading ? 'Retrieving Policy...' : 'Track with AI →'}
                </button>
              </div>

              {/* Quick Query Pills */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 600 }}>Quick Inquiries:</span>
                {[
                  'Track status for order ORD-99215 (Sony Headphones)',
                  'What is the 30-day return policy for delivered items?',
                  'How to claim free replacement for damaged goods within 48h?',
                  'Can I cancel an order within 1 hour of placing?'
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleQueryAi(prompt)}
                    style={{
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.75rem',
                      background: '#f1f5f9',
                      border: '1px solid #e2e8f0',
                      borderRadius: '20px',
                      color: '#334155',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {/* AI Answer Box */}
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
                        Grounded ShopVerse Resolution
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

            {/* Orders Header & Search Count */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.2rem 0' }}>
                  {customerUser ? `${customerUser.name}'s Orders` : 'Tracked Orders'}
                </h2>
                <p style={{ fontSize: '0.82rem', color: '#64748b', margin: 0 }}>
                  Real-time carrier tracking milestones and AI-powered return assistance.
                </p>
              </div>

              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                Showing <strong>{filteredOrders.length}</strong> orders
              </div>
            </div>

            {/* Orders Grid */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {filteredOrders.map((order) => {
                const isDelivered = order.status === 'Delivered';
                const isInTransit = order.status === 'In Transit';

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
                    {/* Top Row */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #f1f5f9', paddingBottom: '1.15rem', marginBottom: '1.35rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                          <strong style={{ fontSize: '1.15rem', color: '#0f172a' }}>{order.id}</strong>
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
                        <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                          Ordered on {order.date} • Recipient: <strong style={{ color: '#334155' }}>{order.customerName || customerUser?.name || 'Customer'}</strong> • Carrier: {order.carrier} (<span style={{ fontFamily: 'monospace' }}>{order.trackingNumber}</span>)
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a' }}>{order.amount}</div>
                        <div style={{ fontSize: '0.76rem', color: '#64748b' }}>ETA: {order.eta}</div>
                      </div>
                    </div>

                    {/* Stepper Progress */}
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

                    {/* Product & Action */}
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
                          <strong style={{ fontSize: '0.94rem', color: '#0f172a', display: 'block' }}>{order.product}</strong>
                          <span style={{ fontSize: '0.76rem', color: '#059669', fontWeight: 600 }}>
                            {order.aiTip}
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '0.65rem' }}>
                        <button
                          onClick={() => handleQueryAi(`Track status and policy rules for order ${order.id} (${order.product}). Please cite the 30-day return window, damage replacement policy, and dispatch SLA.`)}
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
                          Ask AI About Order
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* VIEW 3: POLICIES */}
        {/* =================================================================== */}
        {activeTab === 'policies' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>
              ShopVerse Return &amp; Vendor SLA Policy Handbook
            </h2>
            <p style={{ fontSize: '0.86rem', color: '#64748b', marginBottom: '1.75rem' }}>
              These rules are indexed in the PolicyPilot RAG knowledge base to answer all customer and merchant questions.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem' }}>
                <strong style={{ fontSize: '0.96rem', color: '#0f172a', display: 'block', marginBottom: '0.4rem' }}>
                  1. 30-Day Return Window (Clause 3.1)
                </strong>
                <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55, margin: 0 }}>
                  Items in unused condition with tags and original packaging can be returned within 30 days of delivery. Refunds are credited to the original payment mode within 5-7 business days.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem' }}>
                <strong style={{ fontSize: '0.96rem', color: '#0f172a', display: 'block', marginBottom: '0.4rem' }}>
                  2. 48-Hour Damaged Reporting (Clause 3.4)
                </strong>
                <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55, margin: 0 }}>
                  Defective or transit-damaged items must be reported within 48 hours for immediate free doorstep pickup and express replacement or 100% refund.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem' }}>
                <strong style={{ fontSize: '0.96rem', color: '#0f172a', display: 'block', marginBottom: '0.4rem' }}>
                  3. Seller 2-Day Dispatch SLA (Clause 4.2)
                </strong>
                <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55, margin: 0 }}>
                  Merchants must hand over orders to assigned logistics carriers within 2 business days of order confirmation.
                </p>
              </div>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.35rem' }}>
                <strong style={{ fontSize: '0.96rem', color: '#0f172a', display: 'block', marginBottom: '0.4rem' }}>
                  4. 1-Hour Order Cancellation (Clause 2.1)
                </strong>
                <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.55, margin: 0 }}>
                  Orders may be cancelled with 100% instant refund within 1 hour of placement before merchant packaging begins.
                </p>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Customer Authentication Modal */}
      {authModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', maxWidth: '440px', width: '100%', padding: '2rem', boxShadow: '0 25px 50px rgba(0,0,0,0.25)' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  ShopVerse Customer Account
                </span>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>
                  {authMode === 'login' ? 'Sign In as Customer' : 'Create Customer Account'}
                </h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
                  {authMode === 'login' ? 'Access your orders and AI tracking assistant.' : 'Join ShopVerse for 30-day returns and real-time tracking.'}
                </p>
              </div>
              <button
                onClick={() => setAuthModalOpen(false)}
                style={{ background: '#f1f5f9', border: 'none', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            {/* Tab switch */}
            <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '8px', marginBottom: '1.25rem' }}>
              <button
                onClick={() => setAuthMode('login')}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  fontSize: '0.82rem',
                  fontWeight: authMode === 'login' ? 700 : 500,
                  background: authMode === 'login' ? '#ffffff' : 'transparent',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: authMode === 'login' ? '#0f172a' : '#64748b'
                }}
              >
                Sign In
              </button>
              <button
                onClick={() => setAuthMode('signup')}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  fontSize: '0.82rem',
                  fontWeight: authMode === 'signup' ? 700 : 500,
                  background: authMode === 'signup' ? '#ffffff' : 'transparent',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  color: authMode === 'signup' ? '#0f172a' : '#64748b'
                }}
              >
                New Customer
              </button>
            </div>

            {authMode === 'login' ? (
              <form onSubmit={handleCustomerLogin}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Customer Email Address
                  </label>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="e.g. ananya@customer.com"
                    required
                    style={{ width: '100%', padding: '0.7rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ marginBottom: '1.25rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Password
                  </label>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="Enter password..."
                    required
                    style={{ width: '100%', padding: '0.7rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <button
                  type="submit"
                  id="customer-login-submit"
                  style={{
                    width: '100%',
                    padding: '0.8rem',
                    background: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.86rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  Sign In to Customer Store →
                </button>
              </form>
            ) : (
              <form onSubmit={handleCustomerSignup}>
                <div style={{ marginBottom: '0.85rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={signupName}
                    onChange={(e) => setSignupName(e.target.value)}
                    placeholder="e.g. Ananya"
                    required
                    style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ marginBottom: '0.85rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="e.g. ananya@customer.com"
                    required
                    style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ marginBottom: '0.85rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Delivery Address
                  </label>
                  <input
                    type="text"
                    value={signupAddress}
                    onChange={(e) => setSignupAddress(e.target.value)}
                    placeholder="e.g. 102 MG Road, Bengaluru"
                    style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ marginBottom: '1.25rem' }}>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.35rem' }}>
                    Password
                  </label>
                  <input
                    type="password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="Create a password..."
                    required
                    style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.84rem', boxSizing: 'border-box' }}
                  />
                </div>

                <button
                  type="submit"
                  id="customer-signup-submit"
                  style={{
                    width: '100%',
                    padding: '0.8rem',
                    background: '#059669',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.86rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  Create Account &amp; Continue →
                </button>
              </form>
            )}

          </div>
        </div>
      )}

      {/* Checkout Modal */}
      {productForCheckout && customerUser && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#ffffff', borderRadius: '16px', maxWidth: '500px', width: '100%', padding: '2rem', boxShadow: '0 25px 50px rgba(0,0,0,0.25)' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>ShopVerse Secure Checkout</span>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>Confirm Your Order</h3>
              </div>
              <button
                onClick={() => setProductForCheckout(null)}
                style={{ background: '#f1f5f9', border: 'none', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>{productForCheckout.name}</strong>
                <strong style={{ fontSize: '0.95rem', color: '#059669' }}>{productForCheckout.priceFormatted}</strong>
              </div>
              <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                Sold by {productForCheckout.vendor} • {productForCheckout.returnPolicy}
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem', fontSize: '0.8rem', color: '#334155' }}>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem' }}>Delivery Address ({customerUser.name})</label>
              <input
                type="text"
                defaultValue={customerUser.address}
                style={{ width: '100%', padding: '0.65rem 0.85rem', border: '1px solid #cbd5e1', borderRadius: '7px', fontSize: '0.82rem', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem', background: '#ecfdf5', border: '1px solid #bbf7d0', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.76rem', color: '#15803d' }}>
              ✓ Backed by 30-day return policy and 48-hour damage replacement guarantee.
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                onClick={() => setProductForCheckout(null)}
                style={{ flex: 1, padding: '0.75rem', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.84rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmOrder}
                style={{ flex: 2, padding: '0.75rem', background: '#4f46e5', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '0.86rem', fontWeight: 700, cursor: 'pointer', boxShadow: '0 2px 6px rgba(79,70,229,0.3)' }}
              >
                Place Order &amp; Track Live →
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

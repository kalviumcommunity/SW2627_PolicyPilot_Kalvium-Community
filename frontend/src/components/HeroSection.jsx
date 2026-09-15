'use client';
import React from 'react';

export default function HeroSection() {
  return (
    <section className="hero-section" id="hero">
      {/* Background Image */}
      <div className="hero-bg">
        <img src="/hero_banner.jpg" alt="ShopVerse Hero" />
      </div>

      {/* Content */}
      <div className="hero-content">
        <div className="hero-badge">
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#a78bfa', display: 'inline-block' }} />
          New Season Arrivals
        </div>

        <h1 className="hero-title">
          Shop Everything,<br />
          <span>Anywhere,</span><br />
          Anytime.
        </h1>

        <p className="hero-subtitle">
          Discover millions of products across fashion, electronics, home décor, beauty and more — all with lightning-fast delivery.
        </p>

        <div className="hero-actions">
          <button className="btn-primary" id="hero-shop-btn">
            Shop Now
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
          <button className="btn-outline" id="hero-explore-btn">
            Explore Deals
          </button>
        </div>

        <div className="hero-stats">
          <div>
            <div className="hero-stat-val">10M+</div>
            <div className="hero-stat-label">Products</div>
          </div>
          <div>
            <div className="hero-stat-val">2M+</div>
            <div className="hero-stat-label">Happy Customers</div>
          </div>
          <div>
            <div className="hero-stat-val">180+</div>
            <div className="hero-stat-label">Countries</div>
          </div>
        </div>
      </div>
    </section>
  );
}

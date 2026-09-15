'use client';
import React from 'react';

export default function PromoBanners() {
  return (
    <section className="section" id="promo" style={{ paddingTop: '2rem' }}>
      <div className="promo-grid">
        {/* Promo 1 */}
        <div className="promo-card promo-card-1" id="promo-sale-btn">
          <div className="promo-content">
            <span className="promo-tag">Mega Sale</span>
            <div className="promo-title">Up to 70%<br />Off Sitewide</div>
            <p className="promo-subtitle">Limited stock. Ends in 24 hours.</p>
            <button className="promo-btn">
              Shop the Sale →
            </button>
          </div>
          <div className="promo-deco">🛍️</div>
        </div>

        {/* Promo 2 */}
        <div className="promo-card promo-card-2" id="promo-new-btn">
          <div className="promo-content">
            <span className="promo-tag">New In</span>
            <div className="promo-title">2026 Winter<br />Collection</div>
            <p className="promo-subtitle">Explore the freshest arrivals this season.</p>
            <button className="promo-btn">
              Discover Now →
            </button>
          </div>
          <div className="promo-deco">🧥</div>
        </div>
      </div>
    </section>
  );
}

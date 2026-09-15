'use client';
import React from 'react';

const features = [
  {
    icon: '🚚',
    bg: 'rgba(124,58,237,0.15)',
    title: 'Free Delivery',
    desc: 'Free shipping on all orders above ₹499. Same-day delivery available in 50+ cities.',
  },
  {
    icon: '🔒',
    bg: 'rgba(236,72,153,0.15)',
    title: 'Secure Payments',
    desc: 'Your transactions are protected with bank-grade 256-bit SSL encryption.',
  },
  {
    icon: '↩️',
    bg: 'rgba(245,158,11,0.15)',
    title: 'Easy Returns',
    desc: '30-day hassle-free returns. No questions asked on most items.',
  },
  {
    icon: '🎧',
    bg: 'rgba(74,222,128,0.15)',
    title: '24/7 Support',
    desc: 'Real human support around the clock via chat, email, or phone.',
  },
];

const testimonials = [
  {
    stars: '★★★★★',
    quote: '"ShopVerse completely changed how I shop online. The curated deals are incredible and delivery is always on time!"',
    name: 'Priya Sharma',
    role: 'Verified Buyer · Fashion',
    emoji: '👩',
  },
  {
    stars: '★★★★★',
    quote: '"Bought three gadgets in one week. The quality is top-notch and prices beat every other platform I checked."',
    name: 'Rahul Mehta',
    role: 'Verified Buyer · Electronics',
    emoji: '👨',
  },
  {
    stars: '★★★★☆',
    quote: '"Returns are completely painless and the customer support team resolved my issue in under 10 minutes. Superb!"',
    name: 'Ananya Singh',
    role: 'Verified Buyer · Beauty',
    emoji: '🧑',
  },
];

export default function TrustSection() {
  return (
    <>
      {/* Features */}
      <section className="features-section" id="features">
        <div style={{ textAlign: 'center' }}>
          <div className="section-label" style={{ justifyContent: 'center', display: 'block' }}>Why ShopVerse</div>
          <h2 className="section-title" style={{ margin: '0 auto 0.5rem' }}>Built for Shoppers,<br />Loved by Millions</h2>
        </div>
        <div className="features-grid">
          {features.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="feature-icon" style={{ background: f.bg }}>{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section" id="reviews">
        <div>
          <div className="section-label">Customer Reviews</div>
          <h2 className="section-title">What Our<br />Shoppers Say</h2>
        </div>
        <div className="testimonials-grid">
          {testimonials.map((t) => (
            <div className="testimonial-card" key={t.name}>
              <div className="test-stars">{t.stars}</div>
              <p className="test-quote">{t.quote}</p>
              <div className="test-author">
                <div className="test-avatar">{t.emoji}</div>
                <div>
                  <div className="test-name">{t.name}</div>
                  <div className="test-role">{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

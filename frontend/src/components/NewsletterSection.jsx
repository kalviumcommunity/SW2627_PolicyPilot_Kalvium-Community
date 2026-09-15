'use client';
import React, { useState } from 'react';

export default function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email) setSubmitted(true);
  };

  return (
    <section className="newsletter-section" id="newsletter">
      <div className="newsletter-card">
        <div className="section-label" style={{ justifyContent: 'center', display: 'block', textAlign: 'center' }}>
          Stay in the Loop
        </div>
        <h2 className="newsletter-title">Get Exclusive Deals<br />Before Anyone Else</h2>
        <p className="newsletter-subtitle">
          Join 2 million+ shoppers who get first access to flash sales, new launches, and member-only discounts.
        </p>
        {submitted ? (
          <div style={{
            display: 'inline-block',
            padding: '0.85rem 2rem',
            background: 'rgba(74,222,128,0.15)',
            border: '1px solid rgba(74,222,128,0.3)',
            borderRadius: '9999px',
            color: '#4ade80',
            fontWeight: 600,
            fontSize: '0.95rem',
          }}>
            ✓ You're in! Check your inbox for the welcome offer.
          </div>
        ) : (
          <form className="newsletter-form" onSubmit={handleSubmit} id="newsletter-form">
            <input
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              id="newsletter-email"
            />
            <button type="submit" id="newsletter-submit-btn">Subscribe Free</button>
          </form>
        )}
      </div>
    </section>
  );
}

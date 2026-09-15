'use client';
import React from 'react';

const items = [
  '🚀 Free Delivery on Orders Above ₹499',
  '⚡ Flash Sale: Up to 70% Off Today',
  '🎁 New User Offer: Extra 15% Off First Order',
  '🔒 100% Secure Payments',
  '↩️ 30-Day Easy Returns',
  '📦 1 Million+ Products Delivered Daily',
  '🌟 Rated #1 Marketplace in India',
];

export default function MarqueeStrip() {
  const doubled = [...items, ...items]; // duplicate for seamless loop
  return (
    <div className="marquee-strip">
      <div className="marquee-inner">
        {doubled.map((item, i) => (
          <span key={i} className="marquee-item">
            <span className="marquee-dot" />
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

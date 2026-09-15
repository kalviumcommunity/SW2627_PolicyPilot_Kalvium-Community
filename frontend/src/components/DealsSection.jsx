'use client';
import React, { useState, useEffect } from 'react';

const deals = [
  {
    id: 1,
    badge: '-65%',
    icon: '🎧',
    category: 'Electronics',
    name: 'Pro Wireless Noise Cancelling Headphones',
    price: '₹4,999',
    original: '₹14,999',
    discount: 'Save ₹10,000',
    rating: '★★★★★',
    reviews: '12,481',
  },
  {
    id: 2,
    badge: '-48%',
    icon: '👟',
    category: 'Fashion',
    name: 'Premium Air Cushion Running Shoes',
    price: '₹2,499',
    original: '₹4,799',
    discount: 'Save ₹2,300',
    rating: '★★★★☆',
    reviews: '8,204',
  },
  {
    id: 3,
    badge: '-55%',
    icon: '⌚',
    category: 'Electronics',
    name: 'Smart Fitness Watch with AMOLED Display',
    price: '₹3,299',
    original: '₹7,499',
    discount: 'Save ₹4,200',
    rating: '★★★★★',
    reviews: '21,905',
  },
  {
    id: 4,
    badge: '-42%',
    icon: '💆',
    category: 'Beauty',
    name: 'Vitamin C Glow Serum – 30ml',
    price: '₹899',
    original: '₹1,549',
    discount: 'Save ₹650',
    rating: '★★★★☆',
    reviews: '4,772',
  },
];

function useCountdown(targetHours = 5, targetMinutes = 43, targetSeconds = 20) {
  const [time, setTime] = useState({
    h: targetHours,
    m: targetMinutes,
    s: targetSeconds,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setTime((prev) => {
        let { h, m, s } = prev;
        if (s > 0) return { h, m, s: s - 1 };
        if (m > 0) return { h, m: m - 1, s: 59 };
        if (h > 0) return { h: h - 1, m: 59, s: 59 };
        return { h: 0, m: 0, s: 0 };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return time;
}

export default function DealsSection() {
  const time = useCountdown(5, 43, 20);
  const pad = (n) => String(n).padStart(2, '0');

  return (
    <section className="deals-section" id="deals">
      <div className="deals-header">
        <div>
          <div className="section-label">Limited Time Offers</div>
          <h2 className="section-title">Today's Flash<br />Deals</h2>
        </div>

        {/* Countdown */}
        <div className="countdown-box">
          <div className="countdown-unit">
            <div className="countdown-num">{pad(time.h)}</div>
            <div className="countdown-label">Hours</div>
          </div>
          <div className="countdown-sep">:</div>
          <div className="countdown-unit">
            <div className="countdown-num">{pad(time.m)}</div>
            <div className="countdown-label">Mins</div>
          </div>
          <div className="countdown-sep">:</div>
          <div className="countdown-unit">
            <div className="countdown-num">{pad(time.s)}</div>
            <div className="countdown-label">Secs</div>
          </div>
        </div>
      </div>

      <div className="deals-grid">
        {deals.map((deal) => (
          <div className="deal-card" key={deal.id} id={`deal-${deal.id}`}>
            <span className="deal-badge">{deal.badge}</span>
            <div className="deal-img-wrap">{deal.icon}</div>
            <div className="deal-info">
              <div className="deal-cat">{deal.category}</div>
              <div className="deal-name">{deal.name}</div>
              <div className="deal-price-row">
                <span className="deal-price">{deal.price}</span>
                <span className="deal-original">{deal.original}</span>
              </div>
              <div className="deal-discount">{deal.discount}</div>
              <div className="deal-rating">
                <span className="stars">{deal.rating}</span>
                <span className="rating-count">({deal.reviews})</span>
              </div>
              <button className="add-cart-btn" id={`add-cart-${deal.id}`}>
                Add to Cart
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

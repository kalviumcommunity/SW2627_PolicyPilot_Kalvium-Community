'use client';
import React from 'react';

const categories = [
  { name: 'Fashion', count: '2.4M+ items', icon: '👗', img: '/category_fashion.jpg' },
  { name: 'Electronics', count: '850K+ items', icon: '💻', img: '/category_electronics.jpg' },
  { name: 'Home & Living', count: '1.2M+ items', icon: '🏠', img: '/category_home.jpg' },
  { name: 'Beauty', count: '620K+ items', icon: '✨', img: '/category_beauty.jpg' },
];

export default function CategoriesSection() {
  return (
    <section className="section" id="categories">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div className="section-label">Browse by Category</div>
          <h2 className="section-title">Shop Every<br />Collection</h2>
          <p className="section-desc">From high fashion to home essentials — explore our curated product universe.</p>
        </div>
        <button className="btn-outline" id="view-all-cats-btn">View All Categories →</button>
      </div>

      <div className="categories-grid">
        {categories.map((cat) => (
          <div className="cat-card" key={cat.name} id={`cat-${cat.name.toLowerCase().replace(/\s+/g, '-')}`}>
            <img src={cat.img} alt={cat.name} />
            <div className="cat-card-overlay">
              <div className="cat-icon">{cat.icon}</div>
              <div className="cat-name">{cat.name}</div>
              <div className="cat-count">{cat.count}</div>
              <div className="cat-arrow">→</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

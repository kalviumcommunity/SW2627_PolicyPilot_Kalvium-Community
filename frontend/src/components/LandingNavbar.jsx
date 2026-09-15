'use client';
import React, { useState, useEffect, useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext';

const categories = [
  'Electronics', 'Fashion', 'Home & Living', 'Beauty'
];

export default function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [cartCount] = useState(3);
  const { isDark, toggleDarkMode } = useContext(ThemeContext);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      className="navbar"
      style={{
        background: scrolled
          ? 'rgba(10,10,15,0.96)'
          : 'rgba(10,10,15,0.6)',
      }}
    >
      {/* Logo */}
      <div className="navbar-logo">ShopVerse</div>

      {/* Categories */}
      <div className="navbar-categories">
        {categories.map((cat) => (
          <button key={cat} className="nav-cat-btn">{cat}</button>
        ))}
      </div>

      {/* Search */}
      <div className="navbar-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
        </svg>
        <input type="text" placeholder="Search products, brands..." />
      </div>

      {/* Actions */}
      <div className="navbar-actions">
        {/* Dark mode toggle */}
        <button className="nav-icon-btn" onClick={toggleDarkMode} aria-label="Toggle dark mode">
          {isDark ? '🌙' : '☀️'}
        </button>

        {/* Wishlist */}
        <button className="nav-icon-btn" aria-label="Wishlist">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>

        {/* Cart */}
        <button className="nav-icon-btn" aria-label="Cart">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
          </svg>
          <span className="nav-badge">{cartCount}</span>
        </button>

        {/* Sign In */}
        <button className="nav-cta-btn" id="navbar-signin-btn">Sign In</button>
      </div>
    </nav>
  );
}

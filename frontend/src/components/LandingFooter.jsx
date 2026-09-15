'use client';
import React from 'react';

const footerCols = [
  {
    title: 'Shop',
    links: ['All Products', 'Flash Deals', 'New Arrivals', 'Best Sellers', 'Gift Cards'],
  },
  {
    title: 'Support',
    links: ['Help Center', 'Track Order', 'Returns & Refunds', 'Contact Us', 'Report a Problem'],
  },
  {
    title: 'Company',
    links: ['About ShopVerse', 'Careers', 'Press', 'Blog', 'Investor Relations'],
  },
];

export default function LandingFooter() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        {/* Brand */}
        <div>
          <div className="footer-logo">ShopVerse</div>
          <p className="footer-tagline">
            India's fastest-growing marketplace for millions of products across every category imaginable.
          </p>
          <div className="footer-socials">
            {['𝕏', 'in', 'f', '▶', '📸'].map((s, i) => (
              <button key={i} className="social-btn" aria-label={`Social ${i}`}>{s}</button>
            ))}
          </div>
        </div>

        {/* Columns */}
        {footerCols.map((col) => (
          <div key={col.title}>
            <div className="footer-col-title">{col.title}</div>
            {col.links.map((link) => (
              <a key={link} href="#" className="footer-link">{link}</a>
            ))}
          </div>
        ))}
      </div>

      {/* Bottom bar */}
      <div className="footer-bottom">
        <div className="footer-copy">
          © {new Date().getFullYear()} ShopVerse. All rights reserved.
        </div>
        <div className="footer-legal">
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">Cookie Policy</a>
          <a href="#">Sitemap</a>
        </div>
      </div>
    </footer>
  );
}

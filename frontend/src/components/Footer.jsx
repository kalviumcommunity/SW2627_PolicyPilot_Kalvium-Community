"use client";

import React from 'react';
import Link from 'next/link';

const footerLinks = [
  {
    title: 'Product',
    links: [
      { label: 'Dashboard', href: '/dashboard' },
      { label: 'AI Chat', href: '/chatbot' },
      { label: 'Policy Search', href: '/chatbot' },
    ],
  },
  {
    title: 'Support',
    links: [
      { label: 'Help Center', href: '#' },
      { label: 'Documentation', href: '#' },
      { label: 'Contact Us', href: '#' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#' },
      { label: 'Terms of Service', href: '#' },
      { label: 'Cookie Policy', href: '#' },
    ],
  },
];

const socialLinks = [
  {
    label: 'Twitter/X',
    href: '#',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.26 5.632 5.904-5.632zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
    ),
  },
  {
    label: 'LinkedIn',
    href: '#',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/>
      </svg>
    ),
  },
  {
    label: 'GitHub',
    href: '#',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
      </svg>
    ),
  },
];

export default function Footer() {
  return (
    <footer className="app-footer" id="main-app-footer">
      {/* Top section */}
      <div className="app-footer-top">
        {/* Brand */}
        <div className="app-footer-brand">
          <Link href="/dashboard" className="app-footer-logo" id="footer-logo-link">
            <div className="app-footer-logo-mark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.5C17.25 22.15 21 17.25 21 12V7l-9-5z" fill="url(#footerShieldGrad)" />
                <defs>
                  <linearGradient id="footerShieldGrad" x1="0" y1="0" x2="24" y2="24">
                    <stop offset="0%" stopColor="#7c3aed" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span>PolicyPilot</span>
          </Link>
          <p className="app-footer-tagline">
            Grounded, AI-powered answers for every ShopVerse policy question — instantly.
          </p>
          <div className="app-footer-socials">
            {socialLinks.map((s) => (
              <a
                key={s.label}
                href={s.href}
                className="app-footer-social-btn"
                aria-label={s.label}
                id={`footer-social-${s.label.toLowerCase().replace(/\//g, '-')}`}
              >
                {s.icon}
              </a>
            ))}
          </div>
        </div>

        {/* Links */}
        <div className="app-footer-links-grid">
          {footerLinks.map((col) => (
            <div key={col.title} className="app-footer-col">
              <h3 className="app-footer-col-title">{col.title}</h3>
              <ul className="app-footer-col-list">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="app-footer-link">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="app-footer-bottom">
        <p className="app-footer-copy">
          © {new Date().getFullYear()} ShopVerse Operations · PolicyPilot v2.0
        </p>
        <div className="app-footer-status">
          <span className="app-status-dot" aria-hidden="true" />
          <span>All systems operational</span>
        </div>
        <div className="app-footer-legal">
          <a href="#" className="app-footer-legal-link" id="footer-privacy-link">Privacy</a>
          <a href="#" className="app-footer-legal-link" id="footer-terms-link">Terms</a>
          <a href="#" className="app-footer-legal-link" id="footer-cookies-link">Cookies</a>
        </div>
      </div>
    </footer>
  );
}

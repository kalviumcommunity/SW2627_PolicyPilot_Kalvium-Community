'use client';

import React from 'react';
import Link from 'next/link';

const footerLinks = [
  {
    title: 'Platform',
    links: [
      { label: 'Workspace Dashboard', href: '/dashboard' },
      { label: 'Policy Assistant', href: '/chatbot' },
      { label: 'MongoDB Vector Index', href: '/dashboard' },
    ],
  },
  {
    title: 'Developer',
    links: [
      { label: 'FastAPI Swagger Docs', href: 'http://localhost:8000/docs', external: true },
      { label: 'SSE Stream Endpoint', href: '/chatbot' },
      { label: 'Query Cache Specification', href: '/dashboard' },
    ],
  },
  {
    title: 'Governance',
    links: [
      { label: 'Confidence Thresholds', href: '/dashboard' },
      { label: 'Hallucination Guardrails', href: '/dashboard' },
      { label: 'Audit Trail Logs', href: '/dashboard' },
    ],
  },
];

const socialLinks = [
  {
    label: 'GitHub',
    href: 'https://github.com',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
      </svg>
    ),
  },
  {
    label: 'LinkedIn',
    href: 'https://linkedin.com',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/>
      </svg>
    ),
  },
];

export default function Footer() {
  return (
    <footer className="app-footer" id="main-app-footer">
      <div className="app-footer-top">
        <div className="app-footer-brand">
          <Link href="/dashboard" className="app-footer-logo" id="footer-logo-link">
            <div className="app-footer-logo-mark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="currentColor" fillOpacity="0.15" />
                <path d="M9 12l2 2 4-4" stroke="#4f46e5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span>PolicyPilot</span>
          </Link>
          <p className="app-footer-tagline">
            Grounded, citation-backed answers for every organizational policy question.
          </p>
          <div className="app-footer-socials">
            {socialLinks.map((s) => (
              <a
                key={s.label}
                href={s.href}
                target="_blank"
                rel="noopener noreferrer"
                className="app-footer-social-btn"
                aria-label={s.label}
                id={`footer-social-${s.label.toLowerCase()}`}
              >
                {s.icon}
              </a>
            ))}
          </div>
        </div>

        <div className="app-footer-cols">
          {footerLinks.map((col) => (
            <div key={col.title} className="app-footer-col">
              <h4>{col.title}</h4>
              <ul>
                {col.links.map((link) => (
                  <li key={link.label}>
                    {link.external ? (
                      <a href={link.href} target="_blank" rel="noopener noreferrer">
                        {link.label}
                      </a>
                    ) : (
                      <Link href={link.href}>{link.label}</Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="app-footer-bottom">
        <p className="app-footer-copy">
          © {new Date().getFullYear()} <strong>PolicyPilot</strong>. Enterprise RAG Application.
        </p>
        <div className="app-footer-status">
          <span className="landing-status-dot" />
          <span>MongoDB Vector Store Connected · Latency ~48ms</span>
        </div>
      </div>
    </footer>
  );
}

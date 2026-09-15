'use client';

import { useState } from "react";
import Link from "next/link";
import PolicyChatWidget from "../components/PolicyChatWidget";

export default function Home({ initialNav = "Dashboard" }) {
  const [activeNav, setActiveNav] = useState(initialNav);

  const openChat = () => window.dispatchEvent(new Event("open-policy-chat"));

  return (
    <main className="ops-shell">
      <aside className="ops-sidebar">
        <div className="ops-brand">
          <div className="ops-brand-mark">P</div>
          <div><strong>PolicyPilot</strong><span>ShopVerse operations</span></div>
        </div>
        <div className="ops-sidebar-label">Workspace</div>
        <nav className="ops-nav" aria-label="Policy operations navigation">
          {["Dashboard", "Policy assistant", "Policy library", "Seller agreements"].map((item) => (
            item === "Dashboard" || item === "Policy assistant" ? (
              <Link key={item} href={item === "Dashboard" ? "/dashboard" : "/chatbot"} className={`ops-nav-item ${activeNav === item ? "is-active" : ""}`}>
                <span className="ops-nav-icon" aria-hidden="true">{item === "Dashboard" ? "⌂" : "✦"}</span>
                {item}{item === "Policy assistant" && <span className="ops-live-dot" />}
              </Link>
            ) : (
              <button key={item} className={`ops-nav-item ${activeNav === item ? "is-active" : ""}`} onClick={() => setActiveNav(item)}>
                <span className="ops-nav-icon" aria-hidden="true">{item === "Policy library" ? "▤" : "◫"}</span>
                {item}
              </button>
            )
          ))}
        </nav>
        <div className="ops-sidebar-foot">
          <div className="ops-status"><span /> Knowledge base synced</div>
          <Link href="/login" className="ops-user"><span className="ops-user-avatar">OP</span><span><strong>Operations</strong><small>ShopVerse team</small></span><span className="ops-more">•••</span></Link>
        </div>
      </aside>

      <section className="ops-content">
        <header className="ops-topbar"><div className="ops-breadcrumb"><span>ShopVerse</span><b>/</b> Policy operations</div><div className="ops-top-actions"><span className="ops-date">Monday, 14 September 2026</span><button className="ops-icon-button" aria-label="Notifications">♧<i /></button><button className="ops-avatar-button" aria-label="Open account">OP</button></div></header>
        <div className="ops-main">
          <div className="ops-heading-row"><div><p className="ops-eyebrow">Policy intelligence center</p><h1>Make every answer <em>precise.</em></h1><p className="ops-heading-copy">One grounded workspace for returns, delivery, seller agreements, and every policy question behind the ShopVerse experience.</p></div><button className="ops-primary-button" onClick={openChat}><span>✦</span> Ask PolicyPilot</button></div>

          <section className="ops-chat-hero" aria-label="PolicyPilot assistant overview"><div className="ops-chat-orbit orbit-one" /><div className="ops-chat-orbit orbit-two" /><div className="ops-chat-copy"><div className="ops-assistant-badge"><span>●</span> PolicyPilot is online</div><h2>Answers grounded in the<br /><strong>policy text you trust.</strong></h2><p>Ask in plain language. PolicyPilot searches the ShopVerse knowledge base, gives the exact rule, and shows the source behind it.</p><div className="ops-prompt-row"><button onClick={openChat}>What is our return window? <span>↗</span></button><button onClick={openChat}>When do sellers dispatch? <span>↗</span></button></div></div><div className="ops-chat-visual" aria-hidden="true"><div className="ops-shield">✦</div><div className="ops-visual-line line-one">Returns & refunds <b>[1]</b></div><div className="ops-visual-line line-two">Seller dispatch SLA <b>[2]</b></div><div className="ops-visual-line line-three">Delivery timelines <b>[3]</b></div></div></section>

          <div className="ops-section-heading"><div><p className="ops-eyebrow">At a glance</p><h2>Policy coverage</h2></div><span>Updated from the live knowledge base</span></div>
          <section className="ops-metrics"><article><span className="metric-icon coral">↩</span><div><strong>Returns & refunds</strong><p>Eligibility, windows, damaged items</p></div><b>›</b></article><article><span className="metric-icon mint">◌</span><div><strong>Shipping & delivery</strong><p>Timelines, charges, cancellations</p></div><b>›</b></article><article><span className="metric-icon amber">♧</span><div><strong>Seller agreements</strong><p>Dispatch and marketplace duties</p></div><b>›</b></article></section>

          <section className="user-tracking"><div><p className="ops-eyebrow">Order tracking</p><h2>No order data connected</h2><p>Connect your ShopVerse order service to show live delivery status here.</p></div><div className="tracking-empty"><span>◌</span><p>Live tracking will appear here<br />when an order source is available.</p></div><button onClick={openChat}>Have a policy question? <span>Ask PolicyPilot ↗</span></button></section>

          <section className="ops-bottom-grid"><div className="ops-activity"><div className="ops-section-heading compact"><div><p className="ops-eyebrow">Recent activity</p><h2>Policy questions</h2></div><button onClick={openChat}>Open assistant →</button></div><div className="activity-empty">No conversation history is connected yet. Start a grounded conversation with PolicyPilot.</div></div><div className="ops-note"><span className="note-pin">✦</span><p className="ops-eyebrow">Why this matters</p><h3>Less guesswork.<br />More customer trust.</h3><p>Every citation gives your team a clear path back to the source of truth.</p></div></section>
        </div>
      </section>

      <PolicyChatWidget />
    </main>
  );
}


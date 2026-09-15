'use client';

import React from 'react';
import LandingNavbar from '../components/LandingNavbar';
import HeroSection from '../components/HeroSection';
import MarqueeStrip from '../components/MarqueeStrip';
import CategoriesSection from '../components/CategoriesSection';
import DealsSection from '../components/DealsSection';
import TrustSection from '../components/TrustSection';
import NewsletterSection from '../components/NewsletterSection';
import LandingFooter from '../components/LandingFooter';
import PolicyChatWidget from '../components/PolicyChatWidget';

export default function Home() {
  return (
    <div className="landing-page-wrapper" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <LandingNavbar />
      <main style={{ flex: 1 }}>
        <HeroSection />
        <MarqueeStrip />
        <CategoriesSection />
        <DealsSection />
        <TrustSection />
        <NewsletterSection />
      </main>
      <LandingFooter />
      <PolicyChatWidget />
    </div>
  );
}

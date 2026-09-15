'use client';

import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({ children }) {
  const { user, role, isReady } = useAuth() || {};
  const router = useRouter();

  useEffect(() => {
    if (!isReady) return;
    if (!user) router.replace('/login');
  }, [isReady, user, router]);

  if (!isReady || !user) return null;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark, #f8fafc)', color: 'var(--text-main, #0f172a)' }}>
      <Header />
      <main style={{ flex: 1, width: '100%' }}>{children}</main>
      <Footer />
    </div>
  );
}

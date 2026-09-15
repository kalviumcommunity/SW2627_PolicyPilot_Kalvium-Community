'use client';

import Header from "../../components/Header";
import Footer from "../../components/Footer";
import Sidebar from "../../components/Sidebar";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({ children }) {
  const { user, role, isReady } = useAuth() || {};
  const router = useRouter();

  useEffect(() => {
    if (!isReady) return;
    if (!user) router.replace('/login');
    else if (role !== 'user') router.replace(role === 'admin' ? '/admin' : '/login');
  }, [isReady, user, role, router]);

  if (!isReady || !user || role !== 'user') return null;

  return (
    <div className="flex min-h-screen bg-[var(--bg-dark)] text-[var(--text-main)]">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Header />
        <main className="flex-1 p-4">{children}</main>
        <Footer />
      </div>
    </div>
  );
}

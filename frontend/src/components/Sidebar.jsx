import React from 'react';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { role } = useAuth() || {};
  const commonLinks = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/chatbot', label: 'Chatbot' },
  ];
  const adminLinks = [
    { href: '/admin', label: 'Admin Panel' },
    { href: '/admin/users', label: 'User List' },
    { href: '/admin/stats', label: 'Stats' },
  ];

  const links = role === 'admin' ? [...commonLinks, ...adminLinks] : commonLinks;

  return (
    <nav className="w-64 bg-[var(--panel-bg)] border-r border-[var(--border-color)] min-h-screen p-4">
      <ul className="space-y-2">
        {links.map((link) => (
          <li key={link.href}>
            <Link href={link.href} className="block px-3 py-2 rounded hover:bg-primary hover:text-white transition-colors">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;

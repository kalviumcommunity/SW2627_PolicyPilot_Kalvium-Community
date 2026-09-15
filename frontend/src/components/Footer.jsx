import React from 'react';

export default function Footer() {
  return (
    <footer className="p-4 text-center text-sm text-[var(--text-muted)] bg-[var(--panel-bg)] border-t border-[var(--border-color)]">
      © {new Date().getFullYear()} PolicyPilot. All rights reserved.
    </footer>
  );
}

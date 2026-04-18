import { useState, type ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
  onPageChange: (page: 'dashboard' | 'settings') => void;
  currentPage: string;
}

export function Layout({ children, onPageChange, currentPage }: LayoutProps) {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1 className="app-title">YT Shorts Dashboard</h1>
        <nav className="app-nav">
          <button
            className={`nav-btn ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => onPageChange('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`nav-btn ${currentPage === 'settings' ? 'active' : ''}`}
            onClick={() => onPageChange('settings')}
          >
            Settings
          </button>
        </nav>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}

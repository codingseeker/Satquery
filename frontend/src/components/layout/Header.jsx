import React from 'react';
import { Menu, Orbit } from 'lucide-react';

export default function Header({ onToggleSidebar, sidebarOpen }) {
  return (
    <header className="app-header" role="banner">
      <div className="header-left">
        <button
          className="header-menu-btn"
          onClick={onToggleSidebar}
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <Menu size={20} />
        </button>
      </div>

      <div className="header-center">
        <div className="header-model-pill">
          <Orbit size={14} />
          <span className="header-model-name">SatQuery AI</span>
        </div>
      </div>

      <div className="header-right" />
    </header>
  );
}

import React, { useState } from 'react';
import {
  Plus, Search, MessageSquare, Clock3, Settings, PanelLeftClose,
  Orbit, Trash2, ChevronDown, LogOut, Info, PanelLeft, Pencil, Check, X
} from 'lucide-react';

/**
 * ChatGPT-style left sidebar.
 * Contains: new chat, search, conversation list, settings, user profile.
 * Collapsible on all screen sizes.
 */
export default function Sidebar({
  conversations,
  activeId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  onSettings,
  onAbout,
  onLogout,
  userEmail,
  collapsed,
  onToggle,
}) {
  const [hoverId, setHoverId] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = searchQuery.trim()
    ? conversations.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : conversations;

  function startRename(conv) {
    setRenamingId(conv.id);
    setRenameValue(conv.title);
  }

  function commitRename(id) {
    if (renameValue.trim()) onRenameChat(id, renameValue.trim());
    setRenamingId(null);
    setRenameValue('');
  }

  if (collapsed) {
    return (
      <aside className="sidebar sidebar-collapsed" aria-label="Collapsed sidebar">
        <button className="sb-icon-btn" onClick={onToggle} title="Expand sidebar">
          <PanelLeft size={19} />
        </button>
        <button className="sb-icon-btn" onClick={onNewChat} title="New analysis">
          <Plus size={19} />
        </button>
        <div className="sb-collapsed-spacer" />
        <button className="sb-icon-btn" onClick={onSettings} title="Settings">
          <Settings size={18} />
        </button>
        <button className="sb-icon-btn" onClick={onAbout} title="About SatQuery AI">
          <Info size={18} />
        </button>
        <button className="sb-icon-btn" onClick={onLogout} title="Log out">
          <LogOut size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside className="sidebar" aria-label="Sidebar">
      {/* Brand + collapse */}
      <div className="sb-brand">
        <div className="sb-brand-mark" aria-hidden="true"><Orbit size={18} /></div>
        <div className="sb-brand-text">
          <span className="sb-brand-name">SatQuery AI</span>
        </div>
        <button className="sb-icon-btn sb-collapse-btn" onClick={onToggle} title="Collapse sidebar">
          <PanelLeftClose size={17} />
        </button>
      </div>

      {/* New chat */}
      <button className="sb-new-chat" onClick={onNewChat}>
        <Plus size={16} />
        New analysis
      </button>

      {/* Search */}
      <div className="sb-search">
        <Search size={14} />
        <input
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search conversations…"
          aria-label="Search conversations"
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} aria-label="Clear search"><X size={13} /></button>
        )}
      </div>

      {/* Conversation list */}
      <div className="sb-section-label">
        <Clock3 size={12} />
        <span>Recent</span>
      </div>

      <nav className="sb-chat-list" aria-label="Conversation history">
        {filtered.length === 0 && (
          <div className="sb-empty">
            {searchQuery ? 'No conversations found.' : 'No analyses yet. Start a new analysis.'}
          </div>
        )}

        {filtered.map(conv => (
          <div
            key={conv.id}
            className={`sb-chat-item ${activeId === conv.id ? 'active' : ''}`}
            onMouseEnter={() => setHoverId(conv.id)}
            onMouseLeave={() => { setHoverId(null); }}
          >
            {renamingId === conv.id ? (
              <div className="sb-rename-row">
                <input
                  className="sb-rename-input"
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') commitRename(conv.id);
                    if (e.key === 'Escape') setRenamingId(null);
                  }}
                  autoFocus
                />
                <button onClick={() => commitRename(conv.id)} title="Save"><Check size={13} /></button>
                <button onClick={() => setRenamingId(null)} title="Cancel"><X size={13} /></button>
              </div>
            ) : (
              <>
                <button
                  className="sb-chat-btn"
                  onClick={() => onSelectChat(conv.id)}
                  title={conv.title}
                >
                  <MessageSquare size={14} />
                  <span className="sb-chat-title">{conv.title}</span>
                </button>

                {(hoverId === conv.id || activeId === conv.id) && (
                  <div className="sb-chat-actions">
                    <button
                      className="sb-action-btn"
                      onClick={() => startRename(conv)}
                      title="Rename"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      className="sb-action-btn sb-action-delete"
                      onClick={() => onDeleteChat(conv.id)}
                      title="Delete"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sb-footer">
        <button className="sb-footer-btn" onClick={onSettings}>
          <Settings size={16} />
          <span>Settings</span>
        </button>
        <button className="sb-footer-btn" onClick={onAbout}>
          <Info size={16} />
          <span>About SatQuery AI</span>
        </button>

        {/* User profile */}
        <div className="sb-profile-wrap">
          <button
            className="sb-profile-btn"
            onClick={() => setProfileOpen(v => !v)}
            aria-expanded={profileOpen}
            aria-haspopup="menu"
          >
            <div className="sb-avatar" aria-hidden="true">
              {userEmail ? userEmail[0].toUpperCase() : 'U'}
            </div>
            <div className="sb-profile-info">
              <span className="sb-profile-email">{userEmail || 'student@satquery.ai'}</span>
              <span className="sb-profile-workspace">SatQuery workspace</span>
            </div>
            <ChevronDown size={14} className={`sb-chevron ${profileOpen ? 'open' : ''}`} />
          </button>

          {profileOpen && (
            <div className="sb-profile-menu" role="menu">
              <div className="sb-profile-menu-head">
                <div className="sb-avatar sb-avatar-lg">
                  {userEmail ? userEmail[0].toUpperCase() : 'U'}
                </div>
                <div>
                  <div className="sb-profile-menu-name">{userEmail || 'student@satquery.ai'}</div>
                  <div className="sb-profile-menu-role">SIH26167 · Student</div>
                </div>
              </div>
              <button className="sb-profile-menu-item sb-logout" onClick={onLogout} role="menuitem">
                <LogOut size={14} />
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

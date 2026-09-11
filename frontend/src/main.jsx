import React, { useState, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import SettingsPanel from './components/settings/SettingsPanel';
import WelcomeScreen from './components/chat/WelcomeScreen';
import MessageList from './components/chat/MessageList';
import Composer from './components/chat/Composer';

import { sendQuery, listConversations as fetchConversations, deleteConversation as apiDeleteConversation } from './services/chatService';
import { uploadImage } from './services/imageService';
import { generateId } from './utils/fileUtils';
import { SIH_PROBLEM_STATEMENT } from './utils/constants';
import api from './services/api';

// ─── Login page ───────────────────────────────────────────────────────────────
import { Mail, Lock, Eye, EyeOff, Orbit } from 'lucide-react';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter your email and password.');
      return;
    }
    if (password.trim().length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password: password.trim() }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      localStorage.setItem('satquery_token', data.access_token);
      onLogin({ email: data.user.email, user: data.user });
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="login-brand-mark"><Orbit size={18} /></div>
        <span className="login-brand-name">SatQuery AI</span>
      </div>

      <div className="login-card">
        <h1 className="login-heading">{isRegister ? 'Create account' : 'Welcome back'}</h1>
        <p className="login-sub">{isRegister ? 'Sign up to start satellite imagery analysis.' : 'Sign in to continue satellite imagery analysis.'}</p>

        <form onSubmit={submit} noValidate>
          <div className="login-field">
            <label htmlFor="login-email">Email</label>
            <div className="login-input-wrap">
              <Mail size={15} />
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>
          </div>

          <div className="login-field">
            <label htmlFor="login-password">Password</label>
            <div className="login-input-wrap">
              <Lock size={15} />
              <input
                id="login-password"
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                autoComplete="current-password"
              />
              <button type="button" onClick={() => setShowPw(v => !v)} aria-label={showPw ? 'Hide password' : 'Show password'}>
                {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {error && <div className="login-error" role="alert">{error}</div>}

          <button className="login-submit" type="submit" disabled={loading}>
            {loading ? 'Please wait...' : isRegister ? 'Create account' : 'Sign in'}
          </button>
        </form>

<div className="login-divider"><span>or</span></div>

<button className="login-demo mt-2" onClick={() => setIsRegister(v => !v)}>
  {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
</button>

<p className="login-note">
  Backend authentication. Register a new account or sign in with existing credentials.
</p>

<div className="login-divider"><span>or connect with</span></div>

<div className="login-oauth-grid">
  <button className="login-oauth-btn" onClick={() => onLogin({ email: 'google_user@satquery.ai' })}>
    <svg viewBox="0 0 24 24" width="16" height="16" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
    Google
  </button>
</div>
      </div>
    </div>
  );
}

// ─── Conversation helpers ─────────────────────────────────────────────────────

function makeConversation(title) {
  return { id: generateId(), title, messages: [], createdAt: new Date() };
}

function makeUserMessage(content, uploadedFiles) {
  return {
    id: generateId(),
    role: 'user',
    content,
    uploadedFiles: uploadedFiles || [],
    timestamp: new Date(),
    isLoading: false,
    error: null,
    analysis: null,
  };
}

function makeAssistantMessage(overrides = {}) {
  return {
    id: generateId(),
    role: 'assistant',
    content: '',
    uploadedFiles: [],
    timestamp: null,
    isLoading: true,
    error: null,
    analysis: null,
    ...overrides,
  };
}

// ─── Main App ─────────────────────────────────────────────────────────────────

function App() {
  const [authenticated, setAuthenticated] = useState(() => !!localStorage.getItem('satquery_token'));
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem('satquery_email') || '');

  // Theme: 'light' | 'dark'
  const [theme, setTheme] = useState('light');
  const [accent, setAccent] = useState('#6366f1');
  const [contrast, setContrast] = useState('standard');

  // Sidebar
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);

  // Conversations
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);

  // Welcome screen uploaded files (before first message)
  const [welcomeFiles, setWelcomeFiles] = useState([]);

  // Loading state
  const [isLoading, setIsLoading] = useState(false);

  // ── Auth ──────────────────────────────────────────────────────────────────
  function login({ email, user }) {
    setUserEmail(email);
    localStorage.setItem('satquery_email', email);
    setAuthenticated(true);
  }

  function logout() {
    localStorage.removeItem('satquery_token');
    localStorage.removeItem('satquery_email');
    setAuthenticated(false);
    setUserEmail('');
    setConversations([]);
    setActiveConvId(null);
    setWelcomeFiles([]);
  }

  // On mount: validate the stored token against the backend immediately.
  // If it's expired or invalid, clear state and show login right away.
  React.useEffect(() => {
    const token = localStorage.getItem('satquery_token');
    if (!token) return;
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000';
    fetch(`${apiBase}/api/conversations`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(res => {
      if (res.status === 401) {
        localStorage.removeItem('satquery_token');
        localStorage.removeItem('satquery_email');
        setAuthenticated(false);
        setUserEmail('');
      }
    }).catch(() => { /* network error - keep authenticated state, user will see errors inline */ });
  }, []);

  // Listen for 401 events dispatched by api.js during normal usage
  React.useEffect(() => {
    function handleLogout() {
      localStorage.removeItem('satquery_token');
      localStorage.removeItem('satquery_email');
      setAuthenticated(false);
      setUserEmail('');
      setConversations([]);
      setActiveConvId(null);
      setWelcomeFiles([]);
    }
    window.addEventListener('satquery:logout', handleLogout);
    return () => window.removeEventListener('satquery:logout', handleLogout);
  }, []);

  // ── Conversation management ───────────────────────────────────────────────
  const activeConv = conversations.find(c => c.id === activeConvId) || null;

  function newChat() {
    const conv = makeConversation('New analysis');
    setConversations(prev => [conv, ...prev]);
    setActiveConvId(conv.id);
    setWelcomeFiles([]);
  }

  function selectChat(id) {
    setActiveConvId(id);
    setWelcomeFiles([]);
  }

  function deleteChat(id) {
    const conv = conversations.find(c => c.id === id);
    if (conv?.backendId) {
      apiDeleteConversation(conv.backendId).catch(() => {});
    }
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConvId === id) {
      const remaining = conversations.filter(c => c.id !== id);
      setActiveConvId(remaining[0]?.id || null);
    }
  }

  function renameChat(id, title) {
    setConversations(prev => prev.map(c => c.id === id ? { ...c, title } : c));
  }

  function clearAllConversations() {
    setConversations([]);
    setActiveConvId(null);
    setWelcomeFiles([]);
  }

  // Update messages in the active conversation
  function updateMessages(convId, updater) {
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: updater(c.messages) } : c)
    );
  }

  // ── Sending a message ─────────────────────────────────────────────────────
  const send = useCallback(async (content, attachedFiles = []) => {
    if (isLoading) return;

    let convId = activeConvId;
    let backendConvId = null;

    if (!convId) {
      const title = content.length > 50 ? content.slice(0, 47) + '…' : content || 'New analysis';
      try {
        const backendChat = await api.post('/api/chats', { title });
        backendConvId = String(backendChat.id);
        const conv = { id: backendConvId, title, backendId: backendChat.id, messages: [], createdAt: new Date() };
        setConversations(prev => [conv, ...prev]);
        setActiveConvId(backendConvId);
        convId = backendConvId;
        await new Promise(r => setTimeout(r, 0));
      } catch (err) {
        const conv = makeConversation(title);
        setConversations(prev => [conv, ...prev]);
        setActiveConvId(conv.id);
        convId = conv.id;
        await new Promise(r => setTimeout(r, 0));
      }
    } else {
      const existing = conversations.find(c => c.id === convId);
      backendConvId = existing?.backendId || null;
    }

    if (!backendConvId) {
      try {
        const chats = await fetchConversations();
        const title = content.length > 50 ? content.slice(0, 47) + '…' : content || 'New analysis';
        const matched = chats.find(c => c.id === convId || String(c.id) === convId);
        if (matched) {
          backendConvId = matched.id;
          setConversations(prev =>
            prev.map(c => c.id === convId ? { ...c, backendId: matched.id } : c)
          );
        } else {
          const newChat = await api.post('/api/chats', { title });
          backendConvId = String(newChat.id);
          setConversations(prev =>
            prev.map(c => c.id === convId ? { ...c, id: backendConvId, backendId: newChat.id } : c)
          );
          setActiveConvId(backendConvId);
          convId = backendConvId;
        }
      } catch (err) {
        console.error('Failed to create conversation on backend:', err);
      }
    }

    const allFiles = [...attachedFiles];

    setConversations(prev =>
      prev.map(c => {
        if (c.id !== convId) return c;
        if (c.title === 'New analysis' && content) {
          const t = content.length > 50 ? content.slice(0, 47) + '…' : content;
          return { ...c, title: t };
        }
        return c;
      })
    );

    const userMsg = makeUserMessage(content, allFiles);
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: [...c.messages, userMsg] } : c)
    );

    const aiMsg = makeAssistantMessage();
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: [...c.messages, aiMsg] } : c)
    );

    setIsLoading(true);

    try {
      const imageIds = [];
      for (const f of allFiles) {
        const result = await uploadImage(f.file || f);
        if (result?.image_id) imageIds.push(result.image_id);
      }

      const queryConvId = String(backendConvId || convId);
      const analysis = await sendQuery({
        conversationId: queryConvId,
        query: content,
        imageIds,
        hasImages: allFiles.length > 0,
      });

      setConversations(prev =>
        prev.map(c => {
          if (c.id !== convId) return c;
          return {
            ...c,
            messages: c.messages.map(m =>
              m.id === aiMsg.id
                ? {
                    ...m,
                    content: analysis.answer,
                    analysis,
                    uploadedFiles: allFiles,
                    timestamp: new Date(),
                    isLoading: false,
                  }
                : m
            ),
          };
        })
      );
    } catch (err) {
      setConversations(prev =>
        prev.map(c => {
          if (c.id !== convId) return c;
          return {
            ...c,
            messages: c.messages.map(m =>
              m.id === aiMsg.id
                ? { ...m, isLoading: false, error: err.message || 'Analysis failed. Please try again.' }
                : m
            ),
          };
        })
      );
    } finally {
      setIsLoading(false);
    }
  }, [activeConvId, isLoading, welcomeFiles]);

  // ── Regenerate ────────────────────────────────────────────────────────────
  async function regenerate(msgId) {
    if (!activeConv || isLoading) return;
    const msgs = activeConv.messages;
    const aiIdx = msgs.findIndex(m => m.id === msgId);
    if (aiIdx < 0) return;
    const userMsg = msgs.slice(0, aiIdx).findLast(m => m.role === 'user');
    if (!userMsg) return;

    // Remove the old AI message and re-send
    setConversations(prev =>
      prev.map(c =>
        c.id === activeConvId
          ? { ...c, messages: c.messages.filter(m => m.id !== msgId) }
          : c
      )
    );
    send(userMsg.content, userMsg.uploadedFiles || []);
  }

  // ── Welcome file management ───────────────────────────────────────────────
  function addWelcomeFiles(files) {
    setWelcomeFiles(prev => [...prev, ...files]);
  }

  function removeWelcomeFile(id) {
    setWelcomeFiles(prev => {
      const f = prev.find(f => f.id === id);
      if (f?.url) URL.revokeObjectURL(f.url);
      return prev.filter(f => f.id !== id);
    });
  }

  // ── Render ────────────────────────────────────────────────────────────────
  if (!authenticated) {
    return (
      <div className={`app ${theme} contrast-${contrast}`} style={{
      '--accent': accent,
      '--accent-h': accent,
      '--accent-light': `${accent}18`,
      '--accent-border': `${accent}40`,
      '--active': `${accent}14`,
    }}>
        <LoginPage onLogin={login} />
      </div>
    );
  }

  const messages = activeConv?.messages || [];
  const showWelcome = messages.length === 0;

  return (
    <div className={`app ${theme} contrast-${contrast}`} style={{
      '--accent': accent,
      '--accent-h': accent,
      '--accent-light': `${accent}18`,
      '--accent-border': `${accent}40`,
      '--active': `${accent}14`,
    }}>
      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-mobile-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        onNewChat={newChat}
        onSelectChat={selectChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        onSettings={() => setSettingsOpen(true)}
        onAbout={() => setAboutOpen(true)}
        onLogout={logout}
        userEmail={userEmail}
        collapsed={!sidebarOpen}
        onToggle={() => setSidebarOpen(v => !v)}
      />

      <div className="app-main">
        <Header onToggleSidebar={() => setSidebarOpen(v => !v)} sidebarOpen={sidebarOpen} />

        <div className="chat-area">
          {showWelcome ? (
            <WelcomeScreen onAsk={(prompt) => send(prompt, [])} />
          ) : (
            <MessageList
              messages={messages}
              isLoading={isLoading}
              onRegenerate={regenerate}
              onCopy={() => {}}
            />
          )}
        </div>

        <Composer
          onSend={send}
          loading={isLoading}
          onStop={() => setIsLoading(false)}
          disabled={false}
        />
      </div>

      {/* About SatQuery AI modal */}
      {aboutOpen && (
        <div className="about-backdrop" onClick={() => setAboutOpen(false)} role="dialog" aria-modal="true" aria-label="About SatQuery AI">
          <div className="about-modal" onClick={e => e.stopPropagation()}>
            <div className="about-modal-header">
              <div><h2>About SatQuery AI</h2><p>Interactive vision-language assistant for remote sensing imagery.</p></div>
              <button className="about-close" onClick={() => setAboutOpen(false)} aria-label="Close about"><span>×</span></button>
            </div>
            <div className="about-modal-body">
              <div className="about-info-row"><span>Problem statement</span><strong>{SIH_PROBLEM_STATEMENT.id}</strong></div>
              <div className="about-info-row"><span>Hackathon</span><strong>{SIH_PROBLEM_STATEMENT.hackathon}</strong></div>
              <div className="about-info-row"><span>Version</span><strong>SatQuery AI</strong></div>
              <p>{SIH_PROBLEM_STATEMENT.description}</p>
            </div>
          </div>
        </div>
      )}

      {/* Settings overlay */}
      {settingsOpen && (
        <SettingsPanel
          theme={theme}
          setTheme={setTheme}
          accent={accent}
          setAccent={setAccent}
          contrast={contrast}
          setContrast={setContrast}
          userEmail={userEmail}
          conversations={conversations}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

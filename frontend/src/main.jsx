import React, { useState, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import SettingsPanel from './components/settings/SettingsPanel';
import WelcomeScreen from './components/chat/WelcomeScreen';
import MessageList from './components/chat/MessageList';
import Composer from './components/chat/Composer';

import { sendQuery } from './services/chatService';
import { uploadImage } from './services/imageService';
import { generateId } from './utils/fileUtils';
import { SIH_PROBLEM_STATEMENT } from './utils/constants';

// ─── Login page ───────────────────────────────────────────────────────────────
import { Mail, Lock, Eye, EyeOff, Orbit } from 'lucide-react';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');

  function submit(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter your email and password.');
      return;
    }
    setError('');
    onLogin({ email: email.trim() });
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="login-brand-mark"><Orbit size={18} /></div>
        <span className="login-brand-name">SatQuery AI</span>
      </div>

      <div className="login-card">
        <h1 className="login-heading">Welcome back</h1>
        <p className="login-sub">Sign in to continue satellite imagery analysis.</p>

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
                placeholder="Enter your password"
                autoComplete="current-password"
              />
              <button type="button" onClick={() => setShowPw(v => !v)} aria-label={showPw ? 'Hide password' : 'Show password'}>
                {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {error && <div className="login-error" role="alert">{error}</div>}

          <button className="login-submit" type="submit">Sign in</button>
        </form>

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
          <button className="login-oauth-btn" onClick={() => onLogin({ email: 'github_user@satquery.ai' })}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
            </svg>
            GitHub
          </button>
        </div>

        <button className="login-demo mt-2" onClick={() => onLogin({ email: 'student@satquery.ai' })}>
          Continue as demo student
        </button>
        <p className="login-note">Frontend demo authentication. Connect your backend to enable real login.</p>
      </div>

      <div className="login-footer">
        <div>SatQuery AI · SIH26167 · Smart India Hackathon 2026</div>
        <div className="cyberpod-notice">Secured by CyberPod Shield</div>
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
  const [authenticated, setAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState('');

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
  function login({ email }) {
    setUserEmail(email);
    setAuthenticated(true);
  }

  function logout() {
    setAuthenticated(false);
    setUserEmail('');
    setConversations([]);
    setActiveConvId(null);
    setWelcomeFiles([]);
  }

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

    // Ensure we have an active conversation
    let convId = activeConvId;
    if (!convId) {
      const conv = makeConversation(
        content.length > 50 ? content.slice(0, 47) + '…' : content || 'New analysis'
      );
      setConversations(prev => [conv, ...prev]);
      setActiveConvId(conv.id);
      convId = conv.id;

      // Give React a tick to set state before proceeding
      await new Promise(r => setTimeout(r, 0));
    }

    const allFiles = [...attachedFiles];

    // Auto-title conversation from first message
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

    // Add user message
    const userMsg = makeUserMessage(content, allFiles);
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: [...c.messages, userMsg] } : c)
    );

    // Add loading placeholder for AI response
    const aiMsg = makeAssistantMessage();
    setConversations(prev =>
      prev.map(c => c.id === convId ? { ...c, messages: [...c.messages, aiMsg] } : c)
    );

    setIsLoading(true);

    try {
      // Upload files (demo mode returns mock IDs instantly)
      const imageIds = [];
      for (const f of allFiles) {
        const result = await uploadImage(f.file || f);
        if (result?.image_id) imageIds.push(result.image_id);
      }

      // Query
      const analysis = await sendQuery({
        conversationId: convId,
        query: content,
        imageIds,
        hasImages: allFiles.length > 0,
      });

      // Update AI message with response
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
      // Show error in AI message
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

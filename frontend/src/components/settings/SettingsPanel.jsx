import React, { useEffect, useRef, useState } from 'react';
import {
  X, Sun, Moon, Info, ChevronDown, UserRound, Palette, Gauge,
  Activity, Database, Settings2, Trash2, Check, BarChart3, ShieldCheck,
  KeyRound, Mail, LogOut, Smartphone
} from 'lucide-react';

const NAV = [
  { id: 'general', label: 'General', icon: Settings2 },
  { id: 'account', label: 'Account', icon: UserRound },
  { id: 'personalization', label: 'Personalization', icon: Palette },
  { id: 'storage', label: 'Storage', icon: Database },
  { id: 'usage', label: 'Usage', icon: Gauge },
  { id: 'activity', label: 'Product activity', icon: Activity },
  { id: 'security', label: 'Security and login', icon: ShieldCheck },
];

const ACCENT_OPTIONS = [
  { name: 'Default', value: '#6366f1' },
  { name: 'Gray', value: '#6b7280' },
  { name: 'Green', value: '#10a37f' },
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Purple', value: '#8b5cf6' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Orange', value: '#f59e0b' },
];

function SelectRow({ icon, value, onChange, options, label }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const selected = options.find(o => o.value === value) || options[0];

  useEffect(() => {
    const handleOutside = event => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  return (
    <div className={`settings-select-wrap ${open ? 'open' : ''}`} ref={ref}>
      <button
        type="button"
        className="settings-select-row"
        onClick={() => setOpen(v => !v)}
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {icon && <div className="settings-row-icon">{icon}</div>}
        <span className="settings-select-value">{selected.label}</span>
        <ChevronDown size={15} className="settings-select-chevron" />
      </button>
      {open && options.length > 1 && (
        <div className="settings-select-menu" role="listbox" aria-label={label}>
          {options.map(o => (
            <button
              type="button"
              role="option"
              aria-selected={o.value === value}
              className={`settings-select-option ${o.value === value ? 'selected' : ''}`}
              key={o.value}
              onClick={() => { onChange(o.value); setOpen(false); }}
            >
              <span>{o.label}</span>
              {o.value === value && <Check size={15} />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function General({ theme, setTheme, accent, setAccent, contrast, setContrast }) {
  return <>
    <section className="settings-section">
      <div className="settings-section-title">Appearance</div>
      <SelectRow
        icon={theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
        value={theme}
        onChange={setTheme}
        label="Appearance"
        options={[{ value: 'light', label: 'Light' }, { value: 'dark', label: 'Dark' }]}
      />
      <p className="settings-help">Choose how SatQuery AI looks across your device.</p>
    </section>

    <section className="settings-section">
      <div className="settings-section-title">Contrast</div>
      <SelectRow
        value={contrast}
        onChange={setContrast}
        label="Contrast"
        options={[{ value: 'standard', label: 'Standard' }, { value: 'high', label: 'High contrast' }]}
      />
    </section>

    <section className="settings-section">
      <div className="settings-section-title">Accent color</div>
      <SelectRow
        value={accent}
        onChange={setAccent}
        label="Accent color"
        options={ACCENT_OPTIONS.map(item => ({ value: item.value, label: item.name }))}
      />
      <p className="settings-help">Personalize buttons, highlights and interactive elements.</p>
    </section>
  </>;
}

function Account({ userEmail }) {
  const [deleted, setDeleted] = useState(false);
  if (deleted) return <div className="settings-success"><Check size={18} /><div><strong>Account deletion requested</strong><p>Your local account data has been marked for deletion.</p></div></div>;
  const email = userEmail || 'user@example.com';
  return <section className="settings-section">
    <div className="account-card">
      <div className="account-avatar"><UserRound size={20} /></div>
      <div className="account-details">
        <div><span>Name</span><strong>SatQuery User</strong></div>
        <div><span>Username</span><strong>@satquery_user</strong></div>
        <div><span>Email</span><strong>{email}</strong></div>
      </div>
    </div>
    <div className="danger-card">
      <div><strong>Delete account</strong><p>Permanently remove your account and associated data.</p></div>
      <button className="danger-btn" onClick={() => { if (window.confirm('Delete this account? This action cannot be undone.')) setDeleted(true); }}><Trash2 size={14} /> Delete</button>
    </div>
  </section>;
}

function Personalization() {
  const [baseStyle, setBaseStyle] = useState('default');
  const [warm, setWarm] = useState('default');
  const [enthusiastic, setEnthusiastic] = useState('default');
  const [headers, setHeaders] = useState('default');
  const [emoji, setEmoji] = useState('default');

  const defaultOptions = [{ value: 'default', label: 'Default' }];
  const characteristicOptions = [
    { value: 'more', label: 'More' },
    { value: 'default', label: 'Default' },
    { value: 'less', label: 'Less' },
  ];

  return <>
    <section className="settings-section personalization-settings">
      <div className="personalization-row personalization-main-row">
        <div className="personalization-copy">
          <div className="personalization-label">Base style and tone</div>
          <p>Set the style and tone of how SatQuery AI responds to you.</p>
          <span>This doesn't impact SatQuery AI's capabilities.</span>
        </div>
        <SelectRow value={baseStyle} onChange={setBaseStyle} label="Base style and tone" options={defaultOptions} />
      </div>
    </section>

    <section className="settings-section personalization-settings">
      <div className="personalization-characteristics">
        <div className="personalization-label">Characteristics</div>
        <p>Choose additional customizations on top of your base style and tone.</p>
      </div>

      <div className="personalization-option-row">
        <span>Warm</span>
        <SelectRow value={warm} onChange={setWarm} label="Warm" options={characteristicOptions} />
      </div>
      <div className="personalization-option-row">
        <span>Enthusiastic</span>
        <SelectRow value={enthusiastic} onChange={setEnthusiastic} label="Enthusiastic" options={characteristicOptions} />
      </div>
      <div className="personalization-option-row">
        <span>Headers &amp; Lists</span>
        <SelectRow value={headers} onChange={setHeaders} label="Headers and Lists" options={characteristicOptions} />
      </div>
      <div className="personalization-option-row">
        <span>Emoji</span>
        <SelectRow value={emoji} onChange={setEmoji} label="Emoji" options={characteristicOptions} />
      </div>
    </section>
  </>;
}

function Storage() {
  return <>
    <section className="settings-section">
      <div className="storage-summary"><div><strong>1.8 GB</strong><span> of 5 GB used</span></div><span>36%</span></div>
      <div className="storage-track"><div style={{ width: '36%' }} /></div>
    </section>
    <section className="settings-section">
      <div className="settings-section-title">Storage breakdown</div>
      {[['Files', '1.1 GB', '61%'], ['Images', '0.7 GB', '39%']].map(([name, size, pct]) => <div className="storage-row" key={name}>
        <div><span className="storage-dot" /> <strong>{name}</strong></div><span>{size} <small>{pct}</small></span>
      </div>)}
    </section>
  </>;
}

function Usage() {
  return <>
    <section className="settings-section">
      <div className="usage-plan"><div><span className="plan-label">Current plan</span><strong>SatQuery Free</strong></div><span className="plan-pill">Free</span></div>
    </section>
    <section className="settings-section">
      <div className="settings-section-title">Monthly usage</div>
      <div className="usage-card"><div className="usage-line"><strong>18 / 50 analyses</strong><span>36% used</span></div><div className="usage-track"><div style={{ width: '36%' }} /></div><p>Resets on the 1st of every month.</p></div>
    </section>
    <section className="settings-section">
      <div className="limit-row"><span>Image analyses</span><strong>18 / 50</strong></div>
      <div className="limit-row"><span>AI conversations</span><strong>124 / 500</strong></div>
    </section>
  </>;
}

function ProductActivity({ conversations }) {
  const hasActivity = conversations.some(c => c.messages.some(m => m.role === 'user'));

  if (!hasActivity) {
    return (
      <section className="settings-section">
        <div className="activity-empty-space" aria-label="No product activity yet" />
      </section>
    );
  }

  const userMessages = conversations.flatMap(c => c.messages.filter(m => m.role === 'user'));
  const visionCount = userMessages.filter(m => (m.uploadedFiles || []).length > 0).length;
  const textCount = userMessages.length - visionCount;
  const total = Math.max(userMessages.length, 1);
  const models = [
    { name: 'SatQuery Vision', value: Math.round((visionCount / total) * 100) },
    { name: 'SatQuery AI', value: Math.round((textCount / total) * 100) },
  ].filter(v => v.value > 0);

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const counts = dayNames.map(day => ({ day, value: userMessages.filter(m => dayNames[new Date(m.timestamp).getDay()] === day).length }));
  const max = Math.max(...counts.map(x => x.value), 1);

  return <>
    <section className="settings-section">
      <div className="activity-heading"><div><div className="settings-section-title">Model usage</div><h3>AI model activity</h3></div><span className="activity-period">Your activity</span></div>
      <div className="activity-bars">
        {models.map(v => <div className="activity-model" key={v.name}><div className="activity-bar"><div style={{ height: `${Math.max(v.value, 6)}%` }} /></div><div><strong>{v.value}%</strong><span>{v.name}</span></div></div>)}
      </div>
    </section>
    <section className="settings-section">
      <div className="activity-heading"><div><div className="settings-section-title">Usage over time</div><h3>Queries by day</h3></div></div>
      <div className="activity-line-chart" aria-label="Queries by day chart">
        <div className="chart-grid">{[0,1,2,3].map(i => <i key={i} />)}</div>
        <svg viewBox="0 0 320 130" preserveAspectRatio="none"><polyline points={counts.map((t, i) => `${(i / 6) * 320},${120 - (t.value / max) * 90}`).join(' ')} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
        <div className="chart-labels">{counts.map(t => <span key={t.day}>{t.day}</span>)}</div>
      </div>
    </section>
  </>;
}

function Security({ userEmail }) {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [loggedOut, setLoggedOut] = useState(false);

  const submitPassword = event => {
    event.preventDefault();
    if (newPassword.length < 8) {
      setPasswordMessage('Your new password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMessage('New passwords do not match.');
      return;
    }
    setPasswordMessage('Password updated successfully.');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  return <>
    <section className="settings-section security-settings">
      <div className="security-block">
        <div className="security-item">
          <div className="security-icon"><Mail size={17} /></div>
          <div className="security-copy"><strong>Email</strong><span>{userEmail || 'user@example.com'}</span></div>
          <span className="security-status">Verified</span>
        </div>
        <div className="security-item">
          <div className="security-icon"><KeyRound size={17} /></div>
          <div className="security-copy"><strong>Password</strong><span>••••••••••••</span></div>
          <button className="security-action" onClick={() => { setShowPasswordForm(v => !v); setPasswordMessage(''); }}>Change</button>
        </div>
      </div>
    </section>

    {showPasswordForm && <section className="settings-section">
      <form className="password-form" onSubmit={submitPassword}>
        <div className="settings-section-title">Change password</div>
        <label>Current password<input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required /></label>
        <label>New password<input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} minLength={8} required /></label>
        <label>Confirm new password<input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} minLength={8} required /></label>
        {passwordMessage && <p className={`security-message ${passwordMessage.includes('successfully') ? 'success' : 'error'}`}>{passwordMessage}</p>}
        <div className="password-form-actions"><button type="button" className="security-secondary" onClick={() => setShowPasswordForm(false)}>Cancel</button><button type="submit" className="security-primary">Update password</button></div>
      </form>
    </section>}

    <section className="settings-section security-settings">
      <div className="security-section-heading"><div className="settings-section-title">Sessions</div></div>
      <div className="security-item">
        <div className="security-icon"><Smartphone size={17} /></div>
        <div className="security-copy"><strong>Active sessions</strong><span>This device · Current session</span></div>
        <span className="security-status">Active</span>
      </div>
      <div className="security-signout">
        <div><strong>Log out of all devices</strong><p>Sign out everywhere except this device. You can sign in again anytime.</p></div>
        <button className="security-action" onClick={() => setLoggedOut(true)}><LogOut size={14} /> Log out</button>
      </div>
      {loggedOut && <p className="security-message success">Other active sessions have been signed out.</p>}
    </section>
  </>;
}


export default function SettingsPanel({ theme, setTheme, accent, setAccent, contrast, setContrast, userEmail, conversations = [], onClose }) {
  const [active, setActive] = useState('general');
  const pages = {
    general: <General {...{ theme, setTheme, accent, setAccent, contrast, setContrast }} />,
    account: <Account userEmail={userEmail} />,
    personalization: <Personalization />,
    storage: <Storage />,
    usage: <Usage />,
    activity: <ProductActivity conversations={conversations} />,
    security: <Security userEmail={userEmail} />,
  };
  return <div className="settings-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Settings">
    <div className="settings-panel settings-panel-chatgpt" onClick={e => e.stopPropagation()}>
      <div className="settings-header"><h2 className="settings-title">Settings</h2><button className="settings-close-btn" onClick={onClose} aria-label="Close settings"><X size={18} /></button></div>
      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Settings sections">
          {NAV.map(({ id, label, icon: Icon }) => <button key={id} className={`settings-nav-item ${active === id ? 'active' : ''}`} onClick={() => setActive(id)}><Icon size={15} /><span>{label}</span></button>)}
        </nav>
        <main className="settings-content"><div className="settings-page-title"><h1>{NAV.find(n => n.id === active)?.label}</h1>{active === 'activity' && <BarChart3 size={18} />}</div>{pages[active]}</main>
      </div>
      <div className="settings-footer"><button className="settings-done-btn" onClick={onClose}>Done</button></div>
    </div>
  </div>;
}

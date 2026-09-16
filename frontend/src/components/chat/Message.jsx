import React, { useState } from 'react';
import { Copy, RefreshCw, ThumbsUp, ThumbsDown, Check, AlertCircle, RotateCcw } from 'lucide-react';
import { formatTimestamp } from '../../utils/fileUtils';
import FileCard from '../image/FileCard';
import AnalysisResult from '../results/AnalysisResult';

/**
 * Single chat message — supports user and assistant roles.
 *
 * User message: right-aligned bubble.
 * Assistant message: full-width with subtle avatar, clean prose.
 * Both show timestamps, copy, and feedback controls.
 */
export default function Message({ message, onRegenerate, onCopy }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'up' | 'down' | null

  const { id, role, content, uploadedFiles, activeFile, analysis, timestamp, isLoading, error } = message;
  const isUser = role === 'user';

  function handleCopy() {
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
    onCopy?.(id);
  }

    function handleFeedback(type) {
    if (feedback === type) return;
    setFeedback(type);
    
    // Simulate API feedback submission
    const toast = document.createElement('div');
    toast.textContent = type === 'up' ? 'Feedback submitted! Thanks.' : 'Feedback logged. We will improve.';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.background = 'var(--text)';
    toast.style.color = 'var(--bg)';
    toast.style.padding = '8px 16px';
    toast.style.borderRadius = '20px';
    toast.style.fontSize = '12px';
    toast.style.fontWeight = '500';
    toast.style.zIndex = '9999';
    toast.style.transition = 'opacity 0.3s';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
  }

  // ── User message ────────────────────────────────────────────────────────────
  if (isUser) {
    return (
      <div className="msg msg-user">
        <div className="msg-user-bubble">
          {/* Attached files */}
          {uploadedFiles?.length > 0 && (
            <div className="msg-user-files">
              {uploadedFiles.map(f => (
                <FileCard key={f.id} uploadedFile={f} onRemove={null} compact />
              ))}
            </div>
          )}
          {/* Text */}
          {content && <div className="msg-user-text">{content}</div>}
          {/* Timestamp */}
          {timestamp && <div className="msg-timestamp">{formatTimestamp(timestamp)}</div>}
        </div>
      </div>
    );
  }

  // ── Assistant message ───────────────────────────────────────────────────────
  return (
    <div className="msg msg-assistant">
      {/* Avatar */}
      <div className="msg-ai-avatar" aria-hidden="true">
        <span>S</span>
      </div>

      <div className="msg-ai-body">
        {/* Loading state */}
        {isLoading && (
          <div className="msg-loading">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="msg-loading-label">Analyzing…</span>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="msg-error">
            <AlertCircle size={15} />
            <span>{error}</span>
            {onRegenerate && (
              <button className="msg-retry-btn" onClick={() => onRegenerate(id)}>
                <RotateCcw size={13} /> Retry
              </button>
            )}
          </div>
        )}

        {/* Answer text */}
        {content && !isLoading && (
          <div className="msg-ai-text">{content}</div>
        )}

        {/* Analysis result */}
        {analysis && !isLoading && (
          <AnalysisResult analysis={analysis} uploadedFiles={uploadedFiles} activeFile={activeFile} />
        )}

        {/* Timestamp */}
        {timestamp && !isLoading && (
          <div className="msg-timestamp">{formatTimestamp(timestamp)}</div>
        )}

        {/* Action toolbar */}
        {!isLoading && !error && content && (
          <div className="msg-actions" role="toolbar" aria-label="Message actions">
            <button
              className="msg-action-btn"
              onClick={handleCopy}
              title={copied ? 'Copied' : 'Copy response'}
              aria-label="Copy response"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            {onRegenerate && (
              <button
                className="msg-action-btn"
                onClick={() => onRegenerate(id)}
                title="Regenerate response"
                aria-label="Regenerate"
              >
                <RefreshCw size={13} />
                <span>Regenerate</span>
              </button>
            )}

            <div className="msg-feedback">
              <button
                className={`msg-feedback-btn ${feedback === 'up' ? 'active' : ''}`}
                onClick={() => handleFeedback('up')}
                title="Good response"
                aria-label="Good response"
              >
                <ThumbsUp size={13} />
              </button>
              <button
                className={`msg-feedback-btn ${feedback === 'down' ? 'active' : ''}`}
                onClick={() => handleFeedback('down')}
                title="Poor response"
                aria-label="Poor response"
              >
                <ThumbsDown size={13} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Square, Paperclip, X, Mic, MicOff } from 'lucide-react';
import { validateFile, generateId, canPreviewInBrowser } from '../../utils/fileUtils';
import FileCard from '../image/FileCard';

/**
 * ChatGPT-style composer / chat input.
 *
 * Supports:
 * - Natural language text
 * - Multi-image attach (click or drag-drop on composer)
 * - Paste image from clipboard
 * - Enter to send, Shift+Enter for newline
 * - Stop generation (when streaming)
 * - Disabled while processing
 * - Auto-resize textarea
 * - Voice Assistant typing
 */
export default function Composer({ onSend, loading, onStop, disabled }) {
  const [text, setText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [fileErrors, setFileErrors] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef();
  const fileInputRef = useRef();
  const recognitionRef = useRef(null);

  // Initialize SpeechRecognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        
        recognitionRef.current.onresult = (event) => {
          let interimTranscript = '';
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }
          if (finalTranscript) {
            setText(prev => prev + (prev.endsWith(' ') ? '' : ' ') + finalTranscript);
          }
        };

        recognitionRef.current.onerror = (event) => {
          console.error('Speech recognition error', event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  const toggleMic = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [text]);

  // Paste image
  useEffect(() => {
    function handlePaste(e) {
      const items = e.clipboardData?.items;
      if (!items) return;
      const imageItems = Array.from(items).filter(i => i.type.startsWith('image/'));
      if (imageItems.length === 0) return;
      const files = imageItems.map(i => i.getAsFile()).filter(Boolean);
      addFiles(files);
    }
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, [attachedFiles]);

  const addFiles = useCallback((rawFiles) => {
    const errors = [];
    const valid = [];
    Array.from(rawFiles).forEach(file => {
      const { valid: ok, error } = validateFile(file);
      if (ok) {
        if (attachedFiles.length + valid.length >= 4) {
          errors.push('Maximum 4 files per message.');
          return;
        }
        valid.push({
          id: generateId(),
          file,
          name: file.name,
          url: canPreviewInBrowser(file) ? URL.createObjectURL(file) : null,
          status: 'ready',
          error: null,
          metadata: null,
          uploadProgress: 0,
        });
      } else {
        errors.push(`${file.name}: ${error}`);
      }
    });
    setFileErrors(errors);
    if (valid.length > 0) setAttachedFiles(prev => [...prev, ...valid]);
  }, [attachedFiles]);

  function removeFile(id) {
    setAttachedFiles(prev => {
      const f = prev.find(f => f.id === id);
      if (f?.url) URL.revokeObjectURL(f.url);
      return prev.filter(f => f.id !== id);
    });
  }

  function canSend() {
    return !loading && !disabled && (text.trim().length > 0 || attachedFiles.length > 0);
  }

  function send() {
    if (!canSend()) return;
    const query = text.trim();
    const files = [...attachedFiles];
    setText('');
    setAttachedFiles([]);
    setFileErrors([]);
    onSend(query, files);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  // Drag-drop on composer
  function onDragOver(e) { e.preventDefault(); setIsDragging(true); }
  function onDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) setIsDragging(false);
  }
  function onDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  }

  return (
    <div className="composer-outer">
      {/* File errors */}
      {fileErrors.length > 0 && (
        <div className="composer-file-errors">
          {fileErrors.map((err, i) => (
            <div key={i} className="composer-file-error">
              <X size={11} /> {err}
            </div>
          ))}
          <button onClick={() => setFileErrors([])} className="composer-errors-dismiss">Dismiss</button>
        </div>
      )}

      {/* Attached file chips */}
      {attachedFiles.length > 0 && (
        <div className="composer-files">
          {attachedFiles.map(f => (
            <FileCard key={f.id} uploadedFile={f} onRemove={() => removeFile(f.id)} compact />
          ))}
        </div>
      )}

      {/* Input box */}
      <div
        className={`composer-box ${isDragging ? 'composer-dragging' : ''} ${disabled || loading ? 'composer-disabled' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        {/* Attach button */}
        <button
          className="composer-attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || loading || attachedFiles.length >= 4}
          title="Attach satellite image"
          aria-label="Attach image"
        >
          <Paperclip size={18} />
        </button>

        <input
          ref={fileInputRef}
          type="file"
          hidden
          multiple
          accept=".tif,.tiff,.png,.jpg,.jpeg,image/tiff,image/png,image/jpeg"
          onChange={e => { if (e.target.files?.length) addFiles(e.target.files); e.target.value = ''; }}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          className="composer-textarea"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening 
              ? 'Listening...'
              : attachedFiles.length > 0
                ? 'Ask a question about your imagery…'
                : 'Ask SatQuery AI about satellite imagery…'
          }
          disabled={disabled || loading}
          rows={1}
          aria-label="Message input"
        />

        {/* Mic button */}
        {!loading && (
          <button
            className={`composer-mic-btn ${isListening ? 'active' : ''}`}
            onClick={toggleMic}
            disabled={disabled}
            title={isListening ? 'Stop recording' : 'Voice typing'}
            aria-label="Voice typing"
          >
            {isListening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        )}

        {/* Send / Stop button */}
        {loading ? (
          <button
            className="composer-stop-btn"
            onClick={onStop}
            title="Stop generation"
            aria-label="Stop generation"
          >
            <Square size={16} fill="currentColor" />
          </button>
        ) : (
          <button
            className={`composer-send-btn ${canSend() ? 'active' : ''}`}
            onClick={send}
            disabled={!canSend()}
            title="Send message"
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        )}
      </div>

      {/* Hint */}
      <div className="composer-hint">
        Enter to send · Shift+Enter for new line · Drag &amp; drop images supported
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, Cpu, Layers, CheckCircle, AlertCircle } from 'lucide-react';

/**
 * Expandable execution summary panel.
 * Shows only observable information — no internal chain-of-thought.
 * Hidden if no execution data is available.
 */
export default function ExecutionSummary({ execution }) {
  const [open, setOpen] = useState(false);

  if (!execution) return null;

  const { taskDetected, tools, inputType, status, durationMs, outputType } = execution;

  const statusIcon = status === 'completed'
    ? <CheckCircle size={13} className="exec-status-icon success" />
    : <AlertCircle size={13} className="exec-status-icon warning" />;

  return (
    <div className="exec-summary">
      <button className="exec-summary-toggle" onClick={() => setOpen(v => !v)}>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>Analysis details</span>
        {statusIcon}
        {durationMs && <span className="exec-duration">{(durationMs / 1000).toFixed(1)}s</span>}
      </button>

      {open && (
        <div className="exec-summary-body">
          <div className="exec-row">
            <span className="exec-label"><Layers size={12} /> Task detected</span>
            <span className="exec-value">{taskDetected || 'Not specified'}</span>
          </div>

          {tools?.length > 0 && (
            <div className="exec-row">
              <span className="exec-label"><Cpu size={12} /> Models / tools</span>
              <span className="exec-value">{tools.join(', ')}</span>
            </div>
          )}

          {inputType && (
            <div className="exec-row">
              <span className="exec-label">Input type</span>
              <span className="exec-value">{inputType}</span>
            </div>
          )}

          {outputType && (
            <div className="exec-row">
              <span className="exec-label">Output type</span>
              <span className="exec-value">{outputType}</span>
            </div>
          )}

          <div className="exec-row">
            <span className="exec-label"><CheckCircle size={12} /> Status</span>
            <span className={`exec-value exec-status-text ${status}`}>
              {status === 'completed' ? 'Completed' : status}
            </span>
          </div>

          {durationMs && (
            <div className="exec-row">
              <span className="exec-label"><Clock size={12} /> Duration</span>
              <span className="exec-value">{(durationMs / 1000).toFixed(2)} s</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { AlertTriangle } from 'lucide-react';

/**
 * Confidence badge component.
 * Only renders when confidence is a valid number.
 * Never renders a fake value.
 */
export default function ConfidenceBadge({ confidence }) {
  if (confidence == null || typeof confidence !== 'number') return null;

  const pct = Math.round(confidence * 100);

  let level = 'high';
  let label = null;
  if (pct < 60) {
    level = 'low';
    label = 'Low confidence — additional imagery may improve accuracy.';
  } else if (pct < 80) {
    level = 'medium';
  }

  return (
    <div className={`confidence-badge confidence-${level}`}>
      <div className="confidence-bar-wrap">
        <div className="confidence-bar" style={{ width: `${pct}%` }} />
      </div>
      <span className="confidence-value">{pct}% confidence</span>
      {level === 'low' && (
        <span className="confidence-warning">
          <AlertTriangle size={12} />
          {label}
        </span>
      )}
    </div>
  );
}

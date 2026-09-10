import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import ConfidenceBadge from '../results/ConfidenceBadge';
import ExecutionSummary from '../results/ExecutionSummary';
import SatelliteViewer from '../../SatelliteViewer';

export default function AnalysisResult({ analysis, uploadedFiles }) {
  const [showViewer, setShowViewer] = useState(false);

  if (!analysis) return null;

  const { answer, taskLabel, confidence, regions, changes, execution } = analysis;
  const primaryFile = uploadedFiles?.[0];
  const hasVisualOutput = regions?.length > 0 || changes?.length > 0;

  return (
    <div className="analysis-result-wrap">
      {taskLabel && <div className="result-task-label">{taskLabel}</div>}

      <div className="result-answer">{answer}</div>

      <ConfidenceBadge confidence={confidence} />

      <ExecutionSummary execution={execution} />

      {primaryFile && (
        <div className="result-viewer-section">
          <button className="result-viewer-toggle" onClick={() => setShowViewer(v => !v)}>
            {showViewer ? <EyeOff size={14} /> : <Eye size={14} />}
            {showViewer ? 'Hide image viewer' : 'Show image viewer'}
          </button>
          {showViewer && <SatelliteViewer file={primaryFile} regions={regions} changes={changes} />}
        </div>
      )}

      {hasVisualOutput && (
        <div className="result-regions-summary">
          {regions?.length > 0 && (
            <div className="result-regions">
              <div className="result-regions-title">Detected regions</div>
              {regions.map(r => (
                <div key={r.id} className="result-region-item">
                  <span className="region-dot" />
                  <span>{r.label}</span>
                </div>
              ))}
            </div>
          )}
          {changes?.length > 0 && (
            <div className="result-changes">
              <div className="result-regions-title">Detected changes</div>
              {changes.map(c => (
                <div key={c.id} className={`result-change-item change-${c.type}`}>
                  <span className={`change-dot ${c.type}`} />
                  <span>{c.label}</span>
                  <span className="change-type-badge">{c.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

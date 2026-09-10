import React, { useState } from 'react';
import { X, File, AlertTriangle, CheckCircle, Loader } from 'lucide-react';
import { formatFileSize, getFormatLabel, isGeospatialFormat, canPreviewInBrowser } from '../../utils/fileUtils';

/**
 * File card for a single uploaded file.
 * Shows name, size, format, status, and optional preview thumbnail.
 * Metadata is only shown when supplied by the backend — never invented.
 */
export default function FileCard({ uploadedFile, onRemove, compact = false }) {
  const [showMeta, setShowMeta] = useState(false);
  const { file, name, url, status, error, metadata, uploadProgress } = uploadedFile;

  const canPreview = url && canPreviewInBrowser({ name });
  const isGeo = isGeospatialFormat({ name });
  const formatLabel = getFormatLabel({ name });

  const statusIcon = {
    uploading: <Loader size={13} className="file-status-icon uploading" />,
    ready: <CheckCircle size={13} className="file-status-icon ready" />,
    error: <AlertTriangle size={13} className="file-status-icon error" />,
  }[status] || null;

  if (compact) {
    return (
      <div className={`file-chip-inline ${status === 'error' ? 'file-chip-error' : ''}`}>
        {canPreview
          ? <img src={url} alt={name} className="file-chip-thumb" />
          : <div className="file-chip-thumb file-chip-geo"><span>🛰</span></div>
        }
        <span className="file-chip-name">{name}</span>
        {statusIcon}
        <button className="file-chip-remove" onClick={onRemove} title="Remove file">
          <X size={12} />
        </button>
      </div>
    );
  }

  return (
    <div className={`file-card ${status === 'error' ? 'file-card-error' : ''}`}>
      {/* Preview */}
      <div className="file-card-thumb">
        {canPreview
          ? <img src={url} alt={name} />
          : (
            <div className="file-card-thumb-placeholder">
              <span className="file-geo-icon">🛰</span>
              <small>{formatLabel}</small>
            </div>
          )
        }
      </div>

      {/* Info */}
      <div className="file-card-info">
        <div className="file-card-name">{name}</div>
        <div className="file-card-meta-row">
          <span className={`file-format-badge ${isGeo ? 'geo' : 'standard'}`}>{formatLabel}</span>
          {isGeo && <span className="file-geo-note">Geospatial</span>}
          <span className="file-size">{formatFileSize(file?.size)}</span>
          {statusIcon}
        </div>

        {/* Upload progress */}
        {status === 'uploading' && (
          <div className="file-progress-wrap">
            <div className="file-progress-bar" style={{ width: `${uploadProgress || 0}%` }} />
            <span>{uploadProgress || 0}%</span>
          </div>
        )}

        {/* Error */}
        {status === 'error' && error && (
          <div className="file-error-msg">{error}</div>
        )}

        {/* Metadata (only from backend, never invented) */}
        {metadata && (
          <button className="file-meta-toggle" onClick={() => setShowMeta(v => !v)}>
            {showMeta ? 'Hide metadata' : 'Show metadata'}
          </button>
        )}
        {showMeta && metadata && (
          <div className="file-metadata">
            {[
              ['CRS', metadata.crs],
              ['Resolution', metadata.resolution],
              ['Dimensions', metadata.dimensions],
              ['Bounding box', metadata.bbox],
              ['Acquisition date', metadata.acquisition_date],
              ['Sensor / modality', metadata.sensor],
              ['Bands', metadata.bands],
            ].map(([label, val]) => val ? (
              <div key={label} className="file-meta-row">
                <span className="file-meta-label">{label}</span>
                <span className="file-meta-value">{val}</span>
              </div>
            ) : null)}
          </div>
        )}

        {!isGeo && (
          <div className="file-standard-note">
            PNG/JPEG accepted for benchmarking and demo. GeoTIFF is the primary geospatial format.
          </div>
        )}
      </div>

      {/* Remove button */}
      <button className="file-card-remove" onClick={onRemove} title="Remove file">
        <X size={15} />
      </button>
    </div>
  );
}

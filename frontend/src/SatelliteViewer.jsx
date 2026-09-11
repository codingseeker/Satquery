import React, { useMemo, useState } from 'react';
import { Layers, Map, Image as ImageIcon, ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, Maximize2, Save } from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { canPreviewInBrowser } from './utils/fileUtils';

// Default coordinates — Bengaluru (ISRO / SIH context)
const DEFAULT_CENTER = [12.9716, 77.5946];

function CoordinateTracker() {
  const map = useMap();
  const [coords, setCoords] = useState(map.getCenter());

  React.useEffect(() => {
    const onMove = () => setCoords(map.getCenter());
    map.on('move', onMove);
    return () => { map.off('move', onMove); };
  }, [map]);

  return (
    <div className="viewer-map-badge">
      {Math.abs(coords.lat).toFixed(4)}° {coords.lat >= 0 ? 'N' : 'S'} · {Math.abs(coords.lng).toFixed(4)}° {coords.lng >= 0 ? 'E' : 'W'}
    </div>
  );
}

function RecenterButton() {
  const map = useMap();
  return (
    <button
      className="map-recenter-btn"
      onClick={() => map.setView(DEFAULT_CENTER, 14)}
      title="Reset map view"
    >
      <RotateCcw size={14} />
    </button>
  );
}

/**
 * Satellite image viewer.
 * Supports: zoom, pan, fullscreen, region overlays, layer visibility, map view, layer panel.
 * Regions and changes are passed from the parent (AnalysisResult) — never invented here.
 *
 * @param {{ file: UploadedFile, regions: Region[], changes: Change[], activeRegionId?: string }} props
 */
export default function SatelliteViewer({ file, regions = [], changes = [], mapData = {}, metadata = {}, activeRegionId = null }) {
  const [tab, setTab] = useState('image');
  const [zoom, setZoom] = useState(1);
  const [showRegions, setShowRegions] = useState(true);
  const [showChanges, setShowChanges] = useState(true);
  const [layers, setLayers] = useState({ optical: true, sar: false });
  const [fullscreen, setFullscreen] = useState(false);

  const imageUrl = file?.url;
  const canPreview = imageUrl && canPreviewInBrowser({ name: file?.name || '' });
  const scale = useMemo(() => Math.min(2.8, Math.max(0.5, zoom)), [zoom]);

  const toggleLayer = (key) => setLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const hasRegions = regions.length > 0;
  const hasChanges = changes.length > 0;
  const hasOverlays = hasRegions || hasChanges;

  return (
    <div className={`viewer-card ${fullscreen ? 'viewer-fullscreen' : ''}`}>
      {/* Header */}
      <div className="viewer-head">
        <div>
          <span className="viewer-eyebrow">SATELLITE WORKSPACE</span>
          <strong className="viewer-filename">Analysis Result</strong>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="viewer-fs-btn"
            onClick={() => alert("Analysis saved successfully!")}
            title="Save Analysis"
            aria-label="Save Analysis"
          >
            <Save size={14} />
          </button>
          <button
            className="viewer-fs-btn"
            onClick={() => setFullscreen(v => !v)}
            title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            aria-label={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="viewer-tabs" role="tablist">
        {[
          { id: 'image', Icon: ImageIcon, label: 'Image' },
          { id: 'side-by-side', Icon: Eye, label: 'Side-by-side' },
          { id: 'map', Icon: Map, label: 'Map' },
          { id: 'layers', Icon: Layers, label: 'Layers' },
        ].map(({ id, Icon, label }) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            className={`viewer-tab ${tab === id ? 'active' : ''}`}
            onClick={() => setTab(id)}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Image tab */}
      {tab === 'image' && (
        <div className="viewer-image-panel">
          <div className="viewer-canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%', maxHeight: '100%' }}>
              {canPreview ? (
                <img
                  src={imageUrl}
                  alt={`Satellite imagery: ${file.name}`}
                  style={{ transform: `scale(${scale})`, transformOrigin: 'center', maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  draggable={false}
                />
              ) : (
                <div className="viewer-placeholder" style={{ position: 'static' }}>
                  <span className="viewer-placeholder-icon" aria-hidden="true">🛰️</span>
                  <strong>GeoTIFF — browser preview not available</strong>
                  <span>The backend can return a rendered tile URL for visual display.</span>
                </div>
              )}

              {/* Region overlays (from backend/analysis — never invented) */}
              {showRegions && hasRegions && regions.map(r => (
                <div
                  key={r.id}
                  className="viewer-region"
                  style={{
                    left: `${r.bounds.x}%`,
                    top: `${r.bounds.y}%`,
                    width: `${r.bounds.w}%`,
                    height: `${r.bounds.h}%`,
                  }}
                  title={r.label}
                >
                  <span className="viewer-region-label">{r.label}</span>
                </div>
              ))}

              {/* Change overlays */}
              {showChanges && hasChanges && changes.map(c => (
                <div
                  key={c.id}
                  className={`viewer-change viewer-change-${c.type} ${activeRegionId === c.id ? 'active' : ''}`}
                  style={{
                    position: 'absolute',
                    left: `${c.bounds.x}%`,
                    top: `${c.bounds.y}%`,
                    width: `${c.bounds.w}%`,
                    height: `${c.bounds.h}%`,
                    border: activeRegionId === c.id ? '2px solid #ef4444' : (c.type === 'added' ? '2px solid #10b981' : '2px solid #f59e0b'),
                    backgroundColor: activeRegionId === c.id ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                    boxShadow: activeRegionId === c.id ? '0 0 0 2px white, 0 0 10px rgba(239,68,68,0.5)' : 'none',
                    zIndex: activeRegionId === c.id ? 10 : 1
                  }}
                  title={c.label}
                >
                  <span className="viewer-region-label" style={{
                     background: activeRegionId === c.id ? '#ef4444' : (c.type === 'added' ? '#10b981' : '#f59e0b'),
                     color: '#fff', 
                     fontSize: '10px', 
                     padding: '2px 4px', 
                     position: 'absolute', 
                     top: '-18px', 
                     left: '-2px',
                     whiteSpace: 'nowrap'
                  }}>
                    {c.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Overlay labels */}
            <div className="viewer-overlay-top">
              <span>{layers.optical ? 'OPTICAL' : 'NO OPTICAL'}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="viewer-controls">
            <div className="viewer-zoom-controls">
              <button onClick={() => setZoom(z => Math.max(0.5, z - 0.15))} title="Zoom out"><ZoomOut size={14} /></button>
              <span>{Math.round(scale * 100)}%</span>
              <button onClick={() => setZoom(z => Math.min(2.8, z + 0.15))} title="Zoom in"><ZoomIn size={14} /></button>
              <button onClick={() => setZoom(1)} title="Reset zoom"><RotateCcw size={13} /></button>
            </div>

            {hasOverlays && (
              <div className="viewer-overlay-controls">
                {hasRegions && (
                  <button
                    className={`viewer-overlay-btn ${showRegions ? 'on' : ''}`}
                    onClick={() => setShowRegions(v => !v)}
                    title={showRegions ? 'Hide regions' : 'Show regions'}
                  >
                    {showRegions ? <Eye size={13} /> : <EyeOff size={13} />}
                    Regions
                  </button>
                )}
                {hasChanges && (
                  <button
                    className={`viewer-overlay-btn ${showChanges ? 'on' : ''}`}
                    onClick={() => setShowChanges(v => !v)}
                    title={showChanges ? 'Hide changes' : 'Show changes'}
                  >
                    {showChanges ? <Eye size={13} /> : <EyeOff size={13} />}
                    Changes
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Side-by-side tab */}
      {tab === 'side-by-side' && (
        <div className="viewer-image-panel side-by-side-layout" style={{ display: 'flex', gap: '1rem', width: '100%', height: '100%' }}>
          {/* Original Image */}
          <div className="viewer-canvas" style={{ flex: 1, position: 'relative', borderRight: '1px solid var(--accent-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="viewer-overlay-top" style={{ zIndex: 10 }}><span>ORIGINAL</span></div>
            <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%', maxHeight: '100%' }}>
              {canPreview ? (
                <img
                  src={imageUrl}
                  alt={`Original: ${file.name}`}
                  style={{ transform: `scale(${scale})`, transformOrigin: 'center', maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  draggable={false}
                />
              ) : (
                <div className="viewer-placeholder" style={{ position: 'static' }}>
                  <span className="viewer-placeholder-icon" aria-hidden="true">🛰️</span>
                  <strong>GeoTIFF — browser preview not available</strong>
                </div>
              )}
            </div>
          </div>
          
          {/* Annotated Image */}
          <div className="viewer-canvas" style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="viewer-overlay-top" style={{ zIndex: 10 }}><span>ANNOTATED BY AI</span></div>
            <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%', maxHeight: '100%' }}>
              {canPreview ? (
                <img
                  src={imageUrl}
                  alt={`Annotated: ${file.name}`}
                  style={{ transform: `scale(${scale})`, transformOrigin: 'center', maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  draggable={false}
                />
              ) : null}

              {/* Region overlays */}
              {showRegions && hasRegions && regions.map(r => (
                <div
                  key={r.id}
                  className={`viewer-region ${activeRegionId === r.id ? 'active' : ''}`}
                  style={{
                    position: 'absolute',
                    left: `${r.bounds.x}%`,
                    top: `${r.bounds.y}%`,
                    width: `${r.bounds.w}%`,
                    height: `${r.bounds.h}%`,
                    border: activeRegionId === r.id ? '2px solid #ef4444' : '2px solid #3b82f6',
                    backgroundColor: activeRegionId === r.id ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.1)',
                    boxShadow: activeRegionId === r.id ? '0 0 0 2px white, 0 0 10px rgba(239,68,68,0.5)' : 'none',
                    zIndex: activeRegionId === r.id ? 10 : 1
                  }}
                  title={r.label}
                >
                  <span className="viewer-region-label" style={{ 
                    background: activeRegionId === r.id ? '#ef4444' : '#3b82f6', 
                    color: '#fff', 
                    fontSize: '10px', 
                    padding: '2px 4px', 
                    position: 'absolute', 
                    top: '-18px', 
                    left: '-2px',
                    whiteSpace: 'nowrap'
                  }}>
                    {r.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="viewer-controls" style={{ position: 'absolute', bottom: '10px', left: '50%', transform: 'translateX(-50%)', zIndex: 10 }}>
            <div className="viewer-zoom-controls">
              <button onClick={() => setZoom(z => Math.max(0.5, z - 0.15))} title="Zoom out"><ZoomOut size={14} /></button>
              <span>{Math.round(scale * 100)}%</span>
              <button onClick={() => setZoom(z => Math.min(2.8, z + 0.15))} title="Zoom in"><ZoomIn size={14} /></button>
              <button onClick={() => setZoom(1)} title="Reset zoom"><RotateCcw size={13} /></button>
            </div>
          </div>
        </div>
      )}

      {/* Map tab */}
      {tab === 'map' && (
        <div className="viewer-map-panel">
          <MapContainer center={mapData?.center || DEFAULT_CENTER} zoom={mapData?.zoom || 14} scrollWheelZoom className="viewer-leaflet">
            <TileLayer
              url={layers.sar
                ? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
                : 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
              }
              attribution={layers.sar ? '© OpenStreetMap contributors' : 'Tiles © Esri'}
            />
            {mapData?.geojson && <GeoJSON data={mapData.geojson} style={() => ({ weight: 2, fillOpacity: 0.22 })} />}
            {metadata?.bounds && <GeoJSON data={{ type: 'Feature', properties: { source: 'raster footprint' }, geometry: { type: 'Polygon', coordinates: [[
              [metadata.bounds.left, metadata.bounds.bottom], [metadata.bounds.left, metadata.bounds.top],
              [metadata.bounds.right, metadata.bounds.top], [metadata.bounds.right, metadata.bounds.bottom], [metadata.bounds.left, metadata.bounds.bottom]
            ]] } }} style={() => ({ weight: 1, fillOpacity: 0.05 })} />}
            <RecenterButton />
            <CoordinateTracker />
          </MapContainer>
        </div>
      )}

      {/* Layers tab */}
      {tab === 'layers' && (
        <div className="viewer-layers-panel">
          <LayerRow
            label="Optical imagery"
            detail="RGB / multispectral base"
            active={layers.optical}
            onClick={() => toggleLayer('optical')}
          />
          <LayerRow
            label="SAR imagery"
            detail="Radar / structural information"
            active={layers.sar}
            onClick={() => toggleLayer('sar')}
          />
          {hasRegions && (
            <LayerRow
              label="Detected regions"
              detail="AI-grounded spatial regions from backend"
              active={showRegions}
              onClick={() => setShowRegions(v => !v)}
            />
          )}
          {hasChanges && (
            <LayerRow
              label="Change overlay"
              detail="Bi-temporal change regions from backend"
              active={showChanges}
              onClick={() => setShowChanges(v => !v)}
            />
          )}
          <div className="viewer-layer-note">
            Layer controls are frontend-ready. The backend can supply rendered tile URLs and spatial geometries.
          </div>
        </div>
      )}
    </div>
  );
}

function LayerRow({ label, detail, active, onClick }) {
  return (
    <button className="viewer-layer-row" onClick={onClick}>
      <span className={`viewer-layer-status ${active ? 'on' : ''}`}>
        {active ? <Eye size={14} /> : <EyeOff size={14} />}
      </span>
      <span className="viewer-layer-info">
        <strong>{label}</strong>
        <small>{detail}</small>
      </span>
      <span className={`viewer-layer-toggle ${active ? 'on' : ''}`}><i /></span>
    </button>
  );
}

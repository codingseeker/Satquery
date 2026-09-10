/**
 * File utilities — validation, formatting, type detection.
 * Keep satellite imagery context in mind: large files, geospatial formats.
 */

import config from '../config/env';

// ─── Supported formats ────────────────────────────────────────────────────────

export const GEOSPATIAL_FORMATS = ['.tif', '.tiff', '.geotiff'];
export const STANDARD_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg'];
export const ALL_SUPPORTED_FORMATS = [...GEOSPATIAL_FORMATS, ...STANDARD_IMAGE_FORMATS];

export const ACCEPTED_MIME_TYPES = [
  'image/tiff',
  'image/png',
  'image/jpeg',
  'image/jpg',
  // GeoTIFF uses the same MIME as TIFF
];

// ─── File validation ──────────────────────────────────────────────────────────

/**
 * Validate a File object against supported formats and size limits.
 * @param {File} file
 * @returns {{ valid: boolean, error: string | null }}
 */
export function validateFile(file) {
  if (!file) return { valid: false, error: 'No file provided.' };

  const ext = getExtension(file.name);
  if (!ALL_SUPPORTED_FORMATS.includes(ext)) {
    return {
      valid: false,
      error: `Unsupported format "${ext}". Supported formats: GeoTIFF, TIFF, PNG, JPEG.`,
    };
  }

  if (file.size > config.maxFileSizeBytes) {
    return {
      valid: false,
      error: `File too large (${formatFileSize(file.size)}). Maximum allowed: ${formatFileSize(config.maxFileSizeBytes)}.`,
    };
  }

  if (file.size === 0) {
    return { valid: false, error: 'File appears to be empty.' };
  }

  return { valid: true, error: null };
}

// ─── Type detection ───────────────────────────────────────────────────────────

/** Get lowercase extension including dot, e.g. ".tif" */
export function getExtension(filename) {
  if (!filename) return '';
  const parts = filename.toLowerCase().split('.');
  return parts.length > 1 ? `.${parts.at(-1)}` : '';
}

/** Returns true if file is a geospatial format (GeoTIFF/TIFF) */
export function isGeospatialFormat(file) {
  return GEOSPATIAL_FORMATS.includes(getExtension(file?.name || ''));
}

/** Returns true if browser can render a preview (not TIFF) */
export function canPreviewInBrowser(file) {
  return STANDARD_IMAGE_FORMATS.includes(getExtension(file?.name || ''));
}

/**
 * Get a human-readable format label.
 * @param {File} file
 * @returns {string}
 */
export function getFormatLabel(file) {
  const ext = getExtension(file?.name || '');
  if (['.tif', '.tiff', '.geotiff'].includes(ext)) return 'GeoTIFF';
  if (ext === '.png') return 'PNG';
  if (['.jpg', '.jpeg'].includes(ext)) return 'JPEG';
  return ext.toUpperCase().replace('.', '') || 'Unknown';
}

/**
 * Guess the sensor modality from filename or format.
 * Returns null if uncertain — do not invent values.
 * @param {File} file
 * @returns {'optical' | 'sar' | null}
 */
export function guessSensorModality(file) {
  const name = (file?.name || '').toLowerCase();
  if (name.includes('sar') || name.includes('s1') || name.includes('sentinel-1')) return 'sar';
  if (name.includes('optical') || name.includes('rgb') || name.includes('s2') || name.includes('sentinel-2')) return 'optical';
  return null; // unknown — do not guess further
}

// ─── Formatting ───────────────────────────────────────────────────────────────

/**
 * Format bytes into human-readable size string.
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (bytes == null || isNaN(bytes)) return 'Unknown size';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

/**
 * Format a timestamp Date to a readable time string.
 * @param {Date | string} date
 * @returns {string}
 */
export function formatTimestamp(date) {
  if (!date) return '';
  const d = date instanceof Date ? date : new Date(date);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Generate a short unique ID (not cryptographic).
 * @returns {string}
 */
export function generateId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

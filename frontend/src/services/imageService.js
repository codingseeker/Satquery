/**
 * Image service — upload, metadata retrieval, image processing.
 * All geospatial image handling goes through this module.
 */

import api from './api';
import config from '../config/env';

// ─── Upload ───────────────────────────────────────────────────────────────────

/**
 * Upload a single image file to the backend.
 *
 * @param {File} file
 * @param {function} onProgress   Called with progress 0–100 (if supported)
 * @returns {Promise<{ image_id: string, metadata: object }>}
 */
export async function uploadImage(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  // Note: XMLHttpRequest is used for progress tracking.
  // Falls back to fetch if onProgress is not needed.
  if (typeof onProgress === 'function') {
    return uploadWithProgress(formData, onProgress);
  }

  return api.postFormData('/api/images/upload', formData);
}

/**
 * Upload with progress tracking using XHR.
 * @private
 */
function uploadWithProgress(formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', e => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (_) {
          reject(new Error('Invalid response from upload endpoint.'));
        }
      } else {
        let msg = `Upload failed (${xhr.status})`;
        try {
          const d = JSON.parse(xhr.responseText);
          msg = d.detail || d.message || msg;
        } catch (_) { /* ignore */ }
        reject(new Error(msg));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Upload failed. Please check your connection.')));
    xhr.addEventListener('abort', () => reject(new Error('Upload was cancelled.')));

    xhr.open('POST', `${config.apiBaseUrl}/api/images/upload`);
    
    const token = localStorage.getItem('satquery_token');
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}

// ─── Metadata ─────────────────────────────────────────────────────────────────

/**
 * Retrieve image metadata from the backend.
 * Returns null if metadata is not available — do NOT invent values.
 *
 * @param {string} imageId
 * @returns {Promise<object|null>}
 */
export async function getImageMetadata(imageId) {
  try {
    return await api.get(`/api/images/${imageId}/metadata`);
  } catch (_) {
    return null; // Metadata unavailable — caller should display "Not available"
  }
}

/**
 * Delete an uploaded image from the backend.
 * @param {string} imageId
 */
export async function deleteImage(imageId) {
  return api.delete(`/api/images/${imageId}`);
}

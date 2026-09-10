/**
 * Chat service — conversation and query management.
 * Adapter layer: backend response format can change here without touching UI components.
 */

import api from './api';
import config from '../config/env';

// ─── Response adapter ─────────────────────────────────────────────────────────
// Normalize backend response into the internal analysis format.
// Change this adapter when the backend response shape changes.

function adaptAnalysisResponse(raw) {
  if (!raw) return null;
  return {
    answer: raw.answer || '',
    task: raw.task || 'vqa',
    taskLabel: raw.task_label || raw.taskLabel || formatTaskLabel(raw.task),
    confidence: typeof raw.confidence === 'number' ? raw.confidence : null,
    regions: Array.isArray(raw.regions) ? raw.regions : [],
    changes: Array.isArray(raw.changes) ? raw.changes : [],
    images: Array.isArray(raw.images) ? raw.images : [],
    metadata: raw.metadata || {},
    execution: raw.execution
      ? {
          taskDetected: raw.execution.task_detected || raw.execution.taskDetected || '',
          tools: Array.isArray(raw.execution.tools) ? raw.execution.tools : [],
          inputType: raw.execution.input_type || raw.execution.inputType || '',
          status: raw.execution.status || 'completed',
          durationMs: raw.execution.duration_ms || raw.execution.durationMs || null,
          outputType: raw.execution.output_type || raw.execution.outputType || '',
        }
      : null,
  };
}

function formatTaskLabel(task) {
  if (!task) return 'Analysis';
  return task
    .replace(/_/g, ' ')
    .split(' ')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

// ─── API functions ────────────────────────────────────────────────────────────

/**
 * Send a query to the SatQuery AI backend.
 *
 * @param {{
 *   conversationId: string,
 *   query: string,
 *   imageIds: string[],
 *   hasImages: boolean,
 * }} params
 * @returns {Promise<object>}   Normalized analysis result
 */
export async function sendQuery({ conversationId, query, imageIds = [] }) {
  const raw = await api.post('/api/query', {
    conversation_id: conversationId,
    query,
    image_ids: imageIds,
  });

  return adaptAnalysisResponse(raw);
}

/**
 * Retrieve an existing conversation by ID.
 * @param {string} conversationId
 * @returns {Promise<object|null>}
 */
export async function getConversation(conversationId) {
  return api.get(`/api/conversations/${conversationId}`);
}

/**
 * List all conversations for the current user.
 * @returns {Promise<object[]>}
 */
export async function listConversations() {
  return api.get('/api/conversations');
}

/**
 * Delete a conversation.
 * @param {string} conversationId
 */
export async function deleteConversation(conversationId) {
  return api.delete(`/api/conversations/${conversationId}`);
}

/**
 * Request a downloadable report for a completed analysis.
 * @param {string} conversationId
 * @param {string} analysisId
 * @returns {Promise<{ download_url: string }>}
 */
export async function requestReport(conversationId, analysisId) {
  return api.post('/api/reports', { conversation_id: conversationId, analysis_id: analysisId });
}

/**
 * Check backend health.
 * @returns {Promise<boolean>}
 */
export async function checkBackendHealth() {
  return api.ping();
}

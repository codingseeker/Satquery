/**
 * Application environment configuration.
 * All environment variables must be prefixed with VITE_ to be exposed to the client.
 * Never place API keys, secrets, or credentials here.
 */

const config = {
  /** Base URL for the SatQuery AI backend API */
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

  /**
   * Demo mode flag.
   * When true, the app uses isolated mock data instead of real API calls.
   * Set VITE_DEMO_MODE=true in .env for offline/demonstration use.
   */
  isDemoMode: import.meta.env.VITE_DEMO_MODE === 'true',

  /** Application version */
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',

  /** Max file size allowed for upload (bytes). Default: 500 MB */
  maxFileSizeBytes: Number(import.meta.env.VITE_MAX_FILE_SIZE_MB || 500) * 1024 * 1024,

  /** Request timeout in milliseconds */
  requestTimeoutMs: Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 120000),
};

export default config;

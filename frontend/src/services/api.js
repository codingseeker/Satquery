import config from '../config/env';

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

function getToken() {
  return localStorage.getItem('satquery_token');
}

class APIClient {
  constructor() {
    this.baseUrl = config.apiBaseUrl;
    this.timeoutMs = config.requestTimeoutMs;
  }

  async request(method, path, body = null, extraHeaders = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };

    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
      method,
      headers,
      signal: controller.signal,
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, options);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData = null;
        try { errorData = await response.json(); } catch (_) { /* ignore */ }
        if (response.status === 401) {
          localStorage.removeItem('satquery_token');
          localStorage.removeItem('satquery_email');
          window.dispatchEvent(new Event('satquery:logout'));
          return new Promise(() => {});
        }
        const message = errorData?.detail || errorData?.message || `Request failed with status ${response.status}`;
        throw new APIError(message, response.status, errorData);
      }

      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return response.json();
      }
      return response.text();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new APIError('Request timed out. The analysis service may be unavailable.', 408, null);
      }
      if (err instanceof APIError) throw err;
      throw new APIError(
        'SatQuery AI could not connect to the analysis service. Please check your network and try again.',
        0,
        null,
      );
    }
  }

  async get(path, headers = {}) {
    return this.request('GET', path, null, headers);
  }

  async post(path, body, headers = {}) {
    return this.request('POST', path, body, headers);
  }

  async delete(path, headers = {}) {
    return this.request('DELETE', path, null, headers);
  }

  async postFormData(path, formData) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers = {};
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        body: formData,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData = null;
        try { errorData = await response.json(); } catch (_) { /* ignore */ }
        if (response.status === 401) {
          localStorage.removeItem('satquery_token');
          localStorage.removeItem('satquery_email');
          window.dispatchEvent(new Event('satquery:logout'));
          return new Promise(() => {});
        }
        const message = errorData?.detail || errorData?.message || `Upload failed with status ${response.status}`;
        throw new APIError(message, response.status, errorData);
      }

      return response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new APIError('Upload timed out. The file may be too large or the service is unavailable.', 408, null);
      }
      if (err instanceof APIError) throw err;
      throw new APIError('Upload failed. Please try again.', 0, null);
    }
  }

  async ping() {
    try {
      await this.get('/health');
      return true;
    } catch (_) {
      return false;
    }
  }
}

export { APIError };
export default new APIClient();

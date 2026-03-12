/**
 * Autify Engine V1 -- API client
 * All calls hit the local FastAPI backend (Zero-Cloud).
 * Supports bearer token auth for multi-user login.
 */

const BASE = '/api';

let _authToken = localStorage.getItem('autify_token') || null;

export function setAuthToken(token) {
  _authToken = token;
  if (token) localStorage.setItem('autify_token', token);
  else localStorage.removeItem('autify_token');
}

export function getAuthToken() {
  return _authToken;
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (_authToken) {
    headers['Authorization'] = `Bearer ${_authToken}`;
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    // Token expired / invalid
    setAuthToken(null);
    window.dispatchEvent(new Event('autify:logout'));
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

/* -- Auth -------------------------------------------------------- */
export const authLogin      = (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) });
export const authLogout     = ()     => request('/auth/logout', { method: 'POST' });
export const authMe         = ()     => request('/auth/me');
export const authRegister   = (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
export const authChangePass = (data) => request('/auth/change-password', { method: 'POST', body: JSON.stringify(data) });
export const authListUsers  = ()     => request('/auth/users');
export const authDeleteUser = (id)   => request(`/auth/users/${id}`, { method: 'DELETE' });

/* -- Clients ----------------------------------------------------- */
export const fetchClients    = ()           => request('/clients');
export const fetchClient     = (id)         => request(`/clients/${id}`);
export const createClient    = (data)       => request('/clients', { method: 'POST', body: JSON.stringify(data) });
export const updateClient    = (id, data)   => request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteClient    = (id)         => request(`/clients/${id}`, { method: 'DELETE' });

/* -- Inputs ------------------------------------------------------ */
export const fetchInputs     = ()           => request('/inputs');

export async function uploadFile(clientId, file) {
  const form = new FormData();
  form.append('file', file);
  const headers = {};
  if (_authToken) headers['Authorization'] = `Bearer ${_authToken}`;
  const res = await fetch(`${BASE}/upload/${clientId}`, { method: 'POST', body: form, headers });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

/* -- Analytics --------------------------------------------------- */
export const fetchAnalytics  = ()           => request('/analytics');
export const fetchSummary    = ()           => request('/analytics/summary');

/* -- Drafts ------------------------------------------------------ */
export const fetchDrafts     = (status)     => request(`/drafts${status ? `?status=${status}` : ''}`);
export const fetchDraft      = (id)         => request(`/drafts/${id}`);
export const approveDraft    = (id, userId = 'Admin') =>
  request(`/drafts/${id}/approve`, { method: 'POST', body: JSON.stringify({ user_id: userId }) });
export const rejectDraft     = (id, userId = 'Admin') =>
  request(`/drafts/${id}/reject`,  { method: 'POST', body: JSON.stringify({ user_id: userId }) });

/* -- Chat Bot ---------------------------------------------------- */
export const sendChatMessage = (message, sessionId) =>
  request('/chat', { method: 'POST', body: JSON.stringify({ message, session_id: sessionId }) });
export const fetchChatHistory = (sessionId) =>
  request(`/chat/history${sessionId ? `?session_id=${sessionId}` : ''}`);

/* -- Notifications ----------------------------------------------- */
export const fetchNotifications = ()        => request('/notifications');

/* -- Logs -------------------------------------------------------- */
export const fetchLogs       = ()           => request('/logs');

/* -- Health ------------------------------------------------------ */
export const healthCheck     = ()           => request('/health');

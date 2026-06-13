import axios from 'axios';

/**
 * API origin for axios. Default `http://localhost:8001` matches ./run_engine.sh (avoids clashes with other apps on 8000).
 * Set `VITE_API_URL=` (empty) in `.env` to force same-origin `/api/v1` + Vite proxy.
 */
const raw = import.meta.env.VITE_API_URL;
const API_BASE =
  raw === ''
    ? ''
    : (raw ?? 'http://localhost:8001').replace(/\/$/, '');

export const api = axios.create({
  baseURL: API_BASE ? `${API_BASE}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;




















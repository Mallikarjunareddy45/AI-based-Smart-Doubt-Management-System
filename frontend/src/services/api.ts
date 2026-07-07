import axios from 'axios';

let apiBaseUrl = (import.meta.env.VITE_API_URL as string) || 'https://ai-doubt-backend.onrender.com';
if (apiBaseUrl) {
  if (apiBaseUrl.includes('ai-based-smart-doubt-management-system.onrender.com')) {
    apiBaseUrl = apiBaseUrl.replace('ai-based-smart-doubt-management-system.onrender.com', 'ai-doubt-backend.onrender.com');
  }
  if (!apiBaseUrl.startsWith('http') && !apiBaseUrl.startsWith('/')) {
    apiBaseUrl = 'https://' + apiBaseUrl;
  }
  if (!apiBaseUrl.includes('/api/v1')) {
    apiBaseUrl = apiBaseUrl.replace(/\/+$/, '') + '/api/v1';
  }
}

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to dynamically inject access token into authorization headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to catch auth failures (like expired tokens) and trigger redirection
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear expired credentials from client state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      // Redirect to login if on protected screen
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

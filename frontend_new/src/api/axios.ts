import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
});

// Global error handling
api.interceptors.response.use(
  response => response,
  error => Promise.reject(error)
);

export default api;

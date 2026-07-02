import axios from 'axios';
import type { ApiErrorResponse, NormalizedApiError } from '../types/common';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor — normalize errors to a consistent shape
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      const apiError = error.response.data as ApiErrorResponse;
      const { code, message, details } = apiError.error;
      const normalized = new Error(message) as NormalizedApiError;
      normalized.code = code;
      normalized.details = details || {};
      normalized.status = error.response.status;
      return Promise.reject(normalized);
    }
    return Promise.reject(error);
  },
);

export default apiClient;

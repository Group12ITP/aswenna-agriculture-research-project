import axios, { AxiosError } from 'axios';

const STORAGE_KEY = 'agricost_api_base_url';

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && saved.trim()) return saved.trim();
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
}

export function setApiBaseUrl(url: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, url.trim());
    apiClient.defaults.baseURL = url.trim();
  }
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

// Request Interceptor: Log in development
apiClient.interceptors.request.use(
  (config) => {
    // Dynamic baseURL from storage in case it changed
    config.baseURL = getApiBaseUrl();
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data || '');
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Surface clean 422 validation error messages
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.status} from ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError<{ detail?: any }>) => {
    if (error.response) {
      const data = error.response.data;
      if (error.response.status === 422 && data?.detail) {
        let formattedMessage = '';
        if (Array.isArray(data.detail)) {
          formattedMessage = data.detail
            .map((err: any) => {
              const field = err.loc ? err.loc.slice(1).join('.') : 'field';
              return `${field}: ${err.msg}`;
            })
            .join(' | ');
        } else if (typeof data.detail === 'string') {
          formattedMessage = data.detail;
        } else {
          formattedMessage = JSON.stringify(data.detail);
        }
        return Promise.reject(new Error(formattedMessage));
      }
      if (data?.detail && typeof data.detail === 'string') {
        return Promise.reject(new Error(data.detail));
      }
    }
    return Promise.reject(error);
  }
);

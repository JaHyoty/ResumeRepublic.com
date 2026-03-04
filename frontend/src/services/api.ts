import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshPromise: Promise<void> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      withCredentials: true, // Send cookies with every request
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor — silent refresh on 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Don't retry auth endpoints to avoid loops
          const url = originalRequest?.url || '';
          const isAuthEndpoint = url.includes('/api/auth/login') 
            || url.includes('/api/auth/register')
            || url.includes('/api/auth/refresh');
          
          if (!isAuthEndpoint) {
            originalRequest._retry = true;

            try {
              // Coalesce concurrent refresh calls into one
              if (!this.isRefreshing) {
                this.isRefreshing = true;
                this.refreshPromise = this.client
                  .post('/api/auth/refresh')
                  .then(() => {})
                  .finally(() => {
                    this.isRefreshing = false;
                    this.refreshPromise = null;
                  });
              }

              await this.refreshPromise;
              // Retry the original request — new access_token cookie is set
              return this.client(originalRequest);
            } catch (refreshError) {
              // Refresh failed — redirect to login
              window.location.href = '/login';
            }
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  async get(url: string, config?: AxiosRequestConfig) {
    return this.client.get(url, config);
  }

  async post(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post(url, data, config);
  }

  async put(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put(url, data, config);
  }

  async delete(url: string, config?: AxiosRequestConfig) {
    return this.client.delete(url, config);
  }
}

export const apiClient = new ApiClient();

// For backward compatibility, export as 'api'
export const api = apiClient;
export default api;

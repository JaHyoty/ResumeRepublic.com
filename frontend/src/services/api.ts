import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          // Only redirect if it's not a login/register endpoint
          const url = error.config?.url || ''
          const isAuthEndpoint = url.includes('/api/auth/login') || url.includes('/api/auth/register')
          
          if (!isAuthEndpoint) {
            try {
              const refreshToken = localStorage.getItem('refresh_token');
              if (refreshToken) {
                const response = await this.post<{ access_token: string }>('/api/auth/refresh');
                const { access_token } = response.data;
                localStorage.setItem('auth_token', access_token);
                originalRequest.headers.Authorization = `Bearer ${access_token}`;
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed, redirect to login
              localStorage.removeItem('auth_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.get(url, config);
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.post(url, data, config);
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.put(url, data, config);
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<{ data: T }> {
    return this.client.delete(url, config);
  }
}

export const apiClient = new ApiClient();

// For backward compatibility, export as 'api'
export const api = apiClient;
export default api;

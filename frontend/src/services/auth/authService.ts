import { apiClient } from '../api/client';
import type { 
  User, 
  AuthToken, 
  LoginCredentials, 
  RegisterCredentials, 
  OAuthCredentials 
} from '../../types/auth';

export class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await apiClient.post<AuthToken>('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return response.data;
  }

  async register(credentials: RegisterCredentials): Promise<AuthToken> {
    const response = await apiClient.post<AuthToken>('/api/auth/register', credentials);
    return response.data;
  }

  async loginWithGoogle(credentials: OAuthCredentials): Promise<AuthToken> {
    const response = await apiClient.post<AuthToken>('/api/auth/oauth/google', credentials);
    return response.data;
  }

  async loginWithGitHub(credentials: OAuthCredentials): Promise<AuthToken> {
    const response = await apiClient.post<AuthToken>('/api/auth/oauth/github', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<AuthToken> {
    const response = await apiClient.post<AuthToken>('/api/auth/refresh');
    return response.data;
  }

  setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  removeToken(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }

  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch {
      return true;
    }
  }
}

export const authService = new AuthService();

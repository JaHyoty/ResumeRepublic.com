import { api } from './api'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  preferred_first_name?: string
  is_active: boolean
  is_verified: boolean
  terms_accepted_at?: string
  privacy_policy_accepted_at?: string
  created_at: string
  updated_at?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  first_name: string
  last_name: string
  password: string
  preferred_first_name?: string
}

export interface AuthResponse {
  token_type: string
  access_token_expires_in: number
  refresh_token_expires_in: number
  needs_agreement?: boolean
  message?: string
}

export interface GoogleOAuthRequest {
  id_token: string
}

export const authService = {
  // Register a new user
  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post('/api/auth/register', userData)
    return response.data
  },

  // Login user (sets httpOnly cookies via backend)
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post('/api/auth/login', credentials)
    return response.data
  },

  // Get current user info (uses cookie automatically)
  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  // Logout user (clears httpOnly cookies via backend)
  async logout(): Promise<void> {
    try {
      await api.post('/api/auth/logout')
    } catch {
      // Even if the server call fails, we still want to proceed with client-side cleanup
    }
  },

  // Refresh the access token (uses refresh_token cookie)
  async refreshToken(): Promise<AuthResponse> {
    const response = await api.post('/api/auth/refresh')
    return response.data
  },

  // Verify token by attempting to get current user
  async verifyToken(): Promise<boolean> {
    try {
      await api.get('/api/auth/verify-token')
      return true
    } catch {
      return false
    }
  },

  // Google OAuth login (sets httpOnly cookies via backend)
  async loginWithGoogle(idToken: string): Promise<AuthResponse> {
    const response = await api.post('/api/auth/google', {
      id_token: idToken
    })
    return response.data
  }
}

export default authService

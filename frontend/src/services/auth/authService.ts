import { api } from '../api'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  preferred_first_name?: string
  is_active: boolean
  is_verified: boolean
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
  access_token: string
  token_type: string
}

export const authService = {
  // Register a new user
  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post('/api/auth/register', userData)
    return response.data
  },

  // Login user
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post('/api/auth/login', credentials)
    return response.data
  },

  // Get current user info
  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  // Logout user
  async logout(): Promise<void> {
    await api.post('/api/auth/logout')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  },

  // Verify token
  async verifyToken(): Promise<boolean> {
    try {
      await api.get('/api/auth/verify-token')
      return true
    } catch {
      return false
    }
  },

  // Set auth token
  setToken(token: string): void {
    localStorage.setItem('auth_token', token)
  },

  // Get auth token
  getToken(): string | null {
    return localStorage.getItem('auth_token')
  },

  // Set user data
  setUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user))
  },

  // Get user data
  getUser(): User | null {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getToken()
  }
}

export default authService
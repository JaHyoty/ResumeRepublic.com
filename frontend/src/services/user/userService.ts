import { api } from '../api'

export interface UserInfo {
  id: number
  email: string
  first_name: string
  last_name: string
  preferred_first_name?: string
  phone?: string
  location?: string
  linkedin_url?: string
  website_url?: string
  professional_summary?: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at?: string
}

export interface UpdateUserRequest {
  first_name?: string
  last_name?: string
  preferred_first_name?: string
  phone?: string
  location?: string
  linkedin_url?: string
  website_url?: string
  professional_summary?: string
}

export const userService = {
  async getUserInfo(): Promise<UserInfo> {
    const response = await api.get('/api/user/')
    return response.data
  },

  async updateUser(userData: UpdateUserRequest): Promise<UserInfo> {
    const response = await api.put('/api/user/', userData)
    return response.data
  }
}

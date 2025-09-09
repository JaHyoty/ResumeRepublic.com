import { api } from '../api'

export interface UserProfile {
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

export interface UpdateProfileRequest {
  first_name?: string
  last_name?: string
  preferred_first_name?: string
  phone?: string
  location?: string
  linkedin_url?: string
  website_url?: string
  professional_summary?: string
}

export const profileService = {
  async getProfile(): Promise<UserProfile> {
    const response = await api.get('/api/profile/profile')
    return response.data
  },

  async updateProfile(profileData: UpdateProfileRequest): Promise<UserProfile> {
    const response = await api.put('/api/profile/profile', profileData)
    return response.data
  }
}

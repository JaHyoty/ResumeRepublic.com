import { api } from './api'

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

export interface TermsAgreementRequest {
  terms_accepted: boolean
  privacy_policy_accepted: boolean
}

export const userService = {
  async getUserInfo(): Promise<UserInfo> {
    const response = await api.get('/api/user/')
    return response.data
  },

  async updateUser(userData: UpdateUserRequest): Promise<UserInfo> {
    const response = await api.put('/api/user/', userData)
    return response.data
  },

  async deleteUser(): Promise<{ message: string }> {
    const response = await api.delete('/api/user/')
    return response.data
  },

  async acceptTerms(agreementData: TermsAgreementRequest): Promise<UserInfo> {
    const response = await api.post('/api/user/accept-terms', agreementData)
    return response.data
  }
}

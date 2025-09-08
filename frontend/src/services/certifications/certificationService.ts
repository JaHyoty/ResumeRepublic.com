import { api } from '../api'

export interface Certification {
  id: number
  user_id: number
  name: string
  issuer: string
  issue_date: string  // Will be serialized as YYYY-MM-DD from backend
  expiry_date?: string  // Will be serialized as YYYY-MM-DD from backend
  credential_id?: string
  credential_url?: string
}

export interface CreateCertificationRequest {
  name: string
  issuer: string
  issue_date: string  // YYYY-MM-DD format
  expiry_date?: string  // YYYY-MM-DD format
  credential_id?: string
  credential_url?: string
}

export interface UpdateCertificationRequest {
  name?: string
  issuer?: string
  issue_date?: string  // YYYY-MM-DD format
  expiry_date?: string  // YYYY-MM-DD format
  credential_id?: string
  credential_url?: string
}

export const certificationService = {
  // Get all certifications for the current user
  async getCertifications(): Promise<Certification[]> {
    const response = await api.get('/api/esc/certifications')
    return response.data
  },

  // Create a new certification
  async createCertification(data: CreateCertificationRequest): Promise<Certification> {
    const response = await api.post('/api/esc/certifications', data)
    return response.data
  },

  // Get a specific certification by ID
  async getCertification(id: number): Promise<Certification> {
    const response = await api.get(`/api/esc/certifications/${id}`)
    return response.data
  },

  // Update a certification
  async updateCertification(id: number, data: UpdateCertificationRequest): Promise<Certification> {
    const response = await api.put(`/api/esc/certifications/${id}`, data)
    return response.data
  },

  // Delete a certification
  async deleteCertification(id: number): Promise<void> {
    await api.delete(`/api/esc/certifications/${id}`)
  }
}

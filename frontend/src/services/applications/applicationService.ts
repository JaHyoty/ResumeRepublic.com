import { api } from '../api'

export interface Application {
  id: number
  user_id: number
  job_title: string
  company: string
  job_description?: string
  applied_date: string
  online_assessment: boolean
  interview: boolean
  rejected: boolean
  salary_range?: string
  location?: string
  job_type?: string
  experience_level?: string
  application_metadata?: any
  created_at: string
  updated_at?: string
}

export interface ApplicationStats {
  total_applications: number
  online_assessments: number
  interviews: number
  rejected: number
  online_assessment_rate: number
  interview_rate: number
  rejection_rate: number
}

export interface CreateApplicationRequest {
  job_title: string
  company: string
  job_description?: string
  online_assessment?: boolean
  interview?: boolean
  rejected?: boolean
  salary_range?: string
  location?: string
  job_type?: string
  experience_level?: string
  application_metadata?: any
}

export interface UpdateApplicationRequest {
  job_title?: string
  company?: string
  job_description?: string
  online_assessment?: boolean
  interview?: boolean
  rejected?: boolean
  salary_range?: string
  location?: string
  job_type?: string
  experience_level?: string
  application_metadata?: any
}

export const applicationService = {
  // Get all applications
  async getApplications(): Promise<Application[]> {
    const response = await api.get('/api/applications/')
    return response.data
  },

  // Get application statistics
  async getApplicationStats(): Promise<ApplicationStats> {
    const response = await api.get('/api/applications/stats')
    return response.data
  },

  // Get a specific application
  async getApplication(id: number): Promise<Application> {
    const response = await api.get(`/api/applications/${id}`)
    return response.data
  },

  // Create a new application
  async createApplication(data: CreateApplicationRequest): Promise<Application> {
    const response = await api.post('/api/applications/', data)
    return response.data
  },

  // Update an application
  async updateApplication(id: number, data: UpdateApplicationRequest): Promise<Application> {
    const response = await api.put(`/api/applications/${id}`, data)
    return response.data
  },

  // Delete an application
  async deleteApplication(id: number): Promise<void> {
    await api.delete(`/api/applications/${id}`)
  },
}

export default applicationService

import { api } from './api'

export interface ExperienceTitle {
  id?: number
  title: string
  is_primary: boolean
}

export interface Achievement {
  id?: number
  description: string
}

export interface Experience {
  id?: number
  company: string
  location?: string
  start_date: string
  end_date?: string
  description?: string
  is_current: boolean
  titles: ExperienceTitle[]
  achievements: Achievement[]
}

export interface CreateExperienceRequest {
  company: string
  location?: string
  start_date: string
  end_date?: string
  description?: string
  is_current: boolean
  titles: Omit<ExperienceTitle, 'id'>[]
  achievements: Omit<Achievement, 'id'>[]
}

export const experienceService = {
  async getExperiences(): Promise<Experience[]> {
    try {
      const response = await api.get<Experience[]>('/api/esc/experiences')
      return response.data
    } catch (error) {
      console.error('Failed to fetch experiences:', error)
      throw error
    }
  },

  async createExperience(experienceData: CreateExperienceRequest): Promise<Experience> {
    try {
      const response = await api.post<Experience>('/api/esc/experiences', experienceData)
      return response.data
    } catch (error) {
      console.error('Failed to create experience:', error)
      throw error
    }
  },

  async updateExperience(id: number, experienceData: Partial<CreateExperienceRequest>): Promise<Experience> {
    try {
      const response = await api.put<Experience>(`/api/esc/experiences/${id}`, experienceData)
      return response.data
    } catch (error) {
      console.error('Failed to update experience:', error)
      throw error
    }
  },

  async deleteExperience(id: number): Promise<void> {
    try {
      await api.delete(`/api/esc/experiences/${id}`)
    } catch (error) {
      console.error('Failed to delete experience:', error)
      throw error
    }
  },

  async getExperience(id: number): Promise<Experience> {
    try {
      const response = await api.get<Experience>(`/api/esc/experiences/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch experience:', error)
      throw error
    }
  }
}

import { api } from './api'

export interface Education {
  id: number
  institution: string
  degree: string
  field_of_study?: string
  start_date: string
  end_date?: string
  gpa?: string
  description?: string
  location?: string
  website_url?: string
}

export interface EducationCreate {
  institution: string
  degree: string
  field_of_study?: string
  start_date: string
  end_date?: string
  gpa?: string
  description?: string
  location?: string
  website_url?: string
}

export interface EducationUpdate {
  institution?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
  gpa?: string
  description?: string
  location?: string
  website_url?: string
}

export const educationService = {
  async getEducation(): Promise<Education[]> {
    const response = await api.get<Education[]>('/api/esc/education')
    return response.data
  },

  async createEducation(educationData: EducationCreate): Promise<Education> {
    const response = await api.post<Education>('/api/esc/education', educationData)
    return response.data
  },

  async updateEducation(id: number, educationData: EducationUpdate): Promise<Education> {
    const response = await api.put<Education>(`/api/esc/education/${id}`, educationData)
    return response.data
  },

  async deleteEducation(id: number): Promise<void> {
    await api.delete(`/api/esc/education/${id}`)
  }
}

import { api } from './api'

export interface Project {
  id?: number
  name: string
  description?: string
  start_date: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies_used?: string
}

export interface CreateProjectRequest {
  name: string
  description?: string
  start_date: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies_used?: string
}

export const projectService = {
  async getProjects(): Promise<Project[]> {
    try {
      const response = await api.get('/api/esc/projects')
      return response.data
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      throw error
    }
  },

  async createProject(projectData: CreateProjectRequest): Promise<Project> {
    try {
      const response = await api.post('/api/esc/projects', projectData)
      return response.data
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  },

  async updateProject(id: number, projectData: Partial<CreateProjectRequest>): Promise<Project> {
    try {
      const response = await api.put(`/api/esc/projects/${id}`, projectData)
      return response.data
    } catch (error) {
      console.error('Failed to update project:', error)
      throw error
    }
  },

  async deleteProject(id: number): Promise<void> {
    try {
      await api.delete(`/api/esc/projects/${id}`)
    } catch (error) {
      console.error('Error deleting project:', error)
      throw error
    }
  }
}
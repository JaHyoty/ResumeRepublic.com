import { api } from './api'

export interface ProjectTechnology {
  id?: number
  technology: string
}

export interface ProjectAchievement {
  id?: number
  description: string
}

export interface Project {
  id?: number
  name: string
  description?: string
  start_date: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies: ProjectTechnology[]
  achievements: ProjectAchievement[]
}

export interface CreateProjectRequest {
  name: string
  description?: string
  start_date: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies: Omit<ProjectTechnology, 'id'>[]
  achievements: Omit<ProjectAchievement, 'id'>[]
}

export const projectService = {
  async getProjects(): Promise<Project[]> {
    try {
      const response = await api.get<Project[]>('/api/esc/projects')
      return response.data
    } catch (error) {
      console.error('Failed to fetch projects:', error)
      throw error
    }
  },

  async createProject(projectData: CreateProjectRequest): Promise<Project> {
    try {
      const response = await api.post<Project>('/api/esc/projects', projectData)
      return response.data
    } catch (error) {
      console.error('Failed to create project:', error)
      throw error
    }
  },

  async updateProject(id: number, projectData: Partial<CreateProjectRequest>): Promise<Project> {
    try {
      const response = await api.put<Project>(`/api/esc/projects/${id}`, projectData)
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
      console.error('Failed to delete project:', error)
      throw error
    }
  },

  async getProject(id: number): Promise<Project> {
    try {
      const response = await api.get<Project>(`/api/esc/projects/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch project:', error)
      throw error
    }
  }
}

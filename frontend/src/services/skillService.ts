import { api } from './api'

export interface Skill {
  id: number
  user_id: number
  name: string
}

export interface CreateSkillRequest {
  name: string
}

export interface UpdateSkillRequest {
  name?: string
}

export const skillService = {
  // Get all skills for the current user
  async getSkills(): Promise<Skill[]> {
    const response = await api.get('/api/esc/skills')
    return response.data
  },

  // Create a new skill
  async createSkill(data: CreateSkillRequest): Promise<Skill> {
    const response = await api.post('/api/esc/skills', data)
    return response.data
  },

  // Get a specific skill by ID
  async getSkill(id: number): Promise<Skill> {
    const response = await api.get(`/api/esc/skills/${id}`)
    return response.data
  },

  // Update a skill
  async updateSkill(id: number, data: UpdateSkillRequest): Promise<Skill> {
    const response = await api.put(`/api/esc/skills/${id}`, data)
    return response.data
  },

  // Delete a skill
  async deleteSkill(id: number): Promise<void> {
    await api.delete(`/api/esc/skills/${id}`)
  },

  // Create multiple skills at once
  async createSkillsBulk(skillNames: string[]): Promise<Skill[]> {
    const response = await api.post('/api/esc/skills/bulk', skillNames)
    return response.data
  }
}

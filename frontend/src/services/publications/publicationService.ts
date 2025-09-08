import { api } from '../api'

export interface Publication {
  id: number
  user_id: number
  title: string
  co_authors?: string
  publisher?: string
  publication_date?: string  // Will be serialized as YYYY-MM-DD from backend
  url?: string
  description?: string
  publication_type?: string
}

export interface CreatePublicationRequest {
  title: string
  co_authors?: string
  publisher?: string
  publication_date?: string  // YYYY-MM-DD format
  url?: string
  description?: string
  publication_type?: string
}

export interface UpdatePublicationRequest {
  title?: string
  co_authors?: string
  publisher?: string
  publication_date?: string  // YYYY-MM-DD format
  url?: string
  description?: string
  publication_type?: string
}

export const publicationService = {
  // Get all publications for the current user
  async getPublications(): Promise<Publication[]> {
    const response = await api.get('/api/esc/publications')
    return response.data
  },

  // Create a new publication
  async createPublication(data: CreatePublicationRequest): Promise<Publication> {
    const response = await api.post('/api/esc/publications', data)
    return response.data
  },

  // Get a specific publication by ID
  async getPublication(id: number): Promise<Publication> {
    const response = await api.get(`/api/esc/publications/${id}`)
    return response.data
  },

  // Update a publication
  async updatePublication(id: number, data: UpdatePublicationRequest): Promise<Publication> {
    const response = await api.put(`/api/esc/publications/${id}`, data)
    return response.data
  },

  // Delete a publication
  async deletePublication(id: number): Promise<void> {
    await api.delete(`/api/esc/publications/${id}`)
  }
}

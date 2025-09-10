import { api } from './api'

export interface Website {
  id: number
  site_name: string
  url: string
}

export interface WebsiteCreate {
  site_name: string
  url: string
}

export interface WebsiteUpdate {
  site_name?: string
  url?: string
}

export const getWebsites = async (): Promise<Website[]> => {
  const response = await api.get<Website[]>('/api/esc/websites')
  return response.data
}

export const createWebsite = async (websiteData: WebsiteCreate): Promise<Website> => {
  const response = await api.post<Website>('/api/esc/websites', websiteData)
  return response.data
}

export const updateWebsite = async (id: number, websiteData: WebsiteUpdate): Promise<Website> => {
  const response = await api.put<Website>(`/api/esc/websites/${id}`, websiteData)
  return response.data
}

export const deleteWebsite = async (id: number): Promise<void> => {
  await api.delete(`/api/esc/websites/${id}`)
}

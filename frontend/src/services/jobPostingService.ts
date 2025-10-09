import { api } from './api'

// Types matching backend schemas
export interface JobPostingFetchRequest {
  url: string
  source: string
}

export interface JobPostingFetchResponse {
  job_posting_id: string
  status: string
  message: string
}

export interface ProvenanceInfo {
  method: string
  extractor?: string
  confidence?: number
  excerpt?: string
  timestamp?: string
}

export interface JobPostingResponse {
  id: string
  url?: string
  domain?: string
  created_by_user_id?: number
  title?: string
  company?: string
  description?: string
  status: string
  provenance?: ProvenanceInfo
  created_at: string
  updated_at: string
}

export interface JobPostingCreateRequest {
  title: string
  company: string
  description: string
  url?: string
}

export interface JobPostingListResponse {
  job_postings: JobPostingResponse[]
  total: number
  page: number
  page_size: number
}

export const jobPostingService = {
  // Fetch job posting from URL
  async fetchJobPosting(data: JobPostingFetchRequest): Promise<JobPostingFetchResponse> {
    try {
      const response = await api.post('/api/job-postings/fetch', data)
      return response.data
    } catch (error) {
      console.error('Failed to fetch job posting:', error)
      throw error
    }
  },

  // Create job posting manually
  async createJobPosting(data: JobPostingCreateRequest): Promise<JobPostingResponse> {
    try {
      const response = await api.post('/api/job-postings/create', data)
      return response.data
    } catch (error) {
      console.error('Failed to create job posting:', error)
      throw error
    }
  },

  // Get job posting by ID
  async getJobPosting(id: string): Promise<JobPostingResponse> {
    try {
      const response = await api.get(`/api/job-postings/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to get job posting:', error)
      throw error
    }
  }
}

export default jobPostingService

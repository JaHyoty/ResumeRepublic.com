import { api } from './api'

// Types matching backend schemas
export interface JobPostingFetchRequest {
  url: string
  source: string
}

export interface JobPostingFetchResponse {
  job_id: string
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

export interface DomainSelectorResponse {
  id: string
  domain: string
  selectors: {
    title?: string
    company?: string
    description?: string
  }
  last_success?: string
  created_at: string
  updated_at: string
}

export interface FetchAttemptResponse {
  id: string
  job_posting_id: string
  method: string
  response_code?: number
  duration_ms?: number
  note?: string
  created_at: string
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
  },

  // Get job posting fetch attempts
  async getJobPostingAttempts(id: string): Promise<FetchAttemptResponse[]> {
    try {
      const response = await api.get(`/api/job-postings/${id}/attempts`)
      return response.data
    } catch (error) {
      console.error('Failed to get job posting attempts:', error)
      throw error
    }
  },

  // Get domain selectors (admin endpoint)
  async getDomainSelectors(): Promise<DomainSelectorResponse[]> {
    try {
      const response = await api.get('/api/job-postings/domains/selectors')
      return response.data
    } catch (error) {
      console.error('Failed to get domain selectors:', error)
      throw error
    }
  }
}

export default jobPostingService

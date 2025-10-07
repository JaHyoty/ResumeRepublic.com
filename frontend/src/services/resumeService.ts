import { api } from './api'
import type { AxiosResponse } from 'axios'

export interface ResumeVersion {
  id: number
  title: string
  template_used: string
  pdf_url: string
  created_at: string
  updated_at: string
  has_pdf: boolean
}

export interface ResumeVersionsResponse {
  resume_versions: ResumeVersion[]
}

export interface LaTeXContentResponse {
  latex_content: string
}

export interface ResumeDesignRequest {
  personal_info: {
    name: string
    email: string
    phone: string
    location?: string
    linkedin?: string
    website?: string
    summary?: string
  }
  job_title: string
  company: string
  job_description: string
  linked_application_id?: number | null
  locale?: string
}

export interface ResumeDesignResponse {
  resumeVersionId: number
  pdfBlob: Blob
}

export interface ResumeDesignApiResponse {
  resume_version_id: number
  pdf_data: string // base64 encoded
  filename: string
  content_type: string
}

export interface KeywordAnalysisRequest {
  job_description: string
}

export interface KeywordAnalysisResponse {
  keywords: string[]
}

export const resumeService = {
  // Get resume versions for an application
  async getResumeVersions(applicationId: number): Promise<ResumeVersion[]> {
    const response = await api.get(`/api/resume/versions/${applicationId}`)
    return (response.data as ResumeVersionsResponse).resume_versions
  },

  // Design a new resume and return PDF blob with resume version ID
  async designResume(data: ResumeDesignRequest): Promise<ResumeDesignResponse> {
    try {
      const response = await api.post('/api/resume/design', data, {
        timeout: 60000 // 60 seconds timeout for resume generation
      })

      const apiResponse = response.data as ResumeDesignApiResponse
      
      // Convert base64 PDF data back to blob
      const binaryString = atob(apiResponse.pdf_data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const pdfBlob = new Blob([bytes], { type: 'application/pdf' })

      return {
        resumeVersionId: apiResponse.resume_version_id,
        pdfBlob: pdfBlob
      }
    } catch (error) {
      console.error('Error generating resume:', error)
      
      let errorMessage = 'Failed to generate resume. Please try again.'
      
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          errorMessage = 'Resume generation timed out. Please try again with a shorter job description.'
        } else if (error.message.includes('Network Error')) {
          errorMessage = 'Network error. Please check your connection and try again.'
        } else if (error.message.includes('403')) {
          errorMessage = 'Authentication error. Please log in again.'
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error. Please try again later.'
        }
      }
      
      throw new Error(errorMessage)
    }
  },

  // Get LaTeX content for a resume version
  async getLatexContent(resumeVersionId: number): Promise<string> {
    try {
      const response = await api.get(`/api/resume/latex/${resumeVersionId}`)
      return (response.data as LaTeXContentResponse).latex_content
    } catch (error) {
      console.error('Error fetching LaTeX content:', error)
      throw new Error('Failed to load LaTeX content. Please try again.')
    }
  },

  // Update LaTeX content and regenerate PDF
  async updateLatexContent(resumeVersionId: number, latexContent: string): Promise<Blob> {
    try {
      const response = await api.put(`/api/resume/latex/${resumeVersionId}`, {
        latex_content: latexContent
      }, {
        responseType: 'blob',
        timeout: 60000 // 60 seconds timeout for LaTeX compilation
      }) as AxiosResponse<Blob>

      return response.data
    } catch (error) {
      console.error('Error updating LaTeX content:', error)
      
      let errorMessage = 'Failed to update resume. Please try again.'
      
      if (error instanceof Error) {
        if (error.message.includes('400')) {
          errorMessage = 'LaTeX compilation failed. Please check your LaTeX syntax.'
        } else if (error.message.includes('timeout')) {
          errorMessage = 'LaTeX compilation timed out. Please try again.'
        }
      }
      
      throw new Error(errorMessage)
    }
  },

  // View PDF in browser (no download)
  async viewResumePdf(resumeId: number): Promise<void> {
    try {
      // Get the CloudFront signed URL - Content-Disposition header is stored in S3 metadata
      const response = await api.get(`/api/resume/pdf/${resumeId}/url`)
      const cloudfrontUrl = (response.data as {url: string, filename: string}).url
      
      // Create a temporary link element to bypass React Router completely
      const link = document.createElement('a')
      link.href = cloudfrontUrl
      link.target = '_blank'
      link.rel = 'noopener noreferrer'
      
      // Append to body, click, and remove
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Failed to open PDF:', error)
      throw new Error('Failed to open PDF. Please try again.')
    }
  },

  // Analyze job description for keywords
  async analyzeKeywords(jobDescription: string): Promise<string[]> {
    try {
      const response = await api.post('/api/resume/analyze-keywords', {
        job_description: jobDescription
      }, {
        timeout: 30000 // 30 seconds timeout for keyword analysis
      })

      const result = response.data as KeywordAnalysisResponse
      return result.keywords
    } catch (error) {
      console.error('Error analyzing keywords:', error)
      
      let errorMessage = 'Failed to analyze keywords. Please try again.'
      
      if (error instanceof Error) {
        if (error.message.includes('timeout')) {
          errorMessage = 'Keyword analysis timed out. Please try again with a shorter job description.'
        } else if (error.message.includes('Network Error')) {
          errorMessage = 'Network error. Please check your connection and try again.'
        } else if (error.message.includes('503')) {
          errorMessage = 'AI service temporarily unavailable. Please try again later.'
        } else if (error.message.includes('400')) {
          errorMessage = 'Please provide a valid job description.'
        }
      }
      
      throw new Error(errorMessage)
    }
  }
}

import { api } from './api'

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

export const resumeService = {
  // Get resume versions for an application
  async getResumeVersions(applicationId: number): Promise<ResumeVersion[]> {
    const response = await api.get<ResumeVersionsResponse>(`/api/resume/versions/${applicationId}`)
    return response.data.resume_versions
  },


  // View PDF in browser (no download)
  async viewResumePdf(resumeId: number): Promise<void> {
    try {
      // Get the CloudFront signed URL - Content-Disposition header is stored in S3 metadata
      const response = await api.get<{url: string, filename: string}>(`/api/resume/pdf/${resumeId}/url`)
      const cloudfrontUrl = response.data.url
      
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
  }
}

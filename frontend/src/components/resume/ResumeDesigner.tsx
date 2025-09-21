import React, { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { applicationService } from '../../services/applicationService'
import { userService } from '../../services/userService'
import { api } from '../../services/api'
import PDFViewer from './PDFViewer'

interface PersonalInfo {
  name: string
  email: string
  phone: string
  location: string
  linkedin?: string
  website?: string
  summary?: string
}

interface ResumeDesignerProps {
  linkedApplicationId?: number
  jobDescription?: string
}

const ResumeDesigner: React.FC<ResumeDesignerProps> = ({ 
  linkedApplicationId, 
  jobDescription: initialJobDescription 
}) => {
  const location = useLocation()
  const [personalInfo, setPersonalInfo] = useState<PersonalInfo>({
    name: '',
    email: '',
    phone: '',
    location: '',
    linkedin: '',
    website: '',
    summary: ''
  })
  
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  // Template is now fixed to resume-template-1
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [jobDescription, setJobDescription] = useState(initialJobDescription || '')
  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(linkedApplicationId || null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // Get user's locale for phone number formatting
  const [userLocale, setUserLocale] = useState<string>('en-US')

  // Detect user's locale on component mount
  useEffect(() => {
    const detectedLocale = navigator.language || navigator.languages?.[0] || 'en-US'
    setUserLocale(detectedLocale)
  }, [])

  // Fetch user data (only for personal info and applications)
  const { data: userInfo } = useQuery({
    queryKey: ['userInfo'],
    queryFn: userService.getUserInfo
  })

  const { data: applications } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationService.getApplications
  })

  // Handle navigation state from ApplicationsView
  useEffect(() => {
    if (location.state) {
      const { jobDescription: navJobDescription, applicationId } = location.state as any
      if (navJobDescription) {
        setJobDescription(navJobDescription)
      }
      if (applicationId) {
        setSelectedApplicationId(applicationId)
      }
    }
  }, [location.state])

  // Prepopulate personal info from user profile
  useEffect(() => {
    if (userInfo) {
      const fullName = userInfo.preferred_first_name 
        ? `${userInfo.preferred_first_name} ${userInfo.last_name}`
        : `${userInfo.first_name} ${userInfo.last_name}`
      
      setPersonalInfo({
        name: fullName,
        email: userInfo.email,
        phone: userInfo.phone || '',
        location: userInfo.location || '',
        linkedin: userInfo.linkedin_url || '',
        website: userInfo.website_url || '',
        summary: userInfo.professional_summary || ''
      })
    }
  }, [userInfo])

  // Load job details from linked application
  useEffect(() => {
    if (selectedApplicationId && applications) {
      const application = applications.find(app => app.id === selectedApplicationId)
      if (application) {
        if (application.job_title) setJobTitle(application.job_title)
        if (application.company) setCompany(application.company)
        if (application.job_description) setJobDescription(application.job_description)
      }
    }
  }, [selectedApplicationId, applications])

  // Handle clicks outside dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handlePersonalInfoChange = (field: keyof PersonalInfo, value: string) => {
    setPersonalInfo(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const generateResume = async () => {
    if (!jobTitle.trim() || !company.trim() || !jobDescription.trim()) {
      alert('Please provide job title, company, and job description')
      return
    }
    
    setIsGenerating(true)
    
    try {
      // Prepare resume data (only personal info and job details - backend fetches the rest)
      const data = {
        personal_info: personalInfo,
        job_title: jobTitle,
        company: company,
        job_description: jobDescription,
        linked_application_id: selectedApplicationId,
        locale: userLocale
      }

      // Generate optimized resume using LLM
      const response = await api.post<Blob>('/api/resume/design', data, {
        responseType: 'blob',
        timeout: 60000 // 60 seconds timeout for resume generation
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      setPdfUrl(url)

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
      
      alert(errorMessage)
    } finally {
      setIsGenerating(false)    
      
      // Scroll will be handled by the PDFViewer onReady callback
    }
  }

  const handlePdfViewerReady = () => {
    // Scroll to the PDF viewer when it's ready
    const pdfViewer = document.getElementById('pdf-viewer');
    if (pdfViewer) {
      pdfViewer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  const downloadResume = () => {
    if (pdfUrl) {
      const link = document.createElement('a')
      link.href = pdfUrl
      link.download = 'resume.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const handleApplicationSelect = (applicationId: number) => {
    setSelectedApplicationId(applicationId)
    const application = applications?.find(app => app.id === applicationId)
    if (application) {
      if (application.job_title) setJobTitle(application.job_title)
      if (application.company) setCompany(application.company)
      if (application.job_description) setJobDescription(application.job_description)
    }
    setIsDropdownOpen(false)
  }

  const handleDropdownToggle = () => {
    setIsDropdownOpen(!isDropdownOpen)
  }

  const getSelectedApplicationText = () => {
    if (!selectedApplicationId || !applications) return 'Select an application...'
    const application = applications.find(app => app.id === selectedApplicationId)
    return application ? `${application.job_title} at ${application.company}` : 'Select an application...'
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Resume Designer</h2>
        <p className="text-gray-600">Create an AI-optimized resume tailored to your target job</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Designer Panel */}
        <div className="space-y-6">
          {/* Job Description Input */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Description</h2>
            
            {/* Link to Application */}
            {applications && applications.length > 0 && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center mb-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <label className="text-sm font-semibold text-blue-800">
                    Link to Existing Application (Optional)
                  </label>
                </div>
                
                {/* Custom Dropdown */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    type="button"
                    onClick={handleDropdownToggle}
                    className="w-full px-4 py-3 bg-white border-2 border-blue-300 rounded-lg text-left text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 shadow-sm hover:border-blue-400 flex items-center justify-between"
                  >
                    <span className={selectedApplicationId ? 'text-gray-700' : 'text-gray-500'}>
                      {getSelectedApplicationText()}
                    </span>
                    <svg
                      className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                        isDropdownOpen ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {/* Dropdown Options */}
                  {isDropdownOpen && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                      <div
                        className="px-4 py-1.5 text-gray-500 cursor-pointer hover:bg-gray-50 border-b border-gray-100"
                        onClick={() => {
                          setSelectedApplicationId(null)
                          setJobTitle('')
                          setCompany('')
                          setJobDescription('')
                          setIsDropdownOpen(false)
                        }}
                      >
                        Select an application...
                      </div>
                      {applications.map((app) => (
                        <div
                          key={app.id}
                          className="px-4 py-1.5 text-gray-700 cursor-pointer hover:bg-blue-50 hover:text-blue-700 transition-colors duration-150 flex items-center justify-between"
                          onClick={() => handleApplicationSelect(app.id)}
                        >
                          <span className="font-medium">{app.job_title} at {app.company}</span>
                          {selectedApplicationId === app.id && (
                            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="mt-2 text-xs text-blue-600 flex items-center">
                  {selectedApplicationId ? (
                    <>
                      <span className="mr-1">✓</span>
                      <span>Application linked successfully</span>
                    </>
                  ) : (
                    <>
                      <span className="mr-1">✗</span>
                      <span>Application not linked</span>
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Software Engineer"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company *
                </label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Google"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Description *
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Paste the job description here to optimize your resume..."
              />
              <p className="text-sm text-gray-500 mt-1">
                The AI will analyze this job description to optimize your resume content, keywords, and structure.
              </p>
            </div>
          </div>

          {/* Personal Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  value={personalInfo.name}
                  onChange={(e) => handlePersonalInfoChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  value={personalInfo.email}
                  onChange={(e) => handlePersonalInfoChange('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your.email@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                <input
                  type="tel"
                  value={personalInfo.phone}
                  onChange={(e) => handlePersonalInfoChange('phone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="(555) 123-4567"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location *</label>
                <input
                  type="text"
                  value={personalInfo.location}
                  onChange={(e) => handlePersonalInfoChange('location', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="City, State"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn</label>
                <input
                  type="url"
                  value={personalInfo.linkedin || ''}
                  onChange={(e) => handlePersonalInfoChange('linkedin', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://linkedin.com/in/yourprofile"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
                <input
                  type="url"
                  value={personalInfo.website || ''}
                  onChange={(e) => handlePersonalInfoChange('website', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://yourwebsite.com"
                />
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Professional Summary</label>
              <textarea
                value={personalInfo.summary || ''}
                onChange={(e) => handlePersonalInfoChange('summary', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief summary of your professional background and key strengths..."
              />
              <p className="text-sm text-gray-500 mt-1">
                The AI will optimize this summary based on the job description.
              </p>
            </div>
          </div>

          {/* Template Selection */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Resume Template</h2>
            <div className="flex justify-center">
              <div className="p-4 border-2 border-blue-500 bg-blue-50 rounded-lg">
                <div className="text-center">
                  <img 
                    src="/templates/ResumeTemplate1.jpg" 
                    alt="Resume Template 1" 
                    className="w-48 h-64 object-cover rounded-lg shadow-md mx-auto mb-3"
                  />
                  <h3 className="font-medium text-gray-900">Professional Template</h3>
                  <p className="text-sm text-gray-600">Clean, modern layout optimized for ATS</p>
                </div>
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <button
              onClick={generateResume}
              disabled={isGenerating || !personalInfo.name || !personalInfo.email || !personalInfo.phone || !personalInfo.location || !jobTitle.trim() || !company.trim() || !jobDescription.trim()}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isGenerating ? 'Designing Resume...' : 'Design Resume with AI'}
            </button>
            <p className="text-sm text-gray-500 mt-2 text-center">
              AI will optimize your resume content, keywords, and structure for this specific job
            </p>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="space-y-6" id="pdf-viewer">
          {pdfUrl ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Resume Preview</h2>
                <button
                  onClick={downloadResume}
                  className="bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  Download PDF
                </button>
              </div>
              <PDFViewer pdfUrl={pdfUrl} id="pdf-viewer" onReady={handlePdfViewerReady} />
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">🎨</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Resume Designed</h3>
                <p className="text-gray-600">Fill in your information and job description, then click "Design Resume with AI" to create an optimized resume</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResumeDesigner

import React, { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { applicationService } from '../../services/applicationService'
import { userService } from '../../services/userService'
import { resumeService, type ResumeDesignRequest } from '../../services/resumeService'
import { webhookService, type WebhookEvent } from '../../services/webhookService'
import PDFViewer from './PDFViewer'
import KeywordAnalysis from './KeywordAnalysis'

interface PersonalInfo {
  name: string
  email: string
  phone: string
  location?: string
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
  const [currentResumeVersionId, setCurrentResumeVersionId] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'view' | 'edit'>('view')
  const [latexContent, setLatexContent] = useState<string>('')
  const [isLoadingLatex, setIsLoadingLatex] = useState(false)
  const [isUpdatingLatex, setIsUpdatingLatex] = useState(false)
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [jobDescription, setJobDescription] = useState(initialJobDescription || '')
  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(linkedApplicationId || null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  // Webhook-based resume generation state
  const [resumeGenerationId, setResumeGenerationId] = useState<number | null>(null)
  const [generationStatus, setGenerationStatus] = useState<string>('')
  const [generationMessage, setGenerationMessage] = useState<string>('')
  
  // Keyword analysis workflow state
  const [showKeywordAnalysis, setShowKeywordAnalysis] = useState(false)
  const [keywordAnalysisCompleted, setKeywordAnalysisCompleted] = useState(false)
  const [analyzedKeywords, setAnalyzedKeywords] = useState<string[]>([])
  const [selectedSkillsFromAnalysis, setSelectedSkillsFromAnalysis] = useState<string[]>([])
  
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

  // Webhook subscription for resume generation updates
  useEffect(() => {
    if (!resumeGenerationId) return

    console.log(`Setting up webhook subscription for resume generation: ${resumeGenerationId}`)
    const unsubscribe = webhookService.subscribeToEntity('resume_generation', resumeGenerationId.toString(), (event: WebhookEvent) => {
      console.log('Received resume generation webhook:', event)
      
      if (event.status === 'optimizing') {
        setGenerationStatus('optimizing')
        setGenerationMessage(event.data?.message || 'Optimizing resume content and structure...')
      } else if (event.status === 'finalizing') {
        setGenerationStatus('finalizing')
        setGenerationMessage(event.data?.message || 'Performing final checks and compilation...')
      } else if (event.status === 'complete') {
        setGenerationStatus('complete')
        setGenerationMessage(event.data?.message || 'Resume generation completed successfully!')
        
        // Fetch the completed resume
        fetchCompletedResume(resumeGenerationId)
        
        // Disconnect webhook on completion
        unsubscribe()
      } else if (event.status === 'failed') {
        setGenerationStatus('failed')
        setGenerationMessage(event.data?.error || 'Resume generation failed')
        setIsGenerating(false)
        
        // Disconnect webhook on failure
        unsubscribe()
      }
    })

    // Cleanup function to unsubscribe when component unmounts or generation ID changes
    return () => {
      console.log('Cleaning up webhook subscription for resume generation:', resumeGenerationId)
      unsubscribe()
    }
  }, [resumeGenerationId])

  const fetchCompletedResume = async (generationId: number, retryCount = 0) => {
    try {
      const result = await resumeService.getResumePdfBlob(generationId)
      
      // Set the resume version ID and create PDF URL
      setCurrentResumeVersionId(result.resumeVersionId)
      
      const url = URL.createObjectURL(result.pdfBlob)
      setPdfUrl(url)
      setViewMode('view') // Always start in view mode after generation
      setIsGenerating(false)
      
      // Scroll to PDF viewer
      setTimeout(() => {
        const pdfViewer = document.getElementById('pdf-viewer');
        if (pdfViewer) {
          pdfViewer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100)
    } catch (error) {
      console.error('Error fetching completed resume:', error)
      
      // If the error is "still in progress" and we haven't retried too many times, retry
      if (error instanceof Error && error.message.includes('still in progress') && retryCount < 3) {
        console.log(`Retrying PDF fetch (attempt ${retryCount + 1}/3)...`)
        setTimeout(() => {
          fetchCompletedResume(generationId, retryCount + 1)
        }, 2000) // Wait 2 seconds before retry
        return
      }
      
      // If it's not a "still in progress" error or we've retried too many times, show error
      setGenerationStatus('failed')
      setGenerationMessage(error instanceof Error ? error.message : 'Failed to retrieve completed resume')
      setIsGenerating(false)
    }
  }

  const handlePersonalInfoChange = (field: keyof PersonalInfo, value: string) => {
    setPersonalInfo(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const startResumeGeneration = () => {
    if (!jobTitle.trim() || !company.trim() || !jobDescription.trim()) {
      alert('Please provide job title, company, and job description')
      return
    }
    
    // Show keyword analysis step
    setShowKeywordAnalysis(true)
    
    // Scroll to keyword analysis section
    setTimeout(() => {
      const keywordSection = document.getElementById('keyword-analysis-section');
      if (keywordSection) {
        keywordSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100)
  }

  const generateResume = async () => {
    setIsGenerating(true)
    setGenerationStatus('')
    setGenerationMessage('')
    
    try {
      // Prepare resume data (only personal info and job details - backend fetches the rest)
      const data: ResumeDesignRequest = {
        personal_info: personalInfo,
        job_title: jobTitle,
        company: company,
        job_description: jobDescription,
        linked_application_id: selectedApplicationId,
        locale: userLocale
      }

      // Send resume design request using webhook-based service
      const result = await resumeService.sendResumeDesignRequest(data)
      
      // Set the resume generation ID for webhook tracking
      setResumeGenerationId(result.resumeVersionId)
      setGenerationStatus(result.status || 'processing')
      setGenerationMessage(result.message || 'Resume generation initiated.')

    } catch (error) {
      console.error('Error initiating resume generation:', error)
      setGenerationStatus('failed')
      setGenerationMessage(error instanceof Error ? error.message : 'Failed to initiate resume generation. Please try again.')
      setIsGenerating(false)
    }
  }

  const handleKeywordAnalysisComplete = (keywords: string[], selectedSkills: string[]) => {
    setKeywordAnalysisCompleted(true)
    setAnalyzedKeywords(keywords)
    setSelectedSkillsFromAnalysis(selectedSkills)
    generateResume()
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
      
      // Create user-friendly filename with Resume_ prefix
      const filenameParts = ['Resume']
      if (personalInfo.name) {
        const cleanName = personalInfo.name.replace(/[^a-z0-9\s-]/gi, '').replace(/\s+/g, '_')
        filenameParts.push(cleanName)
      }
      if (jobTitle) {
        const cleanTitle = jobTitle.replace(/[^a-z0-9\s-]/gi, '').replace(/\s+/g, '_')
        filenameParts.push(cleanTitle)
      }
      if (company) {
        const cleanCompany = company.replace(/[^a-z0-9\s-]/gi, '').replace(/\s+/g, '_')
        filenameParts.push(cleanCompany)
      }
      
      const filename = filenameParts.length > 1 
        ? `${filenameParts.join('_')}.pdf`
        : 'Resume.pdf'
      
      link.download = filename
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

  const fetchLatexContent = async () => {
    if (!currentResumeVersionId) return

    setIsLoadingLatex(true)
    try {
      const content = await resumeService.getLatexContent(currentResumeVersionId)
      setLatexContent(content)
    } catch (error) {
      console.error('Error fetching LaTeX content:', error)
      alert(error instanceof Error ? error.message : 'Failed to load LaTeX content. Please try again.')
    } finally {
      setIsLoadingLatex(false)
    }
  }

  const updateLatexContent = async () => {
    if (!currentResumeVersionId || !latexContent.trim()) return

    setIsUpdatingLatex(true)
    try {
      const pdfBlob = await resumeService.updateLatexContent(currentResumeVersionId, latexContent)
      
      // Update PDF with new content
      const url = URL.createObjectURL(pdfBlob)
      
      // Clean up old PDF URL
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl)
      }
      
      setPdfUrl(url)
      setViewMode('view') // Switch back to view mode after successful update
      
    } catch (error) {
      console.error('Error updating LaTeX content:', error)
      alert(error instanceof Error ? error.message : 'Failed to update resume. Please try again.')
    } finally {
      setIsUpdatingLatex(false)
    }
  }

  const handleViewModeChange = async (mode: 'view' | 'edit') => {
    if (mode === 'edit' && !latexContent && currentResumeVersionId) {
      // Fetch LaTeX content when switching to edit mode for the first time
      await fetchLatexContent()
    }
    setViewMode(mode)
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Resume Designer</h2>
        <p className="text-gray-600 text-lg">Create an AI-optimized resume tailored to your target job</p>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={personalInfo.location || ''}
                  onChange={(e) => handlePersonalInfoChange('location', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="City, State (optional)"
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
            {/* Professional Summary - Commented out for now */}
            {/* <div className="mt-4">
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
            </div> */}
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
          {!showKeywordAnalysis && !keywordAnalysisCompleted && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <button
                onClick={startResumeGeneration}
                disabled={isGenerating || !personalInfo.name || !personalInfo.email || !personalInfo.phone || !jobTitle.trim() || !company.trim() || !jobDescription.trim()}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Continue
              </button>
              <p className="text-sm text-gray-500 mt-2 text-center">
                AI will optimize your resume content, keywords, and structure for this specific job
              </p>
            </div>
          )}
        </div>

        {/* Preview Panel */}
        <div className="space-y-6" id="pdf-viewer">
          {/* Keyword Analysis Section */}
          {(showKeywordAnalysis || keywordAnalysisCompleted) && (
            <div id="keyword-analysis-section">
              <KeywordAnalysis
                jobDescription={jobDescription}
                onComplete={handleKeywordAnalysisComplete}
                isCompleted={keywordAnalysisCompleted}
                analyzedKeywords={analyzedKeywords}
                selectedSkills={selectedSkillsFromAnalysis}
              />
            </div>
          )}
          {pdfUrl ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Resume Preview</h2>
                <div className="flex items-center gap-4">
                  {/* Edit/View Mode Toggle */}
                  <div className="flex items-center bg-gray-100 rounded-lg p-1">
                    <button
                      onClick={() => handleViewModeChange('view')}
                      className={`px-4 py-2 rounded-md font-medium transition-colors ${
                        viewMode === 'view'
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-800'
                      }`}
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleViewModeChange('edit')}
                      disabled={!currentResumeVersionId}
                      className={`px-4 py-2 rounded-md font-medium transition-colors ${
                        viewMode === 'edit'
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed'
                      }`}
                    >
                      Edit
                    </button>
                  </div>
                  
                  <button
                    onClick={downloadResume}
                    className="bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                  >
                    Download PDF
                  </button>
                </div>
              </div>
              
              <div style={{ display: viewMode === 'view' ? 'block' : 'none' }}>
                <PDFViewer pdfUrl={pdfUrl} id="pdf-viewer" onReady={handlePdfViewerReady} />
              </div>
              
              {viewMode === 'edit' && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">LaTeX Editor</h3>
                    <button
                      onClick={updateLatexContent}
                      disabled={isUpdatingLatex || !latexContent.trim()}
                      className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isUpdatingLatex ? (
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Rendering...
                        </div>
                      ) : (
                        'Update & Render'
                      )}
                    </button>
                  </div>
                  
                  {isLoadingLatex ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="ml-3 text-gray-600">Loading LaTeX content...</span>
                    </div>
                  ) : (
                    <textarea
                      value={latexContent}
                      onChange={(e) => setLatexContent(e.target.value)}
                      className="w-full h-96 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder="LaTeX content will appear here..."
                      style={{ fontFamily: 'Monaco, Consolas, "Lucida Console", monospace' }}
                    />
                  )}
                  
                  <div className="mt-4 text-sm text-gray-600">
                    <p className="mb-2">
                      <strong>Tips:</strong>
                    </p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Edit the LaTeX code directly to customize your resume</li>
                      <li>Click "Update & Render" to compile your changes and generate a new PDF</li>
                      <li>Make sure to maintain proper LaTeX syntax to avoid compilation errors</li>
                      <li>The system will automatically switch back to View mode after successful rendering</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center py-12">
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {generationStatus === 'processing' ? 'Initiating Resume Generation' :
                       generationStatus === 'optimizing' ? 'Optimizing Resume' :
                       generationStatus === 'finalizing' ? 'Performing Final Checks' :
                       'Generating your optimized resume...'}
                    </h3>
                    <p className="text-gray-600">
                      {generationMessage || 'Please wait while we create your personalized resume'}
                    </p>
                    {generationStatus === 'failed' && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-700 text-sm">{generationMessage}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="text-gray-400 text-6xl mb-4">🎨</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {(showKeywordAnalysis || keywordAnalysisCompleted) ? 'Resume Ready to Generate' : 'No Resume Designed'}
                    </h3>
                    <p className="text-gray-600">
                      {(showKeywordAnalysis || keywordAnalysisCompleted) 
                        ? 'Finalize your keyword optimization to create optimized resume'
                        : 'Fill in your information and job description to create an optimized resume'
                      }
                    </p>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResumeDesigner

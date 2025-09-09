import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { experienceService } from '../../services/experienceService'
import { skillService } from '../../services/skills/skillService'
import { certificationService } from '../../services/certifications/certificationService'
import { publicationService } from '../../services/publications/publicationService'
import { applicationService } from '../../services/applications/applicationService'
import { profileService } from '../../services/profile/profileService'
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
  const [selectedTemplate, setSelectedTemplate] = useState('professional')
  const [jobDescription, setJobDescription] = useState(initialJobDescription || '')
  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(linkedApplicationId || null)

  // Fetch user data
  const { data: userProfile } = useQuery({
    queryKey: ['userProfile'],
    queryFn: profileService.getProfile
  })

  const { data: experiences } = useQuery({
    queryKey: ['experiences'],
    queryFn: experienceService.getExperiences
  })

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: skillService.getSkills
  })

  const { data: certifications } = useQuery({
    queryKey: ['certifications'],
    queryFn: certificationService.getCertifications
  })

  const { data: publications } = useQuery({
    queryKey: ['publications'],
    queryFn: publicationService.getPublications
  })

  const { data: applications } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationService.getApplications
  })

  // Mock education data - you might want to add this to your backend
  const education = [
    {
      institution: "University of Technology",
      degree: "Bachelor of Science",
      field_of_study: "Computer Science",
      graduation_date: "2020",
      location: "New York, NY",
      gpa: "3.8"
    }
  ]

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
    if (userProfile) {
      const fullName = userProfile.preferred_first_name 
        ? `${userProfile.preferred_first_name} ${userProfile.last_name}`
        : `${userProfile.first_name} ${userProfile.last_name}`
      
      setPersonalInfo({
        name: fullName,
        email: userProfile.email,
        phone: userProfile.phone || '',
        location: userProfile.location || '',
        linkedin: userProfile.linkedin_url || '',
        website: userProfile.website_url || '',
        summary: userProfile.professional_summary || ''
      })
    }
  }, [userProfile])

  // Load job description from linked application
  useEffect(() => {
    if (selectedApplicationId && applications) {
      const application = applications.find(app => app.id === selectedApplicationId)
      if (application && application.job_description) {
        setJobDescription(application.job_description)
      }
    }
  }, [selectedApplicationId, applications])

  const handlePersonalInfoChange = (field: keyof PersonalInfo, value: string) => {
    setPersonalInfo(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const generateResume = async () => {
    if (!experiences || !skills || !certifications || !publications) {
      alert('Please wait for data to load')
      return
    }

    if (!jobDescription.trim()) {
      alert('Please provide a job description or select an application')
      return
    }

    setIsGenerating(true)
    
    try {
      // Prepare resume data
      const data = {
        personal_info: personalInfo,
        work_experience: experiences,
        education: education,
        skills: skills.map(skill => skill.name),
        certifications: certifications,
        publications: publications,
        job_description: jobDescription,
        template: selectedTemplate,
        linked_application_id: selectedApplicationId
      }

      // Generate optimized resume using LLM
      const response = await api.post('/api/resume/design', data, {
        responseType: 'blob'
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      setPdfUrl(url)

    } catch (error) {
      console.error('Error generating resume:', error)
      alert('Failed to generate resume. Please try again.')
    } finally {
      setIsGenerating(false)
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
    if (application && application.job_description) {
      setJobDescription(application.job_description)
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Resume Designer</h1>
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
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Link to Existing Application (Optional)
                </label>
                <select
                  value={selectedApplicationId || ''}
                  onChange={(e) => handleApplicationSelect(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select an application...</option>
                  {applications.map(app => (
                    <option key={app.id} value={app.id}>
                      {app.job_title} at {app.company}
                    </option>
                  ))}
                </select>
              </div>
            )}

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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { id: 'professional', name: 'Professional', description: 'Clean, traditional layout' },
                { id: 'modern', name: 'Modern', description: 'Contemporary design' },
                { id: 'academic', name: 'Academic', description: 'Research-focused format' }
              ].map(template => (
                <div
                  key={template.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    selectedTemplate === template.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <h3 className="font-medium text-gray-900">{template.name}</h3>
                  <p className="text-sm text-gray-600">{template.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <button
              onClick={generateResume}
              disabled={isGenerating || !personalInfo.name || !personalInfo.email || !personalInfo.phone || !personalInfo.location || !jobDescription.trim()}
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
        <div className="space-y-6">
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
              <PDFViewer pdfUrl={pdfUrl} />
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

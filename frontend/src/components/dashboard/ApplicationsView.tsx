import React, { useState } from 'react'

interface Application {
  id: number
  jobTitle: string
  company: string
  appliedDate: string
  onlineAssessment: boolean
  interview: boolean
  rejected: boolean
  jobDescription: string
}

const ApplicationsView: React.FC = () => {
  // State for tracking which application is expanded
  const [expandedApplication, setExpandedApplication] = useState<number | null>(null)
  // State for new application modal
  const [isNewApplicationModalOpen, setIsNewApplicationModalOpen] = useState(false)
  const [newJobDescription, setNewJobDescription] = useState('')

  // Mock data - in a real app, this would come from an API
  const [recentApplications, setRecentApplications] = useState<Application[]>([
    {
      id: 1,
      jobTitle: 'Senior Software Engineer',
      company: 'TechCorp Inc.',
      appliedDate: '2024-01-15',
      onlineAssessment: true,
      interview: true,
      rejected: false,
      jobDescription: 'We are looking for a Senior Software Engineer to join our growing team. You will be responsible for designing and implementing scalable web applications using React, Node.js, and AWS. The ideal candidate has 5+ years of experience in full-stack development, strong problem-solving skills, and experience with microservices architecture. You will work closely with product managers and designers to deliver high-quality software solutions.'
    },
    {
      id: 2,
      jobTitle: 'Full Stack Developer',
      company: 'StartupXYZ',
      appliedDate: '2024-01-12',
      onlineAssessment: true,
      interview: false,
      rejected: true,
      jobDescription: 'Join our fast-paced startup as a Full Stack Developer! You will work on our core product using modern technologies like TypeScript, Next.js, and PostgreSQL. We are looking for someone who can wear multiple hats, from frontend development to database optimization. This is a great opportunity to grow with a company and have a significant impact on our product direction.'
    },
    {
      id: 3,
      jobTitle: 'Frontend Developer',
      company: 'DesignStudio',
      appliedDate: '2024-01-10',
      onlineAssessment: false,
      interview: false,
      rejected: false,
      jobDescription: 'We are seeking a creative Frontend Developer to join our design-focused team. You will be responsible for creating beautiful, responsive user interfaces using React, CSS-in-JS, and modern design systems. The ideal candidate has a strong eye for design, experience with animation libraries, and a passion for creating exceptional user experiences. You will collaborate closely with our design team to bring mockups to life.'
    },
    {
      id: 4,
      jobTitle: 'Backend Engineer',
      company: 'DataFlow Systems',
      appliedDate: '2024-01-08',
      onlineAssessment: true,
      interview: true,
      rejected: false,
      jobDescription: 'Join our backend team to build robust, scalable APIs and data processing systems. You will work with Python, Django, and cloud technologies to handle large-scale data processing. The ideal candidate has experience with database optimization, API design, and cloud infrastructure. You will be responsible for maintaining high availability and performance of our core services.'
    },
    {
      id: 5,
      jobTitle: 'DevOps Engineer',
      company: 'CloudTech',
      appliedDate: '2024-01-05',
      onlineAssessment: true,
      interview: false,
      rejected: true,
      jobDescription: 'We are looking for a DevOps Engineer to help us scale our infrastructure and improve our deployment processes. You will work with Docker, Kubernetes, AWS, and CI/CD pipelines to ensure reliable and efficient deployments. The ideal candidate has experience with infrastructure as code, monitoring systems, and automation. You will play a key role in improving our development workflow and system reliability.'
    }
  ])

  const handleStatusChange = (applicationId: number, statusType: keyof Pick<Application, 'onlineAssessment' | 'interview' | 'rejected'>) => {
    setRecentApplications(prevApplications =>
      prevApplications.map(app =>
        app.id === applicationId
          ? { ...app, [statusType]: !app[statusType] }
          : app
      )
    )
  }

  const handleToggleApplication = (applicationId: number) => {
    setExpandedApplication(expandedApplication === applicationId ? null : applicationId)
  }

  const handleOpenNewApplicationModal = () => {
    setIsNewApplicationModalOpen(true)
    setNewJobDescription('')
  }

  const handleCloseNewApplicationModal = () => {
    setIsNewApplicationModalOpen(false)
    setNewJobDescription('')
  }

  const handleCreateOptimizedResume = () => {
    // TODO: Implement resume optimization logic
    console.log('Creating optimized resume for job description:', newJobDescription)
    // For now, just close the modal
    handleCloseNewApplicationModal()
  }

  const handleAddToApplications = () => {
    // Create a new application with the job description
    const newApplication: Application = {
      id: Math.max(...recentApplications.map(app => app.id)) + 1,
      jobTitle: 'New Job Application', // This could be extracted from the job description
      company: 'Unknown Company', // This could be extracted from the job description
      appliedDate: new Date().toISOString().split('T')[0],
      onlineAssessment: false,
      interview: false,
      rejected: false,
      jobDescription: newJobDescription
    }

    // Add the new application to the list
    setRecentApplications(prevApplications => [newApplication, ...prevApplications])
    
    // Close the modal
    handleCloseNewApplicationModal()
  }

  // Calculate dynamic statistics based on current application data
  const calculateStats = () => {
    const totalApplications = recentApplications.length
    const onlineAssessments = recentApplications.filter(app => app.onlineAssessment).length
    const interviews = recentApplications.filter(app => app.interview).length
    const rejected = recentApplications.filter(app => app.rejected).length

    return {
      applicationsSubmitted: totalApplications,
      onlineAssessments,
      interviews,
      rejected
    }
  }

  const currentStats = calculateStats()

  const stats = [
    {
      title: 'Applications Submitted',
      value: currentStats.applicationsSubmitted,
      percentage: null,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      icon: '📝'
    },
    {
      title: 'Online Assessments',
      value: currentStats.onlineAssessments,
      percentage: currentStats.applicationsSubmitted > 0 
        ? Math.round((currentStats.onlineAssessments / currentStats.applicationsSubmitted) * 100)
        : 0,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      icon: '💻'
    },
    {
      title: 'Interviews',
      value: currentStats.interviews,
      percentage: currentStats.applicationsSubmitted > 0 
        ? Math.round((currentStats.interviews / currentStats.applicationsSubmitted) * 100)
        : 0,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      icon: '🎯'
    },
    {
      title: 'Rejected',
      value: currentStats.rejected,
      percentage: currentStats.applicationsSubmitted > 0 
        ? Math.round((currentStats.rejected / currentStats.applicationsSubmitted) * 100)
        : 0,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      icon: '❌'
    }
  ]

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Applications</h2>
      
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className={`${stat.bgColor} rounded-lg p-6 border border-gray-200`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
                <div className="flex items-baseline gap-2">
                  <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                  {stat.percentage !== null && (
                    <p className={`text-sm font-medium ${stat.color} opacity-75`}>
                      ({stat.percentage}%)
                    </p>
                  )}
                </div>
              </div>
              <div className="text-2xl">
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Applications List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Recent Applications</h3>
          <button
            onClick={handleOpenNewApplicationModal}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors duration-200"
          >
            New Application
          </button>
        </div>
        <div className="divide-y divide-gray-200">
          {recentApplications.map((application, index) => (
            <div key={index}>
              <div className="px-6 py-4 hover:bg-gray-50 transition-colors duration-200">
                {/* Desktop Layout */}
                <div className="hidden md:flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <h4 className="text-lg font-medium text-gray-900">{application.jobTitle}</h4>
                      <span className="text-sm text-gray-500">at</span>
                      <span className="text-lg font-medium text-gray-700">{application.company}</span>
                    </div>
                    
                    {/* Status Checkboxes */}
                    <div className="flex items-center gap-6 mb-3">
                      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application.onlineAssessment}
                          onChange={() => handleStatusChange(application.id, 'onlineAssessment')}
                          className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                        />
                        <span>Online Assessment</span>
                      </label>
                      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application.interview}
                          onChange={() => handleStatusChange(application.id, 'interview')}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span>Interview</span>
                      </label>
                      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application.rejected}
                          onChange={() => handleStatusChange(application.id, 'rejected')}
                          className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                        />
                        <span>Rejected</span>
                      </label>
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      Applied on {application.appliedDate}
                    </div>
                  </div>
                  
                  {/* Action Button - Desktop */}
                  <div className="flex items-center ml-6">
                    <button 
                      onClick={() => handleToggleApplication(application.id)}
                      className="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors duration-200"
                    >
                      {expandedApplication === application.id ? 'Hide Application' : 'Show Application'}
                    </button>
                  </div>
                </div>

                {/* Mobile Layout */}
                <div className="md:hidden">
                  <div className="mb-3">
                    <h4 className="text-lg font-medium text-gray-900 mb-1">{application.jobTitle}</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">at</span>
                      <span className="text-lg font-medium text-gray-700">{application.company}</span>
                    </div>
                  </div>
                  
                  {/* Status Checkboxes - Mobile */}
                  <div className="flex flex-wrap items-center gap-4 mb-3">
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={application.onlineAssessment}
                        onChange={() => handleStatusChange(application.id, 'onlineAssessment')}
                        className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                      />
                      <span>Assessment</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={application.interview}
                        onChange={() => handleStatusChange(application.id, 'interview')}
                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                      />
                      <span>Interview</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={application.rejected}
                        onChange={() => handleStatusChange(application.id, 'rejected')}
                        className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                      />
                      <span>Rejected</span>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      Applied on {application.appliedDate}
                    </div>
                    
                    {/* Action Button - Mobile */}
                    <button 
                      onClick={() => handleToggleApplication(application.id)}
                      className="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors duration-200"
                    >
                      {expandedApplication === application.id ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Expandable Job Description Section */}
              {expandedApplication === application.id && (
                <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
                  <h5 className="text-sm font-semibold text-gray-700 mb-3">Job Description</h5>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {application.jobDescription}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* New Application Modal */}
      {isNewApplicationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop with blur effect */}
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}
            onClick={handleCloseNewApplicationModal}
          />
          
          {/* Modal Content */}
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">New Job Application</h3>
              <button
                onClick={handleCloseNewApplicationModal}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="px-6 py-4 flex-1 overflow-y-auto">
              <div className="space-y-4">
                <div>
                  <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-700 mb-2">
                    Job Description
                  </label>
                  <textarea
                    id="jobDescription"
                    value={newJobDescription}
                    onChange={(e) => setNewJobDescription(e.target.value)}
                    placeholder="Paste the job description here..."
                    className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
                  />
                </div>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
              <button
                onClick={handleCloseNewApplicationModal}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
              >
                Cancel
              </button>
              <div className="flex gap-3">
                <button
                  onClick={handleAddToApplications}
                  disabled={!newJobDescription.trim()}
                  className="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 hover:bg-purple-100 disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed rounded-lg transition-colors duration-200"
                >
                  Add to Applications
                </button>
                <button
                  onClick={handleCreateOptimizedResume}
                  disabled={!newJobDescription.trim()}
                  className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-lg transition-colors duration-200"
                >
                  Create Optimized Resume
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ApplicationsView

import React, { useState, useEffect } from 'react'
import { applicationService } from '../../services/applications/applicationService'
import type { Application, ApplicationStats } from '../../services/applications/applicationService'

const ApplicationsView: React.FC = () => {
  // State for tracking which application is expanded
  const [expandedApplication, setExpandedApplication] = useState<number | null>(null)
  // State for new application modal
  const [isNewApplicationModalOpen, setIsNewApplicationModalOpen] = useState(false)
  const [newJobDescription, setNewJobDescription] = useState('')
  // State for applications data
  const [recentApplications, setRecentApplications] = useState<Application[]>([])
  const [stats, setStats] = useState<ApplicationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // State for delete confirmation
  const [deletingApplication, setDeletingApplication] = useState<Application | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  // Load applications and stats on component mount
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [applicationsData, statsData] = await Promise.all([
        applicationService.getApplications(),
        applicationService.getApplicationStats()
      ])
      setRecentApplications(applicationsData)
      setStats(statsData)
    } catch (err) {
      setError('Failed to load applications data')
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }


  const handleStatusChange = async (applicationId: number, statusType: 'online_assessment' | 'interview' | 'rejected') => {
    try {
      const application = recentApplications.find(app => app.id === applicationId)
      if (!application) return

      const updateData = {
        [statusType]: !application[statusType]
      }

      const updatedApplication = await applicationService.updateApplication(applicationId, updateData)
      
      setRecentApplications(prevApplications =>
        prevApplications.map(app =>
          app.id === applicationId ? updatedApplication : app
        )
      )

      // Reload stats after update
      const statsData = await applicationService.getApplicationStats()
      setStats(statsData)
    } catch (err) {
      console.error('Error updating application status:', err)
      setError('Failed to update application status')
    }
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

  // Delete application handlers
  const handleDeleteClick = (application: Application) => {
    setDeletingApplication(application)
    setIsDeleteModalOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!deletingApplication) return

    try {
      await applicationService.deleteApplication(deletingApplication.id)
      // Remove the deleted application from the local state
      setRecentApplications(prev => 
        prev.filter(app => app.id !== deletingApplication.id)
      )
      // Reload stats to update counts
      const statsData = await applicationService.getApplicationStats()
      setStats(statsData)
    } catch (err) {
      console.error('Error deleting application:', err)
      setError('Failed to delete application')
    } finally {
      setIsDeleteModalOpen(false)
      setDeletingApplication(null)
    }
  }

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false)
    setDeletingApplication(null)
  }

  const handleCreateOptimizedResume = () => {
    // TODO: Implement resume optimization logic
    console.log('Creating optimized resume for job description:', newJobDescription)
    // For now, just close the modal
    handleCloseNewApplicationModal()
  }

  const handleAddToApplications = async () => {
    try {
      // Create a new application with the job description
      const newApplicationData = {
        job_title: 'New Job Application', // This could be extracted from the job description
        company: 'Unknown Company', // This could be extracted from the job description
        job_description: newJobDescription,
        online_assessment: false,
        interview: false,
        rejected: false
      }

      const newApplication = await applicationService.createApplication(newApplicationData)
      
      // Add the new application to the list
      setRecentApplications(prevApplications => [newApplication, ...prevApplications])
      
      // Reload stats after adding
      const statsData = await applicationService.getApplicationStats()
      setStats(statsData)
      
      // Close the modal
      handleCloseNewApplicationModal()
    } catch (err) {
      console.error('Error creating application:', err)
      setError('Failed to create application')
    }
  }

  // Use API stats or fallback to calculated stats
  const currentStats = stats || {
    total_applications: recentApplications.length,
    online_assessments: recentApplications.filter(app => app.online_assessment).length,
    interviews: recentApplications.filter(app => app.interview).length,
    rejected: recentApplications.filter(app => app.rejected).length,
    online_assessment_rate: 0,
    interview_rate: 0,
    rejection_rate: 0
  }

  const statsDisplay = [
    {
      title: 'Applications Submitted',
      value: currentStats.total_applications,
      percentage: null,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      icon: '📝'
    },
    {
      title: 'Online Assessments',
      value: currentStats.online_assessments,
      percentage: currentStats.online_assessment_rate,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      icon: '💻'
    },
    {
      title: 'Interviews',
      value: currentStats.interviews,
      percentage: currentStats.interview_rate,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      icon: '🎯'
    },
    {
      title: 'Rejected',
      value: currentStats.rejected,
      percentage: currentStats.rejection_rate,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      icon: '❌'
    }
  ]

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Applications</h2>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading applications...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Applications</h2>
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Applications</h2>
      
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statsDisplay.map((stat, index) => (
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
                      <h4 className="text-lg font-medium text-gray-900">{application.job_title}</h4>
                      <span className="text-sm text-gray-500">at</span>
                      <span className="text-lg font-medium text-gray-700">{application.company}</span>
                    </div>
                    
                    {/* Status Checkboxes */}
                    <div className="flex items-center gap-6 mb-3">
                      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={application.online_assessment}
                          onChange={() => handleStatusChange(application.id, 'online_assessment')}
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
                      Applied on {new Date(application.applied_date).toLocaleDateString()}
                    </div>
                  </div>
                  
                  {/* Action Buttons - Desktop */}
                  <div className="flex items-center gap-2 ml-6">
                    <button 
                      onClick={() => handleToggleApplication(application.id)}
                      className="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors duration-200"
                    >
                      {expandedApplication === application.id ? 'Hide Application' : 'Show Application'}
                    </button>
                    <button 
                      onClick={() => handleDeleteClick(application)}
                      className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors duration-200"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Mobile Layout */}
                <div className="md:hidden">
                  <div className="mb-3">
                    <h4 className="text-lg font-medium text-gray-900 mb-1">{application.job_title}</h4>
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
                        checked={application.online_assessment}
                        onChange={() => handleStatusChange(application.id, 'online_assessment')}
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
                      Applied on {new Date(application.applied_date).toLocaleDateString()}
                    </div>
                    
                    {/* Action Buttons - Mobile */}
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleToggleApplication(application.id)}
                        className="px-4 py-2 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors duration-200"
                      >
                        {expandedApplication === application.id ? 'Hide' : 'Show'}
                      </button>
                      <button 
                        onClick={() => handleDeleteClick(application)}
                        className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors duration-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Expandable Job Description Section */}
              {expandedApplication === application.id && (
                <div className="bg-gray-50 border-t border-gray-200 px-6 py-4">
                  <h5 className="text-sm font-semibold text-gray-700 mb-3">Job Description</h5>
                  <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                    {application.job_description}
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

      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && deletingApplication && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={handleCancelDelete}
          />
          
          {/* Modal Content */}
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Application</h3>
                <p className="text-sm text-gray-500">This action cannot be undone</p>
              </div>
            </div>
            
            {/* Modal Body */}
            <div className="px-6 py-4">
              <p className="text-gray-700">
                Are you sure you want to delete the application for{' '}
                <span className="font-medium">{deletingApplication.job_title}</span> at{' '}
                <span className="font-medium">{deletingApplication.company}</span>?
              </p>
            </div>
            
            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={handleCancelDelete}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-red-600 rounded-lg hover:bg-red-700 transition-colors duration-200"
              >
                Delete Application
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ApplicationsView

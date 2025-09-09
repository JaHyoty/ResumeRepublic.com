import React, { useState, useEffect } from 'react'
import { useSearchParams, useLocation } from 'react-router-dom'
import {
  DashboardHeader,
  DashboardNavigation,
  ApplicationsView,
  ExperienceSkillsView
} from '../components/dashboard'
import ResumeDesigner from '../components/resume/ResumeDesigner'

const Dashboard: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const location = useLocation()
  const [activeView, setActiveView] = useState('applications')

  // Initialize active view from URL parameter
  useEffect(() => {
    const view = searchParams.get('view')
    if (view && (view === 'applications' || view === 'experience-skills' || view === 'resume')) {
      setActiveView(view)
    } else {
      // Default to applications if no valid view parameter
      setSearchParams({ view: 'applications' })
    }
  }, [searchParams, setSearchParams])

  const handleViewChange = (view: string) => {
    setActiveView(view)
    setSearchParams({ view })
  }

  const renderActiveView = () => {
    switch (activeView) {
      case 'applications':
        return <ApplicationsView />
      case 'experience-skills':
        return <ExperienceSkillsView />
      case 'resume':
        return <ResumeDesigner 
          linkedApplicationId={location.state?.applicationId}
          jobDescription={location.state?.jobDescription}
        />
      default:
        return <ApplicationsView />
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen w-screen" style={{ marginLeft: 'calc(50% - 50vw)', marginRight: 'calc(50% - 50vw)' }}>
      <DashboardHeader />
      <DashboardNavigation activeView={activeView} onViewChange={handleViewChange} />
      <main className="max-w-6xl mx-auto px-4">
        {renderActiveView()}
      </main>
    </div>
  )
}

export default Dashboard

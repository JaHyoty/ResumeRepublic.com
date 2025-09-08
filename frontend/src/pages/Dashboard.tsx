import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  DashboardHeader,
  DashboardNavigation,
  ApplicationsView,
  ExperienceSkillsView
} from '../components/dashboard'

const Dashboard: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeView, setActiveView] = useState('applications')

  // Initialize active view from URL parameter
  useEffect(() => {
    const view = searchParams.get('view')
    if (view && (view === 'applications' || view === 'experience-skills')) {
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
      default:
        return <ApplicationsView />
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen w-screen left-0 right-0" style={{ marginLeft: 'calc(50% - 50vw)' }}>
      <DashboardHeader />
      <DashboardNavigation activeView={activeView} onViewChange={handleViewChange} />
      <main className="max-w-6xl mx-auto">
        {renderActiveView()}
      </main>
    </div>
  )
}

export default Dashboard

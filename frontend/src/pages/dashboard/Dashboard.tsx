import React, { useState } from 'react'
import {
  DashboardHeader,
  DashboardNavigation,
  ApplicationsView,
  ResumesView,
  ExperienceSkillsView
} from '../../components/dashboard'

const Dashboard: React.FC = () => {
  const [activeView, setActiveView] = useState('applications')

  const renderActiveView = () => {
    switch (activeView) {
      case 'applications':
        return <ApplicationsView />
      case 'resumes':
        return <ResumesView />
      case 'experience-skills':
        return <ExperienceSkillsView />
      default:
        return <ApplicationsView />
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <DashboardHeader />
      <DashboardNavigation activeView={activeView} onViewChange={setActiveView} />
      <main className="max-w-6xl mx-auto">
        {renderActiveView()}
      </main>
    </div>
  )
}

export default Dashboard

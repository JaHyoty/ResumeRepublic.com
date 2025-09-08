import React, { useState } from 'react'
import {
  DashboardHeader,
  DashboardNavigation,
  ApplicationsView,
  ExperienceSkillsView
} from '../components/dashboard'

const Dashboard: React.FC = () => {
  const [activeView, setActiveView] = useState('applications')

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
      <DashboardNavigation activeView={activeView} onViewChange={setActiveView} />
      <main className="max-w-6xl mx-auto">
        {renderActiveView()}
      </main>
    </div>
  )
}

export default Dashboard

import React from 'react'

interface DashboardNavigationProps {
  activeView: string
  onViewChange: (view: string) => void
}

const DashboardNavigation: React.FC<DashboardNavigationProps> = ({ activeView, onViewChange }) => {
  const navigationItems = [
    { id: 'applications', label: 'Applications' },
    { id: 'resumes', label: 'Resumes' },
    { id: 'experience-skills', label: 'Experience and Skills Catalogue' }
  ]

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-center">
          <div className="flex space-x-8">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeView === item.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default DashboardNavigation

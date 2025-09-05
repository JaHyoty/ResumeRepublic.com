import React from 'react'

const ApplicationsView: React.FC = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Applications</h2>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Your job applications will be displayed here.</p>
        <div className="mt-4 text-sm text-gray-500">
          This section will show:
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Active job applications</li>
            <li>Application status tracking</li>
            <li>Interview schedules</li>
            <li>Application history</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default ApplicationsView

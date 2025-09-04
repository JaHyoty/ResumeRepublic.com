import React from 'react'

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-secondary-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Profile Completeness</h3>
          <p className="text-secondary-600">75% Complete</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Resume Versions</h3>
          <p className="text-secondary-600">3 Active</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">Recent Activity</h3>
          <p className="text-secondary-600">Last updated 2 days ago</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

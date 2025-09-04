import React from 'react'

const Resume: React.FC = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-secondary-900 mb-6">Resume Management</h1>
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Generate New Resume</h3>
          <p className="text-secondary-600 mb-4">Create a tailored resume for a specific job posting</p>
          <button className="btn-primary">Generate Resume</button>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Resume Versions</h3>
          <p className="text-secondary-600">No resume versions created yet</p>
        </div>
      </div>
    </div>
  )
}

export default Resume

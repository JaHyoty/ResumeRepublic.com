import React from 'react'

const ESC: React.FC = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-secondary-900 mb-6">Experience & Skills Catalog</h1>
      <div className="space-y-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Work Experience</h3>
          <p className="text-secondary-600">No experiences added yet</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Skills</h3>
          <p className="text-secondary-600">No skills added yet</p>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Tools & Technologies</h3>
          <p className="text-secondary-600">No tools added yet</p>
        </div>
      </div>
    </div>
  )
}

export default ESC

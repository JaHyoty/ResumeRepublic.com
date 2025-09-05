import React from 'react'

const ExperienceSkillsView: React.FC = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Experience and Skills Catalogue</h2>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Manage your professional experience and skills.</p>
        <div className="mt-4 text-sm text-gray-500">
          This section will show:
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Work experience entries</li>
            <li>Skills inventory</li>
            <li>Certifications and achievements</li>
            <li>Education history</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default ExperienceSkillsView

import React from 'react'

const ResumesView: React.FC = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Resumes</h2>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Your resume management center.</p>
        <div className="mt-4 text-sm text-gray-500">
          This section will show:
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Multiple resume versions</li>
            <li>Resume templates</li>
            <li>Resume analytics</li>
            <li>Download and sharing options</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default ResumesView

import React from 'react'
import { type Education } from '../../services/educationService'

interface EducationCardProps {
  education: Education
  onEdit: (education: Education) => void
  onDelete: (education: Education) => void
}

const EducationCard: React.FC<EducationCardProps> = ({
  education,
  onEdit,
  onDelete
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short'
    })
  }

  const formatDateRange = () => {
    const startDate = formatDate(education.start_date)
    const endDate = education.end_date ? formatDate(education.end_date) : 'Present'
    return `${startDate} - ${endDate}`
  }

  return (
    <div className="w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all">
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">
            {education.degree}{education.field_of_study && ` in ${education.field_of_study}`}
          </h4>
          <p className="text-sm text-gray-700 mt-1">
            {education.institution}
          </p>
          <div className="flex items-center mt-1">
            <p className="text-xs text-gray-500">
              {formatDateRange()}
              {education.gpa && ` • GPA: ${isNaN(parseFloat(education.gpa)) ? education.gpa : parseFloat(education.gpa).toFixed(2)}`}
            </p>
          </div>
        </div>
        <div className="flex space-x-1 ml-4">
          <button 
            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
            onClick={(e) => {
              e.stopPropagation()
              onEdit(education)
            }}
          >
            Edit
          </button>
          <button 
            className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(education)
            }}
          >
            Delete
          </button>
        </div>
      </div>
      
      {education.coursework && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-600">{education.coursework}</p>
        </div>
      )}
    </div>
  )
}

export default EducationCard

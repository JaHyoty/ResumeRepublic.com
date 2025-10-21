import React, { useState } from 'react'
import type { Project } from '../../services/projectService'

interface ProjectCardProps {
  project: Project
  onEdit: (project: Project) => void
  onDelete: (project: Project) => void
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onEdit, onDelete }) => {
  const [isSelected, setIsSelected] = useState(false)

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short'
    })
  }

  return (
    <div 
      className={`w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all cursor-pointer ${
        isSelected ? 'border-orange-300 bg-orange-50' : 'border-gray-200'
      }`}
      onClick={() => setIsSelected(!isSelected)}
    >
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h4 className="font-semibold text-gray-900">{project.name}</h4>
            {project.is_current && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Current
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {project.start_date ? formatDate(project.start_date) : 'Start date unknown'} - {project.is_current ? 'Present' : (project.end_date ? formatDate(project.end_date) : 'Present')}
          </p>
          {project.technologies_used && (
            <p className="text-xs text-gray-500 mt-1">
              Technologies: {project.technologies_used}
            </p>
          )}
        </div>
        <div className="flex space-x-1 ml-4">
          <button 
            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
            onClick={(e) => {
              e.stopPropagation()
              onEdit(project)
            }}
          >
            Edit
          </button>
          <button 
            className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(project)
            }}
          >
            Delete
          </button>
        </div>
      </div>
      
      {/* Expanded details */}
      {isSelected && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {project.role && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-900 mb-1">Role</h5>
              <p className="text-sm text-gray-600">{project.role}</p>
            </div>
          )}
          
          {project.description && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-900 mb-1">Description</h5>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{project.description}</p>
            </div>
          )}
          
          {project.url && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-900 mb-1">Project URL</h5>
              <a 
                href={project.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800"
                onClick={(e) => e.stopPropagation()}
              >
                {project.url} →
              </a>
            </div>
          )}
          
          {project.technologies_used && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Technologies Used</h5>
              <div className="flex flex-wrap gap-1">
                {project.technologies_used.split(',').map((tech, index) => (
                  <span 
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded text-xs bg-orange-100 text-orange-800"
                  >
                    {tech.trim().replace(/\(/g, ', ').replace(/\)/g, '')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ProjectCard
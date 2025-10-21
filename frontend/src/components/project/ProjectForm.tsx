import React, { useState, useEffect, useRef } from 'react'
import { projectService, type Project, type CreateProjectRequest } from '../../services/projectService'

interface ProjectFormData {
  name: string
  description?: string
  role?: string
  start_date?: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies_used?: string
}

interface ProjectFormProps {
  onSuccess: (data: any) => void
  onCancel: () => void
  initialData?: Project | null
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  onSuccess,
  onCancel,
  initialData
}) => {
  const projectNameInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    description: '',
    role: '',
    start_date: '',
    end_date: '',
    url: '',
    is_current: false,
    technologies_used: ''
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name,
        description: initialData.description || '',
        role: initialData.role || '',
        start_date: initialData.start_date || '',
        end_date: initialData.end_date || '',
        url: initialData.url || '',
        is_current: initialData.is_current,
        technologies_used: initialData.technologies_used || ''
      })
    } else {
      setFormData({
        name: '',
        description: '',
        role: '',
        start_date: '',
        end_date: '',
        url: '',
        is_current: false,
        technologies_used: ''
      })
    }
    setErrors({})
  }, [initialData])

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (projectNameInputRef.current) {
      projectNameInputRef.current.focus()
    }
  }, [])

  const handleInputChange = (field: keyof ProjectFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
    
    // Clear end_date when is_current is set to true
    if (field === 'is_current' && value === true) {
      setFormData(prev => ({
        ...prev,
        end_date: ''
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required'
    }

    // Start date is now optional

    if (!formData.is_current && !formData.end_date) {
      newErrors.end_date = 'End date is required for completed projects'
    }

    if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
      newErrors.end_date = 'End date must be after start date'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)

    try {
      const projectData: CreateProjectRequest = {
        name: formData.name.trim(),
        description: formData.description?.trim() || undefined,
        role: formData.role?.trim() || undefined,
        start_date: formData.start_date || undefined,
        end_date: formData.is_current ? undefined : formData.end_date,
        url: formData.url?.trim() || undefined,
        is_current: formData.is_current,
        technologies_used: formData.technologies_used?.trim() || undefined
      }

      if (initialData) {
        await projectService.updateProject(initialData.id!, projectData)
      } else {
        await projectService.createProject(projectData)
      }

      onSuccess(projectData)
      onCancel() // This closes the modal
    } catch (error) {
      console.error('Failed to save project:', error)
      alert('Failed to save project. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Project Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Project Name *
        </label>
        <input
          ref={projectNameInputRef}
          type="text"
          id="name"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Enter project name"
          disabled={isSubmitting}
        />
        {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
      </div>

      {/* Role */}
      <div>
        <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
          Role
        </label>
        <input
          type="text"
          id="role"
          value={formData.role}
          onChange={(e) => handleInputChange('role', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., Lead Developer, Project Manager, Full-stack Developer"
          disabled={isSubmitting}
        />
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={8}
          placeholder="Describe the project, its purpose, and key achievements"
          disabled={isSubmitting}
        />
        <p className="text-gray-500 text-sm mt-1">
          Include project details and key achievements
        </p>
      </div>

      {/* URL */}
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
          Project URL
        </label>
        <input
          type="url"
          id="url"
          value={formData.url}
          onChange={(e) => handleInputChange('url', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="https://example.com"
          disabled={isSubmitting}
        />
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            id="start_date"
            value={formData.start_date}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.start_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting}
          />
          {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
          <p className="text-gray-500 text-sm mt-1">Leave empty if start date is unknown</p>
        </div>

        <div>
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            id="end_date"
            value={formData.end_date}
            onChange={(e) => handleInputChange('end_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.end_date ? 'border-red-500' : 'border-gray-300'
            } ${formData.is_current ? 'bg-gray-100 text-gray-500 cursor-not-allowed' : ''}`}
            disabled={isSubmitting || formData.is_current}
          />
          {formData.is_current && (
            <p className="text-gray-500 text-sm mt-1">End date is not required for ongoing projects</p>
          )}
          {errors.end_date && <p className="text-red-500 text-sm mt-1">{errors.end_date}</p>}
        </div>
      </div>

      {/* Current Project Checkbox */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_current"
          checked={formData.is_current}
          onChange={(e) => handleInputChange('is_current', e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          disabled={isSubmitting}
        />
        <label htmlFor="is_current" className="ml-2 block text-sm text-gray-700">
          This is an ongoing project
        </label>
      </div>

      {/* Technologies Used */}
      <div>
        <label htmlFor="technologies_used" className="block text-sm font-medium text-gray-700 mb-1">
          Technologies Used
        </label>
        <input
          type="text"
          id="technologies_used"
          value={formData.technologies_used}
          onChange={(e) => handleInputChange('technologies_used', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="React, Python, AWS, Docker (comma-separated)"
          disabled={isSubmitting}
        />
        <p className="text-gray-500 text-sm mt-1">
          Enter technologies separated by commas (e.g., "React, Python, AWS, Docker")
        </p>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : (initialData ? 'Update Project' : 'Add Project')}
        </button>
      </div>
    </form>
  )
}

export default ProjectForm
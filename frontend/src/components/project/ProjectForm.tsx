import React, { useState, useEffect, useRef } from 'react'

interface ProjectTechnology {
  technology: string
}

interface ProjectAchievement {
  description: string
}

interface ProjectFormData {
  name: string
  description?: string
  start_date: string
  end_date?: string
  url?: string
  is_current: boolean
  technologies: ProjectTechnology[]
  achievements: ProjectAchievement[]
}

interface ProjectFormProps {
  onSubmit: (data: ProjectFormData) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
  initialData?: ProjectFormData
  mode?: 'create' | 'edit'
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData,
  mode = 'create'
}) => {
  const projectNameInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<ProjectFormData>(
    initialData || {
      name: '',
      description: '',
      start_date: '',
      end_date: '',
      url: '',
      is_current: false,
      technologies: [{ technology: '' }],
      achievements: [{ description: '' }]
    }
  )

  const [errors, setErrors] = useState<Record<string, string>>({})

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

  const handleTechnologyChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      technologies: prev.technologies.map((tech, i) => 
        i === index ? { ...tech, technology: value } : tech
      )
    }))
  }

  const addTechnology = () => {
    setFormData(prev => ({
      ...prev,
      technologies: [...prev.technologies, { technology: '' }]
    }))
  }

  const removeTechnology = (index: number) => {
    if (formData.technologies.length > 1) {
      setFormData(prev => ({
        ...prev,
        technologies: prev.technologies.filter((_, i) => i !== index)
      }))
    }
  }

  const handleAchievementChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      achievements: prev.achievements.map((achievement, i) => 
        i === index ? { ...achievement, description: value } : achievement
      )
    }))
  }

  const addAchievement = () => {
    setFormData(prev => ({
      ...prev,
      achievements: [...prev.achievements, { description: '' }]
    }))
  }

  const removeAchievement = (index: number) => {
    if (formData.achievements.length > 1) {
      setFormData(prev => ({
        ...prev,
        achievements: prev.achievements.filter((_, i) => i !== index)
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required'
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    if (!formData.is_current && !formData.end_date) {
      newErrors.end_date = 'End date is required for completed projects'
    }

    if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
      newErrors.end_date = 'End date must be after start date'
    }

    // Validate technologies
    const validTechnologies = formData.technologies.filter(tech => tech.technology.trim())
    if (validTechnologies.length === 0) {
      newErrors.technologies = 'At least one technology is required'
    }

    // Validate achievements
    const validAchievements = formData.achievements.filter(achievement => achievement.description.trim())
    if (validAchievements.length === 0) {
      newErrors.achievements = 'At least one achievement is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    // Filter out empty technologies and achievements
    const filteredTechnologies = formData.technologies.filter(tech => tech.technology.trim())
    const filteredAchievements = formData.achievements.filter(achievement => achievement.description.trim())
    
    const submitData = {
      ...formData,
      technologies: filteredTechnologies,
      achievements: filteredAchievements,
      end_date: formData.is_current ? undefined : formData.end_date
    }

    await onSubmit(submitData)
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
          disabled={isLoading}
        />
        {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
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
          rows={3}
          placeholder="Describe the project, its purpose, and your role"
          disabled={isLoading}
        />
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
          disabled={isLoading}
        />
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-1">
            Start Date *
          </label>
          <input
            type="date"
            id="start_date"
            value={formData.start_date}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.start_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isLoading}
          />
          {errors.start_date && <p className="text-red-500 text-sm mt-1">{errors.start_date}</p>}
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
            disabled={isLoading || formData.is_current}
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
          disabled={isLoading}
        />
        <label htmlFor="is_current" className="ml-2 block text-sm text-gray-700">
          This is an ongoing project
        </label>
      </div>

      {/* Technologies */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Technologies Used *
        </label>
        {formData.technologies.map((tech, index) => (
          <div key={index} className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={tech.technology}
              onChange={(e) => handleTechnologyChange(index, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., React, Python, AWS"
              disabled={isLoading}
            />
            {formData.technologies.length > 1 && (
              <button
                type="button"
                onClick={() => removeTechnology(index)}
                className="text-red-600 hover:text-red-800 p-1"
                disabled={isLoading}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addTechnology}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          disabled={isLoading}
        >
          + Add Technology
        </button>
        {errors.technologies && <p className="text-red-500 text-sm mt-1">{errors.technologies}</p>}
      </div>

      {/* Key Achievements */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Key Achievements *
        </label>
        {formData.achievements.map((achievement, index) => (
          <div key={index} className="flex items-start space-x-2 mb-2">
            <textarea
              value={achievement.description}
              onChange={(e) => handleAchievementChange(index, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Describe a key achievement or outcome from this project"
              disabled={isLoading}
            />
            {formData.achievements.length > 1 && (
              <button
                type="button"
                onClick={() => removeAchievement(index)}
                className="text-red-600 hover:text-red-800 p-1 mt-1"
                disabled={isLoading}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addAchievement}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          disabled={isLoading}
        >
          + Add Achievement
        </button>
        {errors.achievements && <p className="text-red-500 text-sm mt-1">{errors.achievements}</p>}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          disabled={isLoading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : mode === 'edit' ? 'Update Project' : 'Add Project'}
        </button>
      </div>
    </form>
  )
}

export default ProjectForm

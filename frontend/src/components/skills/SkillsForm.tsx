import React, { useState } from 'react'
import { type Skill, type CreateSkillRequest } from '../../services/skills/skillService'

interface SkillsFormData {
  name: string
}

interface SkillsFormProps {
  onSubmit: (data: CreateSkillRequest) => void
  onCancel: () => void
  isLoading?: boolean
  initialData?: Skill
  mode?: 'create' | 'edit'
}

const SkillsForm: React.FC<SkillsFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData,
  mode = 'create'
}) => {
  const [formData, setFormData] = useState<SkillsFormData>({
    name: initialData?.name || ''
  })

  const [errors, setErrors] = useState<Partial<Record<keyof SkillsFormData, string>>>({})

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof SkillsFormData, string>> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Skill name is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    const submitData: CreateSkillRequest = {
      name: formData.name.trim()
    }

    onSubmit(submitData)
  }

  const handleInputChange = (field: keyof SkillsFormData, value: string | number | undefined) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Skill Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
          Skill Name *
        </label>
        <input
          type="text"
          id="name"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., JavaScript, Python, Project Management, React, SQL"
          disabled={isLoading}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : mode === 'edit' ? 'Update Skill' : 'Add Skill'}
        </button>
      </div>
    </form>
  )
}

export default SkillsForm

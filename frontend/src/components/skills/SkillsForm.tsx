import React, { useState, useEffect, useRef } from 'react'
import { skillService, type Skill, type CreateSkillRequest } from '../../services/skillService'

interface SkillsFormData {
  name: string
}

interface SkillsFormProps {
  onSuccess: (data: any) => void
  onCancel: () => void
  initialData?: Skill
  mode?: 'create' | 'edit'
}

const SkillsForm: React.FC<SkillsFormProps> = ({
  onSuccess,
  onCancel,
  initialData,
  mode = 'create'
}) => {
  const skillNameInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<SkillsFormData>({
    name: initialData?.name || ''
  })

  const [errors, setErrors] = useState<Partial<Record<keyof SkillsFormData, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (skillNameInputRef.current) {
      skillNameInputRef.current.focus()
    }
  }, [])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof SkillsFormData, string>> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Skill name is required'
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
      const submitData: CreateSkillRequest = {
        name: formData.name.trim()
      }

      // Handle API calls internally
      if (mode === 'edit' && initialData?.id) {
        await skillService.updateSkill(initialData.id, submitData)
      } else {
        await skillService.createSkill(submitData)
      }

      onSuccess(submitData)
    } catch (error) {
      console.error('Failed to save skill:', error)
      alert('Failed to save skill. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
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
          ref={skillNameInputRef}
          type="text"
          id="name"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., JavaScript, Python, Project Management, React, SQL"
          disabled={isSubmitting}
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
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : mode === 'edit' ? 'Update Skill' : 'Add Skill'}
        </button>
      </div>
    </form>
  )
}

export default SkillsForm

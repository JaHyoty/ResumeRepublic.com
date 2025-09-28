import React, { useState, useEffect, useRef } from 'react'
import { educationService, type Education, type EducationCreate, type EducationUpdate } from '../../services/educationService'
import { useScrollPosition } from '../../hooks/useScrollPosition'

interface EducationFormProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (data: any) => void
  initialData?: Education | null
}

interface EducationFormData {
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string
  gpa: string
  description: string
  location: string
  website_url: string
}

const EducationForm: React.FC<EducationFormProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialData
}) => {
  const institutionInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<EducationFormData>({
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: '',
    gpa: '',
    description: '',
    location: '',
    website_url: ''
  })
  const [errors, setErrors] = useState<Partial<Record<keyof EducationFormData, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData({
        institution: initialData.institution,
        degree: initialData.degree,
        field_of_study: initialData.field_of_study || '',
        start_date: initialData.start_date,
        end_date: initialData.end_date || '',
        gpa: initialData.gpa || '',
        description: initialData.description || '',
        location: initialData.location || '',
        website_url: initialData.website_url || ''
      })
    } else {
      setFormData({
        institution: '',
        degree: '',
        field_of_study: '',
        start_date: '',
        end_date: '',
        gpa: '',
        description: '',
        location: '',
        website_url: ''
      })
    }
    setErrors({})
  }, [initialData, isOpen])

  // Use the scroll lock hook
  useScrollPosition(isOpen)

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (isOpen && institutionInputRef.current) {
      institutionInputRef.current.focus()
    }
  }, [isOpen])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof EducationFormData, string>> = {}

    if (!formData.institution.trim()) {
      newErrors.institution = 'Institution is required'
    }

    if (!formData.degree.trim()) {
      newErrors.degree = 'Degree is required'
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
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
      const educationData: EducationCreate | EducationUpdate = {
        institution: formData.institution.trim(),
        degree: formData.degree.trim(),
        field_of_study: formData.field_of_study.trim() || undefined,
        start_date: formData.start_date,
        end_date: formData.end_date || undefined,
        gpa: formData.gpa.trim() || undefined,
        description: formData.description.trim() || undefined,
        location: formData.location.trim() || undefined,
        website_url: formData.website_url.trim() || undefined
      }

      if (initialData) {
        await educationService.updateEducation(initialData.id, educationData as EducationUpdate)
      } else {
        await educationService.createEducation(educationData as EducationCreate)
      }

      onSuccess(educationData)
      onClose()
    } catch (error) {
      console.error('Failed to save education:', error)
      alert('Failed to save education. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: keyof EducationFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {initialData ? 'Edit Education' : 'Add Education'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Institution */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Institution *
              </label>
              <input
                ref={institutionInputRef}
                type="text"
                value={formData.institution}
                onChange={(e) => handleInputChange('institution', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.institution ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="University of Example"
              />
              {errors.institution && (
                <p className="text-red-500 text-xs mt-1">{errors.institution}</p>
              )}
            </div>

            {/* Degree */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Degree *
              </label>
              <input
                type="text"
                value={formData.degree}
                onChange={(e) => handleInputChange('degree', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.degree ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Bachelor of Science"
              />
              {errors.degree && (
                <p className="text-red-500 text-xs mt-1">{errors.degree}</p>
              )}
            </div>

            {/* Field of Study */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Field of Study
              </label>
              <input
                type="text"
                value={formData.field_of_study}
                onChange={(e) => handleInputChange('field_of_study', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Computer Science"
              />
            </div>

            {/* GPA */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                GPA
              </label>
              <input
                type="text"
                value={formData.gpa}
                onChange={(e) => handleInputChange('gpa', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="3.8/4.0"
              />
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date *
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => handleInputChange('start_date', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.start_date ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.start_date && (
                <p className="text-red-500 text-xs mt-1">{errors.start_date}</p>
              )}
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => handleInputChange('end_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="New York, NY"
              />
            </div>

            {/* Website URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Website URL
              </label>
              <input
                type="url"
                value={formData.website_url}
                onChange={(e) => handleInputChange('website_url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://university.edu"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Additional details about your education..."
            />
          </div>
        </form>
        
        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors duration-200"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isSubmitting ? 'Saving...' : (initialData ? 'Update Education' : 'Add Education')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default EducationForm

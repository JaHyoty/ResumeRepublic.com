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
  coursework: string
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
    coursework: ''
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
        coursework: initialData.coursework || ''
      })
    } else {
      setFormData({
        institution: '',
        degree: '',
        field_of_study: '',
        start_date: '',
        end_date: '',
        gpa: '',
        coursework: ''
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

    if (!formData.field_of_study.trim()) {
      newErrors.field_of_study = 'Field of study is required'
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    if (!formData.end_date) {
      newErrors.end_date = 'Graduation date is required'
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
        field_of_study: formData.field_of_study.trim(),
        start_date: formData.start_date,
        end_date: formData.end_date,
        gpa: formData.gpa.trim() || null,
        coursework: formData.coursework.trim() || null
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
                Field of Study *
              </label>
              <input
                type="text"
                value={formData.field_of_study}
                onChange={(e) => handleInputChange('field_of_study', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.field_of_study ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="E.g. Computer Science, Software Engineering, etc."
              />
              {errors.field_of_study && (
                <p className="text-red-500 text-xs mt-1">{errors.field_of_study}</p>
              )}
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
                placeholder="3.85/4.00 or First Class"
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

            {/* Graduation Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Graduation Date *
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => handleInputChange('end_date', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.end_date ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.end_date && (
                <p className="text-red-500 text-xs mt-1">{errors.end_date}</p>
              )}
            </div>

          </div>

          {/* Completed Coursework */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Completed Coursework
            </label>
            <textarea
              value={formData.coursework}
              onChange={(e) => handleInputChange('coursework', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="List relevant courses, projects, or academic achievements..."
            />
          </div>
          {/* Form Footer */}
          <div className="pt-4 border-t border-gray-200 flex justify-end space-x-3">
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
        </form>
      </div>
    </div>
  )
}

export default EducationForm

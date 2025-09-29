import React, { useState, useEffect, useRef } from 'react'

interface ExperienceTitle {
  title: string
  is_primary: boolean
}

interface ExperienceFormData {
  company: string
  location?: string | null
  start_date: string
  end_date?: string | null
  description?: string | null
  is_current: boolean
  titles: ExperienceTitle[]
}

interface ExperienceFormProps {
  onSubmit: (data: ExperienceFormData) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
  initialData?: ExperienceFormData
  mode?: 'create' | 'edit'
}

const ExperienceForm: React.FC<ExperienceFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData,
  mode = 'create'
}) => {
  const companyInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<ExperienceFormData>(
    initialData || {
      company: '',
      location: '',
      start_date: '',
      end_date: '',
      description: '',
      is_current: false,
      titles: [{ title: '', is_primary: true }]
    }
  )

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (companyInputRef.current) {
      companyInputRef.current.focus()
    }
  }, [])

  const handleInputChange = (field: keyof ExperienceFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleTitleChange = (index: number, field: keyof ExperienceTitle, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      titles: prev.titles.map((title, i) => 
        i === index ? { ...title, [field]: value } : title
      )
    }))
  }

  const addTitle = () => {
    setFormData(prev => ({
      ...prev,
      titles: [...prev.titles, { title: '', is_primary: false }]
    }))
  }

  const removeTitle = (index: number) => {
    if (formData.titles.length > 1) {
      setFormData(prev => ({
        ...prev,
        titles: prev.titles.filter((_, i) => i !== index)
      }))
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required'
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    if (!formData.is_current && !formData.end_date) {
      newErrors.end_date = 'End date is required for past positions'
    }

    if (formData.titles.some(title => !title.title.trim())) {
      newErrors.titles = 'All job titles must be filled'
    }


    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    // Prepare data
    const cleanedData = {
      ...formData,
      // Ensure dates are in YYYY-MM-DD format
      start_date: formData.start_date,
      end_date: formData.is_current ? null : formData.end_date || null,
      // Ensure location is not empty string
      location: formData.location?.trim() || null,
      // Ensure description is not empty string  
      description: formData.description?.trim() || null
    }

    try {
      await onSubmit(cleanedData)
    } catch (error) {
      console.error('Failed to submit experience:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Company and Location */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Company *
          </label>
          <input
            ref={companyInputRef}
            type="text"
            value={formData.company}
            onChange={(e) => handleInputChange('company', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.company ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter company name"
          />
          {errors.company && <p className="text-red-500 text-xs mt-1">{errors.company}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <input
            type="text"
            value={formData.location || ''}
            onChange={(e) => handleInputChange('location', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="City, State/Country"
          />
        </div>
      </div>

      {/* Dates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date *
          </label>
          <input
            type="date"
            value={formData.start_date}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.start_date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.start_date && <p className="text-red-500 text-xs mt-1">{errors.start_date}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={formData.end_date || ''}
            onChange={(e) => handleInputChange('end_date', e.target.value)}
            disabled={formData.is_current}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              formData.is_current ? 'bg-gray-100 cursor-not-allowed' : 'border-gray-300'
            } ${errors.end_date ? 'border-red-500' : ''}`}
          />
          {errors.end_date && <p className="text-red-500 text-xs mt-1">{errors.end_date}</p>}
        </div>
      </div>

      {/* Current Position Checkbox */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_current"
          checked={formData.is_current}
          onChange={(e) => {
            handleInputChange('is_current', e.target.checked)
            if (e.target.checked) {
              handleInputChange('end_date', '')
            }
          }}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="is_current" className="ml-2 block text-sm text-gray-700">
          I currently work here
        </label>
      </div>

      {/* Job Titles */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Titles *
        </label>
        {formData.titles.map((title, index) => (
          <div key={index} className="flex items-center space-x-2 mb-2">
            <input
              type="text"
              value={title.title}
              onChange={(e) => handleTitleChange(index, 'title', e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter job title"
            />
            <label className="flex items-center text-sm text-gray-600">
              <input
                type="radio"
                name="primary_title"
                checked={title.is_primary}
                onChange={() => {
                  setFormData(prev => ({
                    ...prev,
                    titles: prev.titles.map((t, i) => ({
                      ...t,
                      is_primary: i === index
                    }))
                  }))
                }}
                className="mr-1"
              />
              Primary
            </label>
            {formData.titles.length > 1 && (
              <button
                type="button"
                onClick={() => removeTitle(index)}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                Remove
              </button>
            )}
          </div>
        ))}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={addTitle}
            className="text-blue-500 hover:text-blue-700 text-sm"
          >
            + Add another title
          </button>
          <div className="relative group">
            <div className="w-4 h-4 bg-gray-400 text-white rounded-full flex items-center justify-center text-xs cursor-help">
              ?
            </div>
            <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none w-80 z-10">
              Sometimes it might be beneficial to indicate your job title in a way that matches the job description better. However, be mindful and do not lie about your previous work experiences :)
              <div className="absolute right-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-gray-800"></div>
            </div>
          </div>
        </div>
        {errors.titles && <p className="text-red-500 text-xs mt-1">{errors.titles}</p>}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          value={formData.description || ''}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe 2-6 key achievements and how you achieved them. Use action verbs and quantify results when possible (e.g., 'Increased sales by 25% by implementing new CRM system' or 'Led team of 5 developers to deliver project 2 weeks ahead of schedule')."
        />
        {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
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
          {isLoading ? (mode === 'edit' ? 'Updating...' : 'Saving...') : (mode === 'edit' ? 'Update Experience' : 'Save Experience')}
        </button>
      </div>
    </form>
  )
}

export default ExperienceForm

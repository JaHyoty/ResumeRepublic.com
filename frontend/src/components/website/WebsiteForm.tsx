import React, { useState, useEffect } from 'react'
import { createWebsite, updateWebsite, type Website, type WebsiteCreate, type WebsiteUpdate } from '../../services/website/websiteService'
import { useScrollPosition } from '../../hooks/useScrollPosition'

interface WebsiteFormProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (data: any) => void
  initialData?: Website | null
}

interface WebsiteFormData {
  site_name: string
  url: string
}

const WebsiteForm: React.FC<WebsiteFormProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialData
}) => {
  const [formData, setFormData] = useState<WebsiteFormData>({
    site_name: '',
    url: ''
  })
  const [errors, setErrors] = useState<Partial<Record<keyof WebsiteFormData, string>> & { general?: string }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData({
        site_name: initialData.site_name,
        url: initialData.url
      })
    } else {
      setFormData({
        site_name: '',
        url: ''
      })
    }
    setErrors({})
  }, [initialData, isOpen])

  // Use the scroll lock hook
  useScrollPosition(isOpen)

  const handleInputChange = (field: keyof WebsiteFormData, value: string) => {
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

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof WebsiteFormData, string>> = {}

    if (!formData.site_name.trim()) {
      newErrors.site_name = 'Site name is required'
    }

    if (!formData.url.trim()) {
      newErrors.url = 'URL is required'
    } else {
      // Basic URL validation
      try {
        new URL(formData.url)
      } catch {
        newErrors.url = 'Please enter a valid URL'
      }
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
      if (initialData) {
        // Update existing website
        const updateData: WebsiteUpdate = {
          site_name: formData.site_name.trim(),
          url: formData.url.trim()
        }
        await updateWebsite(initialData.id, updateData)
      } else {
        // Create new website
        const createData: WebsiteCreate = {
          site_name: formData.site_name.trim(),
          url: formData.url.trim()
        }
        await createWebsite(createData)
      }
      
      onSuccess(formData)
      onClose()
    } catch (error) {
      console.error('Error saving website:', error)
      setErrors({ general: 'Failed to save website. Please try again.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose()
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {initialData ? 'Edit Website' : 'Add Website'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.general && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {errors.general}
              </div>
            )}

            {/* Site Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Site Name *
              </label>
              <input
                type="text"
                value={formData.site_name}
                onChange={(e) => handleInputChange('site_name', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.site_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., My Portfolio, GitHub Profile"
                disabled={isSubmitting}
              />
              {errors.site_name && (
                <p className="text-red-500 text-xs mt-1">{errors.site_name}</p>
              )}
            </div>

            {/* URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL *
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => handleInputChange('url', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.url ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="https://example.com"
                disabled={isSubmitting}
              />
              {errors.url && (
                <p className="text-red-500 text-xs mt-1">{errors.url}</p>
              )}
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
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
                {isSubmitting ? 'Saving...' : (initialData ? 'Update' : 'Add')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default WebsiteForm

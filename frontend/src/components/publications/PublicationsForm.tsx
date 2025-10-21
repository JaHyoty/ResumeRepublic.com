import React, { useState, useEffect, useRef } from 'react'
import { publicationService, type Publication, type CreatePublicationRequest } from '../../services/publicationService'

interface PublicationsFormData {
  title: string
  authors?: string
  publisher?: string
  publication_date?: string
  url?: string
  description?: string
  publication_type?: string
}

interface PublicationsFormProps {
  onSuccess: (data: any) => void
  onCancel: () => void
  initialData?: Publication
  mode?: 'create' | 'edit'
}

const PublicationsForm: React.FC<PublicationsFormProps> = ({
  onSuccess,
  onCancel,
  initialData,
  mode = 'create'
}) => {
  const publicationTitleInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<PublicationsFormData>({
    title: initialData?.title || '',
    authors: initialData?.authors || '',
    publisher: initialData?.publisher || '',
    publication_date: initialData?.publication_date || '',
    url: initialData?.url || '',
    description: initialData?.description || '',
    publication_type: initialData?.publication_type || ''
  })

  const [errors, setErrors] = useState<Partial<Record<keyof PublicationsFormData, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (publicationTitleInputRef.current) {
      publicationTitleInputRef.current.focus()
    }
  }, [])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof PublicationsFormData, string>> = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Publication title is required'
    }

    // Date validation is handled by the native date input

    // Validate URL format if provided
    if (formData.url && formData.url.trim()) {
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
      const submitData: CreatePublicationRequest = {
        title: formData.title.trim(),
        authors: formData.authors?.trim() || null,
        publisher: formData.publisher?.trim() || null,
        publication_date: formData.publication_date?.trim() || null,
        url: formData.url?.trim() || null,
        description: formData.description?.trim() || null,
        publication_type: formData.publication_type?.trim() || null
      }

      // Handle API calls internally
      if (mode === 'edit' && initialData?.id) {
        await publicationService.updatePublication(initialData.id, submitData)
      } else {
        await publicationService.createPublication(submitData)
      }

      onSuccess(submitData)
    } catch (error) {
      console.error('Failed to save publication:', error)
      alert('Failed to save publication. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: keyof PublicationsFormData, value: string) => {
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

  const publicationTypes = [
    { value: '', label: 'Select type...' },
    { value: 'Journal', label: 'Journal Article' },
    { value: 'Conference', label: 'Conference Paper' },
    { value: 'Book', label: 'Book' },
    { value: 'Book Chapter', label: 'Book Chapter' },
    { value: 'Blog', label: 'Blog Post' },
    { value: 'Report', label: 'Technical Report' },
    { value: 'Thesis', label: 'Thesis/Dissertation' },
    { value: 'Other', label: 'Other' }
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Publication Title */}
        <div className="md:col-span-2">
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            Publication Title *
          </label>
          <input
            ref={publicationTitleInputRef}
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.title ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="e.g., Machine Learning Applications in Healthcare"
            disabled={isSubmitting}
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title}</p>
          )}
        </div>

        {/* Author(s) */}
        <div>
          <label htmlFor="authors" className="block text-sm font-medium text-gray-700 mb-2">
            Author(s)
          </label>
          <input
            type="text"
            id="authors"
            value={formData.authors}
            onChange={(e) => handleInputChange('authors', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., John Doe, Jane Smith"
            disabled={isSubmitting}
          />
        </div>

        {/* Publisher */}
        <div>
          <label htmlFor="publisher" className="block text-sm font-medium text-gray-700 mb-2">
            Publisher
          </label>
          <input
            type="text"
            id="publisher"
            value={formData.publisher}
            onChange={(e) => handleInputChange('publisher', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Nature, IEEE, ACM, Springer"
            disabled={isSubmitting}
          />
        </div>

        {/* Publication Type */}
        <div>
          <label htmlFor="publication_type" className="block text-sm font-medium text-gray-700 mb-2">
            Publication Type
          </label>
          <select
            id="publication_type"
            value={formData.publication_type}
            onChange={(e) => handleInputChange('publication_type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isSubmitting}
          >
            {publicationTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Publication Date */}
        <div>
          <label htmlFor="publication_date" className="block text-sm font-medium text-gray-700 mb-2">
            Publication Date
          </label>
          <input
            type="date"
            id="publication_date"
            value={formData.publication_date}
            onChange={(e) => handleInputChange('publication_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.publication_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting}
          />
          {errors.publication_date && (
            <p className="mt-1 text-sm text-red-600">{errors.publication_date}</p>
          )}
        </div>

        {/* URL */}
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            URL
          </label>
          <input
            type="url"
            id="url"
            value={formData.url}
            onChange={(e) => handleInputChange('url', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.url ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="https://example.com/publication"
            disabled={isSubmitting}
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600">{errors.url}</p>
          )}
        </div>

        {/* Description */}
        <div className="md:col-span-2">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Brief description of the publication..."
            disabled={isSubmitting}
          />
        </div>
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
          {isSubmitting ? 'Saving...' : mode === 'edit' ? 'Update Publication' : 'Add Publication'}
        </button>
      </div>
    </form>
  )
}

export default PublicationsForm

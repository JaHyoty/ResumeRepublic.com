import React, { useState, useEffect, useRef } from 'react'
import { certificationService, type Certification, type CreateCertificationRequest } from '../../services/certificationService'

interface CertificationsFormData {
  name: string
  issuer: string
  issue_date: string
  expiry_date?: string
  credential_id?: string
  credential_url?: string
}

interface CertificationsFormProps {
  onSuccess: (data: any) => void
  onCancel: () => void
  initialData?: Certification
  mode?: 'create' | 'edit'
}

const CertificationsForm: React.FC<CertificationsFormProps> = ({
  onSuccess,
  onCancel,
  initialData,
  mode = 'create'
}) => {
  const certificationNameInputRef = useRef<HTMLInputElement>(null)
  
  const [formData, setFormData] = useState<CertificationsFormData>({
    name: initialData?.name || '',
    issuer: initialData?.issuer || '',
    issue_date: initialData?.issue_date || '',
    expiry_date: initialData?.expiry_date || '',
    credential_id: initialData?.credential_id || '',
    credential_url: initialData?.credential_url || ''
  })

  const [errors, setErrors] = useState<Partial<Record<keyof CertificationsFormData, string>>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Auto-focus the first input field when component mounts
  useEffect(() => {
    if (certificationNameInputRef.current) {
      certificationNameInputRef.current.focus()
    }
  }, [])

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof CertificationsFormData, string>> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Certification name is required'
    }

    if (!formData.issuer.trim()) {
      newErrors.issuer = 'Issuer is required'
    }

    if (!formData.issue_date.trim()) {
      newErrors.issue_date = 'Issue date is required'
    }

    // Date validation is handled by the native date input

    // Validate URL format if provided
    if (formData.credential_url && formData.credential_url.trim()) {
      try {
        new URL(formData.credential_url)
      } catch {
        newErrors.credential_url = 'Please enter a valid URL'
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
      const submitData: CreateCertificationRequest = {
        name: formData.name.trim(),
        issuer: formData.issuer.trim(),
        issue_date: formData.issue_date.trim(),
        expiry_date: formData.expiry_date?.trim() || null,
        credential_id: formData.credential_id?.trim() || null,
        credential_url: formData.credential_url?.trim() || null
      }

      // Handle API calls internally
      if (mode === 'edit' && initialData?.id) {
        await certificationService.updateCertification(initialData.id, submitData)
      } else {
        await certificationService.createCertification(submitData)
      }

      onSuccess(submitData)
    } catch (error) {
      console.error('Failed to save certification:', error)
      alert('Failed to save certification. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: keyof CertificationsFormData, value: string) => {
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Certification Name */}
        <div className="md:col-span-2">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Certification Name *
          </label>
          <input
            ref={certificationNameInputRef}
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="e.g., Certified Solutions Architect"
            disabled={isSubmitting}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name}</p>
          )}
        </div>

        {/* Issuer */}
        <div>
          <label htmlFor="issuer" className="block text-sm font-medium text-gray-700 mb-2">
            Issuer *
          </label>
          <input
            type="text"
            id="issuer"
            value={formData.issuer}
            onChange={(e) => handleInputChange('issuer', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.issuer ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="e.g., AWS"
            disabled={isSubmitting}
          />
          {errors.issuer && (
            <p className="mt-1 text-sm text-red-600">{errors.issuer}</p>
          )}
        </div>

        {/* Issue Date */}
        <div>
          <label htmlFor="issue_date" className="block text-sm font-medium text-gray-700 mb-2">
            Issue Date *
          </label>
          <input
            type="date"
            id="issue_date"
            value={formData.issue_date}
            onChange={(e) => handleInputChange('issue_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.issue_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting}
          />
          {errors.issue_date && (
            <p className="mt-1 text-sm text-red-600">{errors.issue_date}</p>
          )}
        </div>

        {/* Expiry Date */}
        <div>
          <label htmlFor="expiry_date" className="block text-sm font-medium text-gray-700 mb-2">
            Expiry Date
          </label>
          <input
            type="date"
            id="expiry_date"
            value={formData.expiry_date}
            onChange={(e) => handleInputChange('expiry_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.expiry_date ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={isSubmitting}
          />
          {errors.expiry_date && (
            <p className="mt-1 text-sm text-red-600">{errors.expiry_date}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">Leave empty if the certification doesn't expire</p>
        </div>

        {/* Credential ID */}
        <div>
          <label htmlFor="credential_id" className="block text-sm font-medium text-gray-700 mb-2">
            Credential ID
          </label>
          <input
            type="text"
            id="credential_id"
            value={formData.credential_id}
            onChange={(e) => handleInputChange('credential_id', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., AWS123456789"
            disabled={isSubmitting}
          />
        </div>

        {/* Credential URL */}
        <div>
          <label htmlFor="credential_url" className="block text-sm font-medium text-gray-700 mb-2">
            Credential URL
          </label>
          <input
            type="url"
            id="credential_url"
            value={formData.credential_url}
            onChange={(e) => handleInputChange('credential_url', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.credential_url ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="https://www.credly.com/badges/..."
            disabled={isSubmitting}
          />
          {errors.credential_url && (
            <p className="mt-1 text-sm text-red-600">{errors.credential_url}</p>
          )}
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
          {isSubmitting ? 'Saving...' : mode === 'edit' ? 'Update Certification' : 'Add Certification'}
        </button>
      </div>
    </form>
  )
}

export default CertificationsForm

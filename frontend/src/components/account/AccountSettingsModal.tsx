import { useEnhancedClickOutside } from '../../hooks/useEnhancedClickOutside'
import React, { useState, useEffect } from 'react'
import { useScrollPosition } from '../../hooks/useScrollPosition'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userService, type UserInfo } from '../../services/userService'
import DeleteAccountModal from './DeleteAccountModal'

interface AccountSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

const AccountSettingsModal: React.FC<AccountSettingsModalProps> = ({
  isOpen,
  onClose
}) => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    preferred_first_name: '',
    phone: '',
    location: '',
    linkedin_url: '',
    website_url: '',
    professional_summary: ''
  })
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const queryClient = useQueryClient()

  // Use the scroll position hook
  useScrollPosition(isOpen)

  // Fetch user information
  const { data: userProfile, isLoading } = useQuery<UserInfo>({
    queryKey: ['userInfo'],
    queryFn: userService.getUserInfo,
    enabled: isOpen
  })

  // Update user information mutation
  const updateUserMutation = useMutation({
    mutationFn: userService.updateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userInfo'] })
      queryClient.invalidateQueries({ queryKey: ['user'] })
      onClose()
    },
    onError: (error) => {
      console.error('Failed to update user:', error)
    }
  })

  // Update form data when user profile loads
  useEffect(() => {
    if (userProfile) {
      setFormData({
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        preferred_first_name: userProfile.preferred_first_name || '',
        phone: userProfile.phone || '',
        location: userProfile.location || '',
        linkedin_url: userProfile.linkedin_url || '',
        website_url: userProfile.website_url || '',
        professional_summary: userProfile.professional_summary || ''
      })
    }
  }, [userProfile])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateUserMutation.mutate(formData)
  }

  // Use enhanced click outside functionality
  const { handleBackdropMouseDown, handleBackdropMouseUp } = useEnhancedClickOutside(onClose)

  if (!isOpen) {
    return null
  }

  return (
    <div 
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onMouseDown={handleBackdropMouseDown}
      onMouseUp={handleBackdropMouseUp}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              Account Settings
            </h2>
            <button
              onClick={onClose}
              disabled={updateUserMutation.isPending}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Personal Information */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name *
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name *
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="preferred_first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Preferred First Name
                    </label>
                    <input
                      type="text"
                      id="preferred_first_name"
                      name="preferred_first_name"
                      value={formData.preferred_first_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <input
                      type="text"
                      id="location"
                      name="location"
                      value={formData.location}
                      onChange={handleInputChange}
                      placeholder="e.g., San Francisco, CA"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Professional Information */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Professional Information</h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="linkedin_url" className="block text-sm font-medium text-gray-700 mb-1">
                      LinkedIn URL
                    </label>
                    <input
                      type="url"
                      id="linkedin_url"
                      name="linkedin_url"
                      value={formData.linkedin_url}
                      onChange={handleInputChange}
                      placeholder="https://linkedin.com/in/yourprofile"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="website_url" className="block text-sm font-medium text-gray-700 mb-1">
                      Personal Website URL
                    </label>
                    <input
                      type="url"
                      id="website_url"
                      name="website_url"
                      value={formData.website_url}
                      onChange={handleInputChange}
                      placeholder="https://yourwebsite.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  {/* Professional Summary - Commented out for now */}
                  {/* <div>
                    <label htmlFor="professional_summary" className="block text-sm font-medium text-gray-700 mb-1">
                      Professional Summary
                    </label>
                    <textarea
                      id="professional_summary"
                      name="professional_summary"
                      value={formData.professional_summary}
                      onChange={handleInputChange}
                      rows={4}
                      placeholder="Brief summary of your professional background and expertise..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    />
                  </div> */}
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex justify-between items-center pt-6 border-t border-gray-200">
                {/* Delete Account Button - Bottom Left */}
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(true)}
                  disabled={updateUserMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  Delete Account
                </button>

                {/* Save/Cancel Buttons - Bottom Right */}
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={updateUserMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={updateUserMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                  >
                    {updateUserMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Delete Account Confirmation Modal */}
      <DeleteAccountModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onAccountDeleted={() => {
          setShowDeleteModal(false)
          onClose()
        }}
      />
    </div>
  )
}

export default AccountSettingsModal

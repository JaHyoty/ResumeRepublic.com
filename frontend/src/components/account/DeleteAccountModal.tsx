import React, { useState } from 'react'
import { useScrollPosition } from '../../hooks/useScrollPosition'
import { useEnhancedClickOutside } from '../../hooks/useEnhancedClickOutside'
import { useMutation } from '@tanstack/react-query'
import { userService } from '../../services/userService'
import { useAuth } from '../../contexts/AuthContext'

interface DeleteAccountModalProps {
  isOpen: boolean
  onClose: () => void
  onAccountDeleted: () => void
}

const DeleteAccountModal: React.FC<DeleteAccountModalProps> = ({
  isOpen,
  onClose,
  onAccountDeleted
}) => {
  const [isDeleting, setIsDeleting] = useState(false)
  const { logout } = useAuth()

  // Use the scroll lock hook
  useScrollPosition(isOpen)
  
  // Use enhanced click outside functionality
  const { handleBackdropMouseDown, handleBackdropMouseUp } = useEnhancedClickOutside(onClose)

  // Delete account mutation
  const deleteAccountMutation = useMutation({
    mutationFn: userService.deleteUser,
    onSuccess: () => {
      setIsDeleting(false)
      logout()
      onAccountDeleted()
    },
    onError: (error) => {
      console.error('Failed to delete account:', error)
      setIsDeleting(false)
    }
  })

  const handleDelete = async () => {
    setIsDeleting(true)
    deleteAccountMutation.mutate()
  }

  if (!isOpen) {
    return null
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-[60]"
      onMouseDown={handleBackdropMouseDown}
      onMouseUp={handleBackdropMouseUp}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Delete Account
              </h3>
              <p className="text-sm text-gray-500">
                This action cannot be undone
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-red-800">
                    Warning: This will permanently delete your account
                  </h4>
                  <div className="mt-2 text-sm text-red-700">
                    <ul className="list-disc list-inside space-y-1">
                      <li>All your personal information will be deleted</li>
                      <li>All your resumes and applications will be deleted</li>
                      <li>All files stored in our system will be removed</li>
                      <li>This action cannot be undone</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-600">
                Are you sure you want to permanently delete your account? This action cannot be undone.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Deleting...</span>
              </div>
            ) : (
              'Delete Account'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default DeleteAccountModal

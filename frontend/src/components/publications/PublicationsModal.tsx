import React from 'react'
import PublicationsForm from './PublicationsForm'
import { type Publication, type CreatePublicationRequest } from '../../services/publications/publicationService'

interface PublicationsModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreatePublicationRequest) => void
  isLoading?: boolean
  initialData?: Publication
  mode?: 'create' | 'edit'
}

const PublicationsModal: React.FC<PublicationsModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  initialData,
  mode = 'create'
}) => {
  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'edit' ? 'Edit Publication' : 'Add New Publication'}
            </h2>
            <button
              onClick={onClose}
              disabled={isLoading}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <PublicationsForm
            onSubmit={onSubmit}
            onCancel={onClose}
            isLoading={isLoading}
            initialData={initialData}
            mode={mode}
          />
        </div>
      </div>
    </div>
  )
}

export default PublicationsModal

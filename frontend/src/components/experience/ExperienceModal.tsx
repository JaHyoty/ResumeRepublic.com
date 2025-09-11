import React from 'react'
import { useScrollPosition } from '../../hooks/useScrollPosition'
import { useEnhancedClickOutside } from '../../hooks/useEnhancedClickOutside'
import ExperienceForm from './ExperienceForm'

interface ExperienceModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: any) => Promise<void>
  isLoading?: boolean
  initialData?: any
  mode?: 'create' | 'edit'
}

const ExperienceModal: React.FC<ExperienceModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  initialData,
  mode = 'create'
}) => {
  // Use the scroll lock hook
  useScrollPosition(isOpen)
  
  // Use enhanced click outside functionality
  const { handleBackdropMouseDown, handleBackdropMouseUp } = useEnhancedClickOutside(onClose)

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onMouseDown={handleBackdropMouseDown}
      onMouseUp={handleBackdropMouseUp}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'edit' ? 'Edit Work Experience' : 'Add Work Experience'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isLoading}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <ExperienceForm
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

export default ExperienceModal

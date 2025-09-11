import { useState } from 'react'

export const useEnhancedClickOutside = (onClose: () => void) => {
  const [mouseDownOutside, setMouseDownOutside] = useState(false)

  const handleBackdropMouseDown = (e: React.MouseEvent) => {
    // Check if the click is on the backdrop (not on modal content)
    if (e.target === e.currentTarget) {
      setMouseDownOutside(true)
    } else {
      setMouseDownOutside(false)
    }
  }

  const handleBackdropMouseUp = (e: React.MouseEvent) => {
    // Only close if both mousedown and mouseup were outside the modal
    if (mouseDownOutside && e.target === e.currentTarget) {
      onClose()
    }
    setMouseDownOutside(false)
  }

  return {
    handleBackdropMouseDown,
    handleBackdropMouseUp
  }
}

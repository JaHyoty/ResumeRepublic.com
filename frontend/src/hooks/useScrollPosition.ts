import { useEffect, useRef } from 'react'
import { saveScrollPosition, restoreScrollPosition } from '../utils/scrollRestore'

export const useScrollPosition = (isOpen: boolean) => {
  const isModalOpenRef = useRef<boolean>(false)

  useEffect(() => {
    if (isOpen && !isModalOpenRef.current) {
      // Save scroll position when modal opens
      saveScrollPosition()
      isModalOpenRef.current = true
      
      // Prevent scrolling immediately
      document.body.style.position = 'fixed'
      document.body.style.top = `-${window.scrollY}px`
      document.body.style.left = '0'
      document.body.style.right = '0'
      document.body.style.width = '100%'
      document.body.style.height = '100%'
      document.body.classList.add('modal-open')
    } else if (!isOpen && isModalOpenRef.current) {
      // Remove styles and restore scroll position
      isModalOpenRef.current = false
      
      // Remove all styles
      document.body.style.position = ''
      document.body.style.top = ''
      document.body.style.left = ''
      document.body.style.right = ''
      document.body.style.width = ''
      document.body.style.height = ''
      document.body.classList.remove('modal-open')
      
      // Restore scroll position
      restoreScrollPosition()
    }
  }, [isOpen])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isModalOpenRef.current) {
        isModalOpenRef.current = false
        document.body.style.position = ''
        document.body.style.top = ''
        document.body.style.left = ''
        document.body.style.right = ''
        document.body.style.width = ''
        document.body.style.height = ''
        document.body.classList.remove('modal-open')
        restoreScrollPosition()
      }
    }
  }, [])
}

// Global scroll position manager
let savedScrollPosition = 0
let isModalOpen = false

export const saveScrollPosition = () => {
  if (!isModalOpen) {
    // Try to get the globally stored scroll position first
    const globalScrollPosition = (window as any).__savedScrollPosition
    if (globalScrollPosition !== undefined) {
      savedScrollPosition = globalScrollPosition
      // Clear it after using
      delete (window as any).__savedScrollPosition
    } else {
      savedScrollPosition = window.scrollY
    }
    isModalOpen = true
  }
}

export const restoreScrollPosition = () => {
  if (isModalOpen) {
    isModalOpen = false
    
    // Try multiple times to ensure it works
    const restore = () => {
      window.scrollTo(0, savedScrollPosition)
    }
    
    // Immediate restore
    restore()
    
    // Restore after a short delay
    setTimeout(restore, 0)
    
    // Restore after a longer delay
    setTimeout(restore, 10)
    
    // Restore after DOM updates
    requestAnimationFrame(restore)
  }
}

export const getSavedScrollPosition = () => savedScrollPosition
export const isScrollSaved = () => isModalOpen

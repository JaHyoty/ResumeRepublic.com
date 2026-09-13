import React from 'react'
import { APP_NAME } from '../../config/constants'

const Footer: React.FC = () => {
  return (
    <footer 
      className="bg-gray-900 text-gray-400 py-6 w-screen left-0 right-0 overflow-hidden border-t border-gray-800 text-sm" 
      style={{ marginLeft: 'calc(50% - 50vw)' }}
      role="contentinfo"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs sm:text-sm">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">{APP_NAME}</span>
          <span>&copy; {new Date().getFullYear()} All rights reserved.</span>
        </div>
        <div>
          <a 
            href="/privacy-policy.html" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-400 hover:text-white transition-colors"
          >
            Privacy Policy
          </a>
        </div>
      </div>
    </footer>
  )
}

export default Footer

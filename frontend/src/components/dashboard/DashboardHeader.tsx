import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { APP_NAME } from '../../config/constants'
import AccountSettingsModal from '../account/AccountSettingsModal'

const DashboardHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleAccountClick = () => {
    setIsAccountModalOpen(true)
    setIsDropdownOpen(false)
  }

  const handleLogoutClick = () => {
    handleLogout()
    setIsDropdownOpen(false)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <header className="bg-white sticky top-0 z-40 w-screen left-0 right-0" style={{ marginLeft: 'calc(50% - 50vw)' }}>
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex justify-between items-center py-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-purple-800 bg-clip-text text-transparent">
            {APP_NAME}
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 hidden sm:block">
              Welcome, {user?.preferred_first_name || user?.first_name}!
            </span>
            
            {/* Desktop buttons - hidden on small screens */}
            <div className="hidden sm:flex items-center gap-4">
              <button
                onClick={handleAccountClick}
                className="text-gray-600 hover:text-gray-800 font-medium text-sm transition-colors duration-200"
              >
                Account
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-800 font-medium text-sm transition-colors duration-200"
              >
                Logout
              </button>
            </div>

            {/* Mobile dropdown menu - visible on small screens */}
            <div className="sm:hidden relative" ref={dropdownRef}>
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="p-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
                aria-label="Account menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              
              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-2 text-sm text-gray-700 border-b border-gray-100">
                    {user?.preferred_first_name || user?.first_name}
                  </div>
                  <button
                    onClick={handleAccountClick}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                  >
                    Account Settings
                  </button>
                  <button
                    onClick={handleLogoutClick}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Account Settings Modal */}
      <AccountSettingsModal
        isOpen={isAccountModalOpen}
        onClose={() => setIsAccountModalOpen(false)}
      />
    </header>
  )
}

export default DashboardHeader

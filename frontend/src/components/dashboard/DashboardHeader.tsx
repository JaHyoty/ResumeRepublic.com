import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { APP_NAME } from '../../config/constants'

const DashboardHeader: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="bg-white sticky top-0 z-40 w-screen left-0 right-0" style={{ marginLeft: 'calc(50% - 50vw)' }}>
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex justify-between items-center py-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-purple-800 bg-clip-text text-transparent">
            {APP_NAME}
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              Welcome, {user?.preferred_first_name || user?.first_name}!
            </span>
            <button
              onClick={handleLogout}
              className="text-gray-600 hover:text-gray-800 font-medium text-sm transition-colors duration-200"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader

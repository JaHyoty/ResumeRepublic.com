import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { APP_NAME } from '../../config/constants'

const Header: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()

  const handleAuthClick = () => {
    if (isAuthenticated) {
      navigate('/dashboard')
    } else {
      navigate('/login')
    }
  }

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
            {isAuthenticated ? (
              <>
                <span className="text-sm text-gray-600">
                  Welcome, {user?.preferred_first_name || user?.first_name}!
                </span>
                <button
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-gray-800 font-medium text-sm transition-colors duration-200"
                >
                  Logout
                </button>
                <button 
                  onClick={() => navigate('/dashboard')}
                  className="bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white font-semibold px-6 py-2 rounded-full text-sm transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  Dashboard
                </button>
              </>
            ) : (
              <button 
                onClick={handleAuthClick}
                className="bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white font-semibold px-6 py-2 rounded-full text-sm transition-all duration-200 shadow-md hover:shadow-lg"
              >
                Login
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

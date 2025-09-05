import React from 'react'
import { APP_NAME } from '../../config/constants'

const Header: React.FC = () => {
  return (
    <header className="bg-white sticky top-0 z-40 w-screen left-0 right-0" style={{ marginLeft: 'calc(50% - 50vw)' }}>
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto flex justify-between items-center py-4">
          <h1 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-purple-800 bg-clip-text text-transparent">
            {APP_NAME}
          </h1>
          <button 
            className="bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white font-semibold px-6 py-2 rounded-full text-sm transition-all duration-200 shadow-md hover:shadow-lg"
          >
            Login
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header

import React from 'react'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-secondary-50">
      <header className="bg-white shadow-sm border-b border-secondary-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-primary-600">CareerPathPro</h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="/dashboard" className="text-secondary-600 hover:text-primary-600">Dashboard</a>
              <a href="/esc" className="text-secondary-600 hover:text-primary-600">ESC</a>
              <a href="/resume" className="text-secondary-600 hover:text-primary-600">Resume</a>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}

export default Layout

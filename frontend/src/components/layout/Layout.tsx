import React from 'react'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-secondary-50">
      <main className="max-w-7xl mx-auto sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}

export default Layout

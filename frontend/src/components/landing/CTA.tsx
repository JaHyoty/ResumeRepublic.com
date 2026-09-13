import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { APP_NAME } from '../../config/constants'

const CTA: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard')
    } else {
      navigate('/login')
    }
  }

  return (
    <section 
      className="py-16 bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 w-screen left-0 right-0 overflow-hidden" 
      style={{ marginLeft: 'calc(50% - 50vw)' }}
      aria-labelledby="cta-heading"
    >
      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
        <h2 id="cta-heading" className="text-3xl md:text-4xl font-bold text-white mb-6">
          Ready to optimize your career?
        </h2>
        <p className="text-lg text-blue-200 mb-8 max-w-2xl mx-auto">
          Join others who are already using {APP_NAME} to build better resumes and advance their careers.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button 
            onClick={handleGetStarted}
            className="bg-blue-600 text-white hover:bg-blue-500 font-semibold text-lg px-8 py-3 rounded-lg flex items-center gap-2 shadow-xl hover:shadow-2xl transition-all duration-300"
          >
            Get Started
          </button>
        </div>
      </div>
    </section>
  )
}

export default CTA

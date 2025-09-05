import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { APP_TAGLINE } from '../../config/constants'

const Hero: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const handleTailorResume = () => {
    if (isAuthenticated) {
      navigate('/dashboard')
    } else {
      navigate('/login')
    }
  }

  return (
    <section className="relative w-full text-white py-16 lg:py-24" role="banner">
      {/* Purple gradient background with circular darker center */}
      <div 
        className="absolute left-0 right-0 top-0 bottom-0 w-screen h-full"
        style={{
          marginLeft: 'calc(50% - 50vw)',
          background: `
            radial-gradient(ellipse at center bottom, 
              rgba(59, 7, 100, 0.9) 0%, 
              rgba(88, 28, 135, 0.8) 30%, 
              rgba(147, 51, 234, 0.7) 60%, 
              rgba(168, 85, 247, 0.6) 100%
            ),
            linear-gradient(135deg, 
              rgba(147, 51, 234, 0.8) 0%, 
              rgba(126, 34, 206, 0.9) 100%
            )
          `
        }}
      ></div>
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8" id="main-content">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Faster career movements with
            <span className="block text-yellow-300 mt-2">Tailored Resumes</span>
          </h1>
          <p className="text-lg md:text-xl text-purple-100 mb-8 leading-relaxed max-w-2xl mx-auto">
            {APP_TAGLINE}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <button 
              onClick={handleTailorResume}
              className="bg-gray-200 text-black border-2 border-gray-300 hover:bg-yellow-50 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              Tailor My Resume
            </button>
            <button className="border-2 border-white text-white hover:bg-purple-500 hover:text-primary-700 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 transition-all duration-300">
              Watch Demo
            </button>
          </div>
          <p className="text-purple-400 text-sm">
            Made to overcome the shortcomings of AI in the hiring process.<br/>
            As such, we'd like to offer this service for free to all users.
          </p>
        </div>
      </div>
    </section>
  )
}

export default Hero

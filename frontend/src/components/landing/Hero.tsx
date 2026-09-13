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
    <section 
      className="relative text-white py-16 lg:py-24 overflow-hidden w-screen left-0 right-0" 
      style={{ marginLeft: 'calc(50% - 50vw)' }}
      role="banner"
    >
      {/* Dark metallic blue background with crossing whiter hue lines */}
      <div 
        className="absolute inset-0 w-full h-full"
        style={{
          background: `
            radial-gradient(ellipse at center bottom, 
              #07152b 0%, 
              #0c2242 35%, 
              #12325c 70%, 
              #0a1c35 100%
            ),
            linear-gradient(135deg, 
              #0c203d 0%, 
              #06101f 100%
            )
          `
        }}
      >
        {/* Crossing whiter hue lines intersecting to form an obtuse angle */}
        <svg 
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 1440 600"
          preserveAspectRatio="none"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="whiteLineGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
              <stop offset="25%" stopColor="#bae6fd" stopOpacity="0.25" />
              <stop offset="50%" stopColor="#ffffff" stopOpacity="0.9" />
              <stop offset="75%" stopColor="#bae6fd" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="whiteLineGrad2" x1="20%" y1="100%" x2="80%" y2="0%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
              <stop offset="25%" stopColor="#bae6fd" stopOpacity="0.25" />
              <stop offset="50%" stopColor="#ffffff" stopOpacity="0.9" />
              <stop offset="75%" stopColor="#bae6fd" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>

            <radialGradient id="centerWhiteGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.25" />
              <stop offset="45%" stopColor="#38bdf8" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Soft specular glow at line intersection */}
          <ellipse cx="720" cy="270" rx="160" ry="75" fill="url(#centerWhiteGlow)" />

          {/* Line 1: crossing downwards */}
          <line x1="-50" y1="110" x2="1490" y2="430" stroke="url(#whiteLineGrad1)" strokeWidth="1.5" />
          <line x1="-50" y1="110" x2="1490" y2="430" stroke="#ffffff" strokeOpacity="0.12" strokeWidth="5" />

          {/* Line 2: crossing upwards, intersecting Line 1 at (720, 270) to form an obtuse angle (~132°) */}
          <line x1="320" y1="590" x2="1120" y2="-50" stroke="url(#whiteLineGrad2)" strokeWidth="1.5" />
          <line x1="320" y1="590" x2="1120" y2="-50" stroke="#ffffff" strokeOpacity="0.12" strokeWidth="5" />
        </svg>
      </div>
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8" id="main-content">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Faster career movements with
            <span className="block text-yellow-300 mt-2">Tailored Resumes</span>
          </h1>
          <p className="text-lg md:text-xl text-blue-100 mb-8 leading-relaxed max-w-2xl mx-auto">
            {APP_TAGLINE}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <button 
              onClick={handleTailorResume}
              className="bg-gray-200 text-black border-2 border-gray-300 hover:bg-yellow-50 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              Tailor My Resume
            </button>
            {/* <button className="border-2 border-white text-white hover:bg-blue-500 hover:text-blue-100 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 transition-all duration-300">
              Watch Demo
            </button> */}
          </div>
          <p className="text-slate-400 text-sm">
            Made to promote responsible AI usage in the application process.<br/>
            As such, this service is <b>free to use</b>, provided as-is with no liabilities.
          </p>
        </div>
      </div>
    </section>
  )
}

export default Hero

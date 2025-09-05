import React from 'react'

const Hero: React.FC = () => {
  return (
    <section className="bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white py-16 lg:py-24" role="banner">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8" id="main-content">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Optimize Your Career with
            <span className="block text-yellow-300 mt-2">AI-Powered Resumes</span>
          </h1>
          <p className="text-lg md:text-xl text-purple-100 mb-8 leading-relaxed max-w-2xl mx-auto">
            Transform your professional profile with intelligent resume parsing, 
            ESC management, and ATS-optimized LaTeX generation.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <button className="bg-white text-primary-700 hover:bg-yellow-50 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300">
              Start Free Trial
            </button>
            <button className="border-2 border-white text-white hover:bg-white hover:text-primary-700 font-semibold text-lg px-8 py-3 rounded-lg flex items-center justify-center gap-2 transition-all duration-300">
              Watch Demo
            </button>
          </div>
          <p className="text-purple-200 text-sm">
            ✨ No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </div>
    </section>
  )
}

export default Hero

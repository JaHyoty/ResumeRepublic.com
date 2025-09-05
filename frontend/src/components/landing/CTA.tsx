import React from 'react'
import { APP_NAME } from '../../config/constants'

const CTA: React.FC = () => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary-600 to-primary-700" aria-labelledby="cta-heading">
      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
        <h2 id="cta-heading" className="text-3xl md:text-4xl font-bold text-black mb-6">
          Ready to optimize your career?
        </h2>
        <p className="text-lg text-purple-600 mb-8 max-w-2xl mx-auto">
          Join others who are already using {APP_NAME} to build better resumes and advance their careers.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button className="bg-purple-600 text-white hover:bg-purple-400 font-semibold text-lg px-8 py-3 rounded-lg flex items-center gap-2 shadow-xl hover:shadow-xl transition-all duration-300">
            Get Started
          </button>
        </div>
      </div>
    </section>
  )
}

export default CTA

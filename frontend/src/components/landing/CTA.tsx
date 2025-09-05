import React from 'react'

const CTA: React.FC = () => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary-600 to-primary-700" aria-labelledby="cta-heading">
      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
        <h2 id="cta-heading" className="text-3xl md:text-4xl font-bold text-white mb-6">
          Ready to optimize your career?
        </h2>
        <p className="text-lg text-purple-100 mb-8 max-w-2xl mx-auto">
          Join thousands of professionals who are already using CareerPathPro to build better resumes and advance their careers.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button className="bg-white text-primary-700 hover:bg-yellow-50 font-semibold text-lg px-8 py-3 rounded-lg flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300">
            Start Free Trial
          </button>
          <button className="border-2 border-white text-white hover:bg-white hover:text-primary-700 font-semibold text-lg px-8 py-3 rounded-lg transition-all duration-300">
            Schedule Demo
          </button>
        </div>
        <p className="text-purple-200 mt-6 text-sm">
          ✨ No credit card required • Cancel anytime • 14-day free trial
        </p>
      </div>
    </section>
  )
}

export default CTA

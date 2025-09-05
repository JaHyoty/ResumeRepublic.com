import React from 'react'

interface StepProps {
  stepNumber: number
  title: string
  description: string
}

const Step: React.FC<StepProps> = ({ stepNumber, title, description }) => {
  return (
    <div className="text-center">
      <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-6">
        {stepNumber}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

const HowItWorks: React.FC = () => {
  const steps = [
    {
      stepNumber: 1,
      title: "Upload & Parse",
      description: "Upload your existing resume and let our system extract all your professional information automatically."
    },
    {
      stepNumber: 2,
      title: "Manage & Optimize",
      description: "Review and edit your ESC data, analyze job descriptions, and optimize your content for ATS systems."
    },
    {
      stepNumber: 3,
      title: "Generate & Export",
      description: "Generate professional LaTeX resumes, preview them, and export to PDF for your job applications."
    }
  ]

  return (
    <section className="py-16 bg-gray-50" aria-labelledby="how-it-works-heading">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 id="how-it-works-heading" className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            How it works
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Get started in minutes with our simple 3-step process
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <Step
              key={index}
              stepNumber={step.stepNumber}
              title={step.title}
              description={step.description}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default HowItWorks

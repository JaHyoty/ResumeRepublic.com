import React from 'react'

interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
  features: string[]
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, features }) => {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6 hover:shadow-lg transition-shadow duration-300">
      <div className="mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>
      <ul className="space-y-2 text-sm text-gray-600">
        {features.map((feature, index) => (
          <li key={index} className="flex items-center gap-2">
            {feature}
          </li>
        ))}
      </ul>
    </div>
  )
}

const Features: React.FC = () => {
  const featuresData = [
    {
      icon: <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center"></div>,
      title: "Smart Resume Parsing",
      description: "Upload your existing resume and let our system extract key details automatically.",
      features: [
        "PDF and DOCX support",
        "Intelligent data extraction", 
        "Error detection and correction"
      ]
    },
    {
      icon: <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center"></div>,
      title: "Experience and Skills Catalog",
      description: "Manage your experiences and skills in one centralized dashboard.",
      features: [
        "Store your experiences, skills, certifications, etc.",
        "Used for accurate resume generation",
        "Skill development suggestions"
      ]
    },
    {
      icon: <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center"></div>,
      title: "PDF Resume Generation",
      description: "Generate professional, ATS-optimized resumes with our clean resume templates.",
      features: [
        "Multiple templates",
        "ATS optimization",
        "PDF export"
      ]
    },
    {
      icon: <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center"></div>,
      title: "Job Description Analysis",
      description: "Analyze job descriptions to identify key requirements and optimize your resume accordingly.",
      features: [
        "Keyword extraction",
        "Skills matching",
        "Optimization suggestions"
      ]
    },
    {
      icon: <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center"></div>,
      title: "Resume Versioning",
      description: "Keep track of different resume versions and easily switch between them for different applications.",
      features: [
        "Version history",
        "Quick switching",
        "Application tracking"
      ]
    },
    {
      icon: <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center"></div>,
      title: "Analytics & Insights",
      description: "Get insights into your career progress and resume performance.",
      features: [
        "Progress tracking",
        "Performance metrics",
        "Improvement suggestions"
      ]
    }
  ]

  return (
    <section className="py-16 bg-white" aria-labelledby="features-heading">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 id="features-heading" className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Everything you need to take the next step
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From intelligent skill matching to ATS optimization, we've got you covered
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featuresData.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              features={feature.features}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default Features

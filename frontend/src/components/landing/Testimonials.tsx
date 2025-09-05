import React from 'react'
import { APP_NAME } from '../../config/constants'

interface TestimonialCardProps {
  quote: string
  author: {
    name: string
    role: string
    initials: string
    bgColor: string
    textColor: string
  }
}

const TestimonialCard: React.FC<TestimonialCardProps> = ({ quote, author }) => {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
      <p className="text-gray-600 mb-4">{quote}</p>
      <div className="flex items-center">
        <div className={`w-10 h-10 ${author.bgColor} rounded-full flex items-center justify-center mr-3`}>
          <span className={`${author.textColor} font-semibold text-sm`}>{author.initials}</span>
        </div>
        <div>
          <p className="font-semibold text-gray-900">{author.name}</p>
          <p className="text-sm text-gray-500">{author.role}</p>
        </div>
      </div>
    </div>
  )
}

const Testimonials: React.FC = () => {
  const testimonials = [
    {
      quote: `${APP_NAME} saved me hours of work. The AI parsing is incredibly accurate and the LaTeX output looks professional.`,
      author: {
        name: "Jessica Smith",
        role: "Software Engineer",
        initials: "JS",
        bgColor: "bg-primary-100",
        textColor: "text-primary-600"
      }
    },
    {
      quote: "The ESC management system is a game-changer. I can finally keep track of all my experiences and skills in one place.",
      author: {
        name: "Michael Rodriguez",
        role: "Product Manager",
        initials: "MR",
        bgColor: "bg-blue-100",
        textColor: "text-blue-600"
      }
    },
    {
      quote: "The ATS optimization feature helped me get more interview calls. My resume now passes through applicant tracking systems.",
      author: {
        name: "Alex Lee",
        role: "Data Scientist",
        initials: "AL",
        bgColor: "bg-green-100",
        textColor: "text-green-600"
      }
    }
  ]

  return (
    <section className="py-16 bg-white" aria-labelledby="testimonials-heading">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 id="testimonials-heading" className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Trusted by professionals worldwide
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            See what our users are saying about {APP_NAME}
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard
              key={index}
              quote={testimonial.quote}
              author={testimonial.author}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default Testimonials

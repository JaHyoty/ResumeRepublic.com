import React from 'react'
import {
  Header,
  Hero,
  Features,
  HowItWorks,
  Testimonials,
  CTA,
  Footer
} from '../components/landing'

const LandingPage: React.FC = () => {
  return (
    <div className="bg-white min-h-screen">
      <Header />
      <Hero />
      <Features />
      <HowItWorks />
      <Testimonials />
      <CTA />
      <Footer />
    </div>
  )
}

export default LandingPage

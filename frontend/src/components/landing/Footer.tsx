import React from 'react'
import { APP_NAME } from '../../config/constants'

interface FooterNavProps {
  title: string
  links: Array<{
    label: string
    href: string
  }>
  ariaLabel?: string
}

const FooterNav: React.FC<FooterNavProps> = ({ title, links, ariaLabel }) => {
  return (
    <nav aria-label={ariaLabel}>
      <h4 className="font-semibold text-white mb-4">{title}</h4>
      <ul className="space-y-2 text-gray-300">
        {links.map((link, index) => (
          <li key={index}>
            <a 
              href={link.href} 
              className="hover:text-white transition-colors"
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

const Footer: React.FC = () => {
  const productLinks = [
    { label: "Features", href: "#features-heading" },
    { label: "Pricing", href: "#" },
    { label: "Templates", href: "#" },
    { label: "API", href: "#" }
  ]

  const supportLinks = [
    { label: "Help Center", href: "#" },
    { label: "Contact Us", href: "#" },
    { label: "Status", href: "#" },
    { label: "Community", href: "#" }
  ]

  const companyLinks = [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Careers", href: "#" },
    { label: "Privacy", href: "#" }
  ]

  return (
    <footer className="bg-gray-900 text-white py-12" role="contentinfo">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-xl font-bold text-white mb-4 bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
              {APP_NAME}
            </h3>
            <p className="text-gray-300 mb-4">
              Optimize your career with AI-powered resume generation and management.
            </p>
          </div>
          
          <FooterNav 
            title="Product"
            links={productLinks}
            ariaLabel="Product navigation"
          />
          
          <FooterNav 
            title="Support"
            links={supportLinks}
            ariaLabel="Support navigation"
          />
          
          <FooterNav 
            title="Company"
            links={companyLinks}
            ariaLabel="Company navigation"
          />
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-300">
          <p>&copy; {new Date().getFullYear()} {APP_NAME}. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer

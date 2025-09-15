/**
 * Application constants and configuration
 * Centralized place to manage app-wide constants that may change
 */

export const APP_CONFIG = {
  name: 'ResumeRepublic',
  description: 'Optimize your career with AI-powered resumes',
  tagline: 'Transform your professional profile with a tool that truly knows your value. No more inaccurate AI resume generators.',
} as const;

export const CONTACT_INFO = {
  email: 'support@resumerepublic.com',
  phone: '+1 (555) 123-4567',
} as const;

export const SOCIAL_LINKS = {
  twitter: 'https://twitter.com/careerpathpro',
  linkedin: 'https://linkedin.com/company/careerpathpro',
  github: 'https://github.com/careerpathpro',
} as const;

// Re-export commonly used values for convenience
export const APP_NAME = APP_CONFIG.name;
export const APP_DESCRIPTION = APP_CONFIG.description;
export const APP_TAGLINE = APP_CONFIG.tagline;

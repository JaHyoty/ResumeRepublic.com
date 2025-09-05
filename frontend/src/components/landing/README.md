# Landing Page Components

This directory contains modular, reusable components for the CareerPathPro landing page. Each component is self-contained and follows React best practices.

## Component Structure

```
landing/
├── Header.tsx          # Navigation header with login/signup
├── Hero.tsx           # Main hero section with CTA
├── Features.tsx       # Feature cards with icons and descriptions
├── HowItWorks.tsx     # 3-step process explanation
├── Testimonials.tsx   # Customer testimonials with ratings
├── CTA.tsx           # Call-to-action section
├── Footer.tsx        # Footer with navigation links
├── index.ts          # Barrel exports for clean imports
└── README.md         # This documentation file
```

## Usage

### Import Individual Components
```tsx
import { Header, Hero, Features } from '../components/landing'
```

### Import All Components
```tsx
import * as Landing from '../components/landing'

// Usage: <Landing.Header />, <Landing.Hero />, etc.
```

## Component Features

### Header
- Sticky navigation
- Login/signup buttons
- Responsive design
- Brand logo with gradient

### Hero
- Gradient background
- Primary and secondary CTAs
- Responsive typography
- Trust indicators

### Features
- Grid layout (1/2/3 columns)
- Icon-based feature cards
- Hover animations
- Reusable FeatureCard component

### HowItWorks
- 3-step process visualization
- Numbered steps
- Reusable Step component
- Clean, minimal design

### Testimonials
- Star ratings
- Customer avatars
- Reusable TestimonialCard component
- Social proof layout

### CTA
- Conversion-focused design
- Multiple call-to-action buttons
- Trust indicators
- Gradient background

### Footer
- Multi-column navigation
- Reusable FooterNav component
- Brand information
- Copyright notice

## Design Principles

1. **Modularity**: Each component is self-contained
2. **Reusability**: Components can be used in other pages
3. **Maintainability**: Easy to update individual sections
4. **TypeScript**: Full type safety with interfaces
5. **Accessibility**: ARIA labels and semantic HTML
6. **Responsive**: Mobile-first design approach

## Customization

Each component accepts props for customization:

```tsx
// Example: Custom testimonials data
const customTestimonials = [
  {
    quote: "Custom testimonial text",
    author: { name: "John Doe", role: "Developer", initials: "JD" }
  }
]

<Testimonials testimonials={customTestimonials} />
```

## Benefits

- **Faster Development**: Focus on one section at a time
- **Better Testing**: Test individual components in isolation
- **Code Reuse**: Use components in other pages/projects
- **Team Collaboration**: Multiple developers can work on different sections
- **Easier Maintenance**: Update sections without affecting others

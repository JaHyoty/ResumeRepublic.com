import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ExperienceModal from '../experience/ExperienceModal'
import { experienceService, type Experience, type CreateExperienceRequest } from '../../services/experienceService'

const ExperienceSkillsView: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [isExperienceModalOpen, setIsExperienceModalOpen] = useState(false)
  
  const queryClient = useQueryClient()

  // Fetch experiences
  const { data: experiences = [], isLoading: experiencesLoading, error: experiencesError } = useQuery({
    queryKey: ['experiences'],
    queryFn: experienceService.getExperiences,
  })

  // Create experience mutation
  const createExperienceMutation = useMutation({
    mutationFn: experienceService.createExperience,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
      setIsExperienceModalOpen(false)
    },
    onError: (error) => {
      console.error('Failed to create experience:', error)
      // You could add toast notification here
    }
  })

  const sections = [
    {
      id: 'experience',
      title: 'Work Experience',
      description: 'Your professional work history, job titles, and achievements',
      icon: '💼',
      color: 'bg-blue-50 border-blue-200',
      iconColor: 'text-blue-600',
      fields: ['Company', 'Job Titles', 'Location', 'Dates', 'Description', 'Achievements', 'Tools Used']
    },
    {
      id: 'skills',
      title: 'Skills',
      description: 'Technical and soft skills with proficiency levels',
      icon: '🎓',
      color: 'bg-green-50 border-green-200',
      iconColor: 'text-green-600',
      fields: ['Skill Name', 'Proficiency Level', 'Years of Experience', 'Source (Work/Education/Certification)']
    },
    {
      id: 'tools',
      title: 'Tools & Technologies',
      description: 'Software, frameworks, and technologies you\'ve worked with',
      icon: '🔧',
      color: 'bg-purple-50 border-purple-200',
      iconColor: 'text-purple-600',
      fields: ['Tool Name', 'Category', 'Associated Experiences']
    },
    {
      id: 'certifications',
      title: 'Certifications',
      description: 'Professional certifications and credentials',
      icon: '🏆',
      color: 'bg-yellow-50 border-yellow-200',
      iconColor: 'text-yellow-600',
      fields: ['Certification Name', 'Issuing Organization', 'Date Obtained', 'Expiration Date', 'Credential URL', 'Credential ID']
    },
    {
      id: 'publications',
      title: 'Publications',
      description: 'Articles, papers, blog posts, and other publications',
      icon: '📚',
      color: 'bg-indigo-50 border-indigo-200',
      iconColor: 'text-indigo-600',
      fields: ['Title', 'Co-authors', 'Publication Date', 'URL', 'Description', 'Publication Type']
    }
  ]

  const handleAddClick = (sectionId: string) => {
    if (sectionId === 'experience') {
      setIsExperienceModalOpen(true)
    } else {
      // Handle other sections later
      console.log(`Add clicked for ${sectionId}`)
    }
  }

  const handleExperienceSubmit = async (data: CreateExperienceRequest) => {
    await createExperienceMutation.mutateAsync(data)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short'
    })
  }

  const ExperienceCard = ({ experience }: { experience: Experience }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-3">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{experience.company}</h4>
          {experience.titles.length > 0 && (
            <p className="text-gray-700">
              {experience.titles.find(t => t.is_primary)?.title || experience.titles[0].title}
              {experience.titles.length > 1 && ` (+${experience.titles.length - 1} more)`}
            </p>
          )}
          <p className="text-sm text-gray-500">
            {formatDate(experience.start_date)} - {experience.is_current ? 'Present' : (experience.end_date ? formatDate(experience.end_date) : 'Present')}
            {experience.location && ` • ${experience.location}`}
          </p>
          {experience.description && (
            <p className="text-sm text-gray-600 mt-2">{experience.description}</p>
          )}
          {experience.achievements.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-500 mb-1">{experience.achievements.length} achievement{experience.achievements.length !== 1 ? 's' : ''}</p>
            </div>
          )}
        </div>
        <div className="flex space-x-2 ml-4">
          <button className="text-xs text-blue-600 hover:text-blue-800">Edit</button>
          <button className="text-xs text-red-600 hover:text-red-800">Delete</button>
        </div>
      </div>
    </div>
  )

  const SectionCard = ({ section }: { section: typeof sections[0] }) => {
    const isExpanded = activeSection === section.id
    const isExperienceSection = section.id === 'experience'
    const hasData = isExperienceSection && experiences.length > 0

    return (
      <div className={`border-2 rounded-lg p-6 transition-all duration-200 ${section.color} ${isExpanded ? 'ring-2 ring-offset-2 ring-gray-300' : ''}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="p-2 rounded-lg bg-white border text-2xl">
              {section.icon}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{section.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{section.description}</p>
              
              {/* Show existing experiences */}
              {isExperienceSection && hasData && (
                <div className="mb-4">
                  {experiences.map((experience) => (
                    <ExperienceCard key={experience.id} experience={experience} />
                  ))}
                </div>
              )}
              
              {isExpanded && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-800 mb-2">Information to collect:</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {section.fields.map((field, index) => (
                      <div key={index} className="text-xs text-gray-600 bg-white px-2 py-1 rounded border">
                        {field}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="mt-4 flex items-center justify-between">
                {isExperienceSection ? (
                  <span className="text-sm text-gray-500">
                    {experiencesLoading ? 'Loading...' : 
                     experiencesError ? 'Error loading experiences' :
                     hasData ? `${experiences.length} experience${experiences.length !== 1 ? 's' : ''} added` : 'No experiences added yet'}
                  </span>
                ) : (
                  <span className="text-sm text-gray-500">No entries added yet</span>
                )}
                <div className="flex space-x-2">
                  <button
                    onClick={() => setActiveSection(isExpanded ? null : section.id)}
                    className="text-xs text-gray-600 hover:text-gray-800 underline"
                  >
                    {isExpanded ? 'Hide details' : 'View details'}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <button 
            onClick={() => handleAddClick(section.id)}
            className="flex items-center space-x-1 bg-white border border-gray-300 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <span className="text-lg">+</span>
            <span>Add</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">Experience & Skills Catalogue</h2>
        <p className="text-gray-600 text-lg">
          Build your comprehensive professional profile by organizing your experience, skills, and achievements.
        </p>
      </div>

      <div className="space-y-6">
        {sections.map((section) => (
          <SectionCard key={section.id} section={section} />
        ))}
      </div>

      <div className="mt-12 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="text-2xl text-gray-400 mt-1">📋</div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">How it works</h3>
            <div className="text-sm text-gray-600 space-y-2">
              <p>• <strong>Centralized Data:</strong> Store all your professional information in one place</p>
              <p>• <strong>Smart Organization:</strong> Link experiences with skills and tools for better context</p>
              <p>• <strong>Resume Generation:</strong> Use this data to automatically generate tailored resumes</p>
              <p>• <strong>Application Matching:</strong> Match your profile against job requirements</p>
            </div>
          </div>
        </div>
      </div>

      {/* Experience Modal */}
      <ExperienceModal
        isOpen={isExperienceModalOpen}
        onClose={() => setIsExperienceModalOpen(false)}
        onSubmit={handleExperienceSubmit}
        isLoading={createExperienceMutation.isPending}
      />
    </div>
  )
}

export default ExperienceSkillsView

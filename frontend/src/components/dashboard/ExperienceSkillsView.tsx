import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ExperienceModal from '../experience/ExperienceModal'
import DeleteConfirmationModal from '../experience/DeleteConfirmationModal'
import SkillsModal from '../skills/SkillsModal'
import { experienceService, type Experience, type CreateExperienceRequest } from '../../services/experienceService'
import { skillService, type Skill, type CreateSkillRequest } from '../../services/skills/skillService'

const ExperienceSkillsView: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [isExperienceModalOpen, setIsExperienceModalOpen] = useState(false)
  const [selectedExperience, setSelectedExperience] = useState<Experience | null>(null)
  const [editingExperience, setEditingExperience] = useState<Experience | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [deletingExperience, setDeletingExperience] = useState<Experience | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [skillsModalMode, setSkillsModalMode] = useState<'create' | 'edit'>('create')
  
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
      setEditingExperience(null)
    },
    onError: (error) => {
      console.error('Failed to create experience:', error)
      // You could add toast notification here
    }
  })

  // Update experience mutation
  const updateExperienceMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateExperienceRequest }) => 
      experienceService.updateExperience(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
      setIsExperienceModalOpen(false)
      setEditingExperience(null)
    },
    onError: (error) => {
      console.error('Failed to update experience:', error)
      // You could add toast notification here
    }
  })

  // Delete experience mutation
  const deleteExperienceMutation = useMutation({
    mutationFn: (id: number) => experienceService.deleteExperience(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
      setIsDeleteModalOpen(false)
      setDeletingExperience(null)
    },
    onError: (error) => {
      console.error('Failed to delete experience:', error)
      // You could add toast notification here
    }
  })

  // Fetch skills
  const { data: skills = [], isLoading: skillsLoading, error: skillsError } = useQuery({
    queryKey: ['skills'],
    queryFn: skillService.getSkills,
  })

  // Create skill mutation
  const createSkillMutation = useMutation({
    mutationFn: skillService.createSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setIsSkillsModalOpen(false)
      setEditingSkill(null)
    },
    onError: (error) => {
      console.error('Failed to create skill:', error)
      // You could add toast notification here
    }
  })

  // Update skill mutation
  const updateSkillMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateSkillRequest }) => 
      skillService.updateSkill(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setIsSkillsModalOpen(false)
      setEditingSkill(null)
    },
    onError: (error) => {
      console.error('Failed to update skill:', error)
      // You could add toast notification here
    }
  })

  // Delete skill mutation
  const deleteSkillMutation = useMutation({
    mutationFn: (id: number) => skillService.deleteSkill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
    },
    onError: (error) => {
      console.error('Failed to delete skill:', error)
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
      description: 'Technical and soft skills you possess',
      icon: '🎓',
      color: 'bg-green-50 border-green-200',
      iconColor: 'text-green-600',
      fields: ['Skill Name']
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
      setModalMode('create')
      setEditingExperience(null)
      setIsExperienceModalOpen(true)
    } else {
      // Handle other sections later
      console.log(`Add clicked for ${sectionId}`)
    }
  }

  const handleEditClick = (experience: Experience) => {
    setModalMode('edit')
    setEditingExperience(experience)
    setIsExperienceModalOpen(true)
  }

  const handleDeleteClick = (experience: Experience) => {
    setDeletingExperience(experience)
    setIsDeleteModalOpen(true)
  }

  const handleConfirmDelete = () => {
    if (deletingExperience) {
      deleteExperienceMutation.mutate(deletingExperience.id!)
    }
  }

  const handleExperienceSubmit = async (data: CreateExperienceRequest) => {
    if (modalMode === 'edit' && editingExperience) {
      await updateExperienceMutation.mutateAsync({ 
        id: editingExperience.id!, 
        data 
      })
    } else {
      await createExperienceMutation.mutateAsync(data)
    }
  }

  // Skills handlers
  const handleAddSkillClick = () => {
    setSkillsModalMode('create')
    setEditingSkill(null)
    setIsSkillsModalOpen(true)
  }


  const handleDeleteSkillClick = (skill: Skill) => {
    deleteSkillMutation.mutate(skill.id!)
  }


  const handleSkillSubmit = async (data: CreateSkillRequest) => {
    if (skillsModalMode === 'edit' && editingSkill) {
      await updateSkillMutation.mutateAsync({ 
        id: editingSkill.id!, 
        data 
      })
    } else {
      await createSkillMutation.mutateAsync(data)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short'
    })
  }

  const ExperienceCard = ({ experience }: { experience: Experience }) => {
    const isSelected = selectedExperience?.id === experience.id
    
    return (
      <div 
        className={`w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all cursor-pointer ${
          isSelected ? 'border-blue-300 bg-blue-50' : 'border-gray-200'
        }`}
        onClick={() => setSelectedExperience(isSelected ? null : experience)}
      >
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold text-gray-900">{experience.company}</h4>
              {experience.is_current && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Current
                </span>
              )}
            </div>
            {experience.titles.length > 0 && (
              <p className="text-sm text-gray-700 mt-1">
                {experience.titles.find(t => t.is_primary)?.title || experience.titles[0].title}
                {experience.titles.length > 1 && ` (+${experience.titles.length - 1} more)`}
              </p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              {formatDate(experience.start_date)} - {experience.is_current ? 'Present' : (experience.end_date ? formatDate(experience.end_date) : 'Present')}
              {experience.location && ` • ${experience.location}`}
            </p>
            {experience.achievements.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {experience.achievements.length} achievement{experience.achievements.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <div className="flex space-x-1 ml-4">
            <button 
              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
              onClick={(e) => {
                e.stopPropagation()
                handleEditClick(experience)
              }}
            >
              Edit
            </button>
            <button 
              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteClick(experience)
              }}
            >
              Delete
            </button>
          </div>
        </div>
        
        {/* Expanded details */}
        {isSelected && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            {experience.description && (
              <div className="mb-3">
                <h5 className="text-sm font-medium text-gray-900 mb-1">Description</h5>
                <p className="text-sm text-gray-600">{experience.description}</p>
              </div>
            )}
            
            {experience.titles.length > 1 && (
              <div className="mb-3">
                <h5 className="text-sm font-medium text-gray-900 mb-1">All Job Titles</h5>
                <div className="flex flex-wrap gap-1">
                  {experience.titles.map((title, index) => (
                    <span 
                      key={index}
                      className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                        title.is_primary 
                          ? 'bg-blue-100 text-blue-800 font-medium' 
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {title.title}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {experience.achievements.length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-900 mb-2">Key Achievements</h5>
                <ul className="space-y-1">
                  {experience.achievements.map((achievement, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start">
                      <span className="text-blue-500 mr-2">•</span>
                      {achievement.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const SkillCard = ({ skill }: { skill: Skill }) => {
    return (
      <div className="inline-block bg-white border border-gray-200 rounded-lg mr-2 mb-2 hover:shadow-md transition-all duration-200 group overflow-hidden">
        <div className="flex items-center px-3 py-1.5">
          <span className="text-sm font-medium text-gray-900 whitespace-nowrap">{skill.name}</span>
          <div className="w-0 group-hover:w-8 transition-all duration-200 overflow-hidden">
            <button 
              className="text-red-600 hover:text-red-800 hover:bg-red-50 ml-2 p-1 rounded-full"
              onClick={() => handleDeleteSkillClick(skill)}
              title="Delete skill"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    )
  }

  const SectionCard = ({ section }: { section: typeof sections[0] }) => {
    const isExpanded = activeSection === section.id
    const isExperienceSection = section.id === 'experience'
    const isSkillsSection = section.id === 'skills'
    const hasData = (isExperienceSection && experiences.length > 0) || (isSkillsSection && skills.length > 0)

    return (
      <div className={`border-2 rounded-lg p-6 transition-all duration-200 ${section.color} ${isExpanded ? 'ring-2 ring-offset-2 ring-gray-300' : ''}`}>
        <div className="flex items-start justify-between w-full">
          <div className="flex items-start space-x-4 w-full">
            <div className="p-2 rounded-lg bg-white border text-2xl">
              {section.icon}
            </div>
            <div className="flex-1 w-full">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{section.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{section.description}</p>
              
              {/* Show existing experiences */}
              {isExperienceSection && hasData && (
                <div className="mb-4 w-full">
                  {experiences.map((experience) => (
                    <ExperienceCard key={experience.id} experience={experience} />
                  ))}
                </div>
              )}

              {/* Show existing skills */}
              {isSkillsSection && hasData && (
                <div className="mb-4 w-full">
                  <div className="flex flex-wrap">
                    {skills.map((skill) => (
                      <SkillCard key={skill.id} skill={skill} />
                    ))}
                  </div>
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
                ) : isSkillsSection ? (
                  <span className="text-sm text-gray-500">
                    {skillsLoading ? 'Loading...' : 
                     skillsError ? 'Error loading skills' :
                     hasData ? `${skills.length} skill${skills.length !== 1 ? 's' : ''} added` : 'No skills added yet'}
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
            onClick={() => isSkillsSection ? handleAddSkillClick() : handleAddClick(section.id)}
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
        onClose={() => {
          setIsExperienceModalOpen(false)
          setEditingExperience(null)
        }}
        onSubmit={handleExperienceSubmit}
        isLoading={createExperienceMutation.isPending || updateExperienceMutation.isPending}
        initialData={editingExperience ? {
          company: editingExperience.company,
          location: editingExperience.location || '',
          start_date: editingExperience.start_date,
          end_date: editingExperience.end_date || '',
          description: editingExperience.description || '',
          is_current: editingExperience.is_current,
          titles: editingExperience.titles.map(t => ({
            title: t.title,
            is_primary: t.is_primary
          })),
          achievements: editingExperience.achievements.map(a => ({
            description: a.description
          }))
        } : undefined}
        mode={modalMode}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setDeletingExperience(null)
        }}
        onConfirm={handleConfirmDelete}
        experienceName={deletingExperience?.company || ''}
        isLoading={deleteExperienceMutation.isPending}
      />

      {/* Skills Modal */}
      <SkillsModal
        isOpen={isSkillsModalOpen}
        onClose={() => {
          setIsSkillsModalOpen(false)
          setEditingSkill(null)
        }}
        onSubmit={handleSkillSubmit}
        isLoading={createSkillMutation.isPending || updateSkillMutation.isPending}
        initialData={editingSkill || undefined}
        mode={skillsModalMode}
      />

    </div>
  )
}

export default ExperienceSkillsView

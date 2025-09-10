import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ExperienceModal from '../experience/ExperienceModal'
import DeleteConfirmationModal from '../experience/DeleteConfirmationModal'
import SkillsModal from '../skills/SkillsModal'
import CertificationsModal from '../certifications/CertificationsModal'
import CertificationDeleteConfirmationModal from '../certifications/CertificationDeleteConfirmationModal'
import PublicationsModal from '../publications/PublicationsModal'
import PublicationsDeleteConfirmationModal from '../publications/PublicationsDeleteConfirmationModal'
import EducationForm from '../education/EducationForm'
import EducationCard from '../education/EducationCard'
import WebsiteForm from '../website/WebsiteForm'
import WebsiteCard from '../website/WebsiteCard'
import ProjectModal from '../project/ProjectModal'
import ProjectDeleteConfirmationModal from '../project/DeleteConfirmationModal'
import ProjectCard from '../project/ProjectCard'
import { experienceService, type Experience, type CreateExperienceRequest } from '../../services/experienceService'
import { skillService, type Skill, type CreateSkillRequest } from '../../services/skillService'
import { certificationService, type Certification, type CreateCertificationRequest } from '../../services/certificationService'
import { publicationService, type Publication, type CreatePublicationRequest } from '../../services/publicationService'
import { educationService, type Education } from '../../services/educationService'
import { getWebsites, createWebsite, updateWebsite, deleteWebsite, type Website } from '../../services/websiteService'
import { projectService, type Project, type CreateProjectRequest } from '../../services/projectService'

const ExperienceSkillsView: React.FC = () => {
  const [isExperienceModalOpen, setIsExperienceModalOpen] = useState(false)
  const [selectedExperience, setSelectedExperience] = useState<Experience | null>(null)
  const [editingExperience, setEditingExperience] = useState<Experience | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [deletingExperience, setDeletingExperience] = useState<Experience | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [skillsModalMode, setSkillsModalMode] = useState<'create' | 'edit'>('create')
  const [expandedSkills, setExpandedSkills] = useState<Set<number>>(new Set())
  const [isCertificationsModalOpen, setIsCertificationsModalOpen] = useState(false)
  const [editingCertification, setEditingCertification] = useState<Certification | null>(null)
  const [certificationsModalMode, setCertificationsModalMode] = useState<'create' | 'edit'>('create')
  const [deletingCertification, setDeletingCertification] = useState<Certification | null>(null)
  const [isCertificationDeleteModalOpen, setIsCertificationDeleteModalOpen] = useState(false)
  const [isPublicationsModalOpen, setIsPublicationsModalOpen] = useState(false)
  const [editingPublication, setEditingPublication] = useState<Publication | null>(null)
  const [publicationsModalMode, setPublicationsModalMode] = useState<'create' | 'edit'>('create')
  const [deletingPublication, setDeletingPublication] = useState<Publication | null>(null)
  const [isPublicationDeleteModalOpen, setIsPublicationDeleteModalOpen] = useState(false)
  const [isEducationModalOpen, setIsEducationModalOpen] = useState(false)
  const [editingEducation, setEditingEducation] = useState<Education | null>(null)
  const [educationModalMode, setEducationModalMode] = useState<'create' | 'edit'>('create')
  const [deletingEducation, setDeletingEducation] = useState<Education | null>(null)
  const [, setIsEducationDeleteModalOpen] = useState(false)
  const [isWebsiteModalOpen, setIsWebsiteModalOpen] = useState(false)
  const [editingWebsite, setEditingWebsite] = useState<Website | null>(null)
  const [websiteModalMode, setWebsiteModalMode] = useState<'create' | 'edit'>('create')
  const [deletingWebsite, setDeletingWebsite] = useState<Website | null>(null)
  const [, setIsWebsiteDeleteModalOpen] = useState(false)
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [projectModalMode, setProjectModalMode] = useState<'create' | 'edit'>('create')
  const [deletingProject, setDeletingProject] = useState<Project | null>(null)
  const [isProjectDeleteModalOpen, setIsProjectDeleteModalOpen] = useState(false)
  
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

  // Fetch certifications
  const { data: certifications = [], isLoading: certificationsLoading, error: certificationsError } = useQuery({
    queryKey: ['certifications'],
    queryFn: certificationService.getCertifications,
  })

  // Create certification mutation
  const createCertificationMutation = useMutation({
    mutationFn: certificationService.createCertification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certifications'] })
      setIsCertificationsModalOpen(false)
      setEditingCertification(null)
    },
    onError: (error) => {
      console.error('Failed to create certification:', error)
      // You could add toast notification here
    }
  })

  // Update certification mutation
  const updateCertificationMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateCertificationRequest }) => 
      certificationService.updateCertification(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certifications'] })
      setIsCertificationsModalOpen(false)
      setEditingCertification(null)
    },
    onError: (error) => {
      console.error('Failed to update certification:', error)
      // You could add toast notification here
    }
  })

  // Delete certification mutation
  const deleteCertificationMutation = useMutation({
    mutationFn: (id: number) => certificationService.deleteCertification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['certifications'] })
      setIsCertificationDeleteModalOpen(false)
      setDeletingCertification(null)
    },
    onError: (error) => {
      console.error('Failed to delete certification:', error)
      // You could add toast notification here
    }
  })

  // Fetch publications
  const { data: publications = [], isLoading: publicationsLoading, error: publicationsError } = useQuery({
    queryKey: ['publications'],
    queryFn: publicationService.getPublications,
  })

  // Create publication mutation
  const createPublicationMutation = useMutation({
    mutationFn: publicationService.createPublication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
      setIsPublicationsModalOpen(false)
      setEditingPublication(null)
    },
    onError: (error) => {
      console.error('Failed to create publication:', error)
      // You could add toast notification here
    }
  })

  // Update publication mutation
  const updatePublicationMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreatePublicationRequest }) => 
      publicationService.updatePublication(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
      setIsPublicationsModalOpen(false)
      setEditingPublication(null)
    },
    onError: (error) => {
      console.error('Failed to update publication:', error)
      // You could add toast notification here
    }
  })

  // Delete publication mutation
  const deletePublicationMutation = useMutation({
    mutationFn: (id: number) => publicationService.deletePublication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
      setIsPublicationDeleteModalOpen(false)
      setDeletingPublication(null)
    },
    onError: (error) => {
      console.error('Failed to delete publication:', error)
      // You could add toast notification here
    }
  })

  // Fetch education
  const { data: education = [] } = useQuery({
    queryKey: ['education'],
    queryFn: educationService.getEducation,
  })

  // Create education mutation
  const createEducationMutation = useMutation({
    mutationFn: educationService.createEducation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['education'] })
      setIsEducationModalOpen(false)
      setEditingEducation(null)
    },
    onError: (error) => {
      console.error('Failed to create education:', error)
      // You could add toast notification here
    }
  })

  // Update education mutation
  const updateEducationMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => educationService.updateEducation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['education'] })
      setIsEducationModalOpen(false)
      setEditingEducation(null)
    },
    onError: (error) => {
      console.error('Failed to update education:', error)
      // You could add toast notification here
    }
  })

  // Delete education mutation
  const deleteEducationMutation = useMutation({
    mutationFn: (id: number) => educationService.deleteEducation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['education'] })
      setIsEducationDeleteModalOpen(false)
      setDeletingEducation(null)
    },
    onError: (error) => {
      console.error('Failed to delete education:', error)
      // You could add toast notification here
    }
  })

  // Fetch websites
  const { data: websites = [] } = useQuery<Website[]>({
    queryKey: ['websites'],
    queryFn: getWebsites,
  })

  // Fetch projects
  const { data: projects = [], isLoading: projectsLoading, error: projectsError } = useQuery({
    queryKey: ['projects'],
    queryFn: projectService.getProjects,
  })

  // Create website mutation
  const createWebsiteMutation = useMutation({
    mutationFn: createWebsite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      setIsWebsiteModalOpen(false)
      setEditingWebsite(null)
    },
    onError: (error) => {
      console.error('Failed to create website:', error)
      // You could add toast notification here
    }
  })

  // Update website mutation
  const updateWebsiteMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateWebsite(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      setIsWebsiteModalOpen(false)
      setEditingWebsite(null)
    },
    onError: (error) => {
      console.error('Failed to update website:', error)
      // You could add toast notification here
    }
  })

  // Delete website mutation
  const deleteWebsiteMutation = useMutation({
    mutationFn: deleteWebsite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
      setIsWebsiteDeleteModalOpen(false)
      setDeletingWebsite(null)
    },
    onError: (error) => {
      console.error('Failed to delete website:', error)
      // You could add toast notification here
    }
  })

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: projectService.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsProjectModalOpen(false)
      setEditingProject(null)
    },
    onError: (error) => {
      console.error('Failed to create project:', error)
      // You could add toast notification here
    }
  })

  // Update project mutation
  const updateProjectMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateProjectRequest }) => 
      projectService.updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsProjectModalOpen(false)
      setEditingProject(null)
    },
    onError: (error) => {
      console.error('Failed to update project:', error)
      // You could add toast notification here
    }
  })

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: (id: number) => projectService.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsProjectDeleteModalOpen(false)
      setDeletingProject(null)
    },
    onError: (error) => {
      console.error('Failed to delete project:', error)
      // You could add toast notification here
    }
  })

  const sections = [
    {
      id: 'education',
      title: 'Education',
      description: 'Your academic background, degrees, and educational achievements',
      icon: '🎓',
      color: 'bg-purple-50 border-purple-200',
      iconColor: 'text-purple-600',
      fields: ['Institution', 'Degree', 'Field of Study', 'Dates', 'GPA', 'Location', 'Description']
    },
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
      icon: '⚡',
      color: 'bg-green-50 border-green-200',
      iconColor: 'text-green-600',
      fields: ['Skill Name']
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
    },
    {
      id: 'websites',
      title: 'Websites',
      description: 'Your personal websites, portfolios, and online profiles',
      icon: '🌐',
      color: 'bg-cyan-50 border-cyan-200',
      iconColor: 'text-cyan-600',
      fields: ['Site Name', 'URL']
    },
    {
      id: 'projects',
      title: 'Projects',
      description: 'Personal and professional projects showcasing your skills',
      icon: '🚀',
      color: 'bg-orange-50 border-orange-200',
      iconColor: 'text-orange-600',
      fields: ['Project Name', 'Description', 'Technologies', 'URL', 'Dates']
    }
  ]

  const handleAddClick = (sectionId: string) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    if (sectionId === 'education') {
      setEducationModalMode('create')
      setEditingEducation(null)
      setIsEducationModalOpen(true)
    } else if (sectionId === 'experience') {
      setModalMode('create')
      setEditingExperience(null)
      setIsExperienceModalOpen(true)
    } else if (sectionId === 'websites') {
      setWebsiteModalMode('create')
      setEditingWebsite(null)
      setIsWebsiteModalOpen(true)
    } else if (sectionId === 'projects') {
      setProjectModalMode('create')
      setEditingProject(null)
      setIsProjectModalOpen(true)
    } else {
      // Handle other sections later
      console.log(`Add clicked for ${sectionId}`)
    }
  }

  const handleEditClick = (experience: Experience) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setModalMode('edit')
    setEditingExperience(experience)
    setIsExperienceModalOpen(true)
  }

  const handleDeleteClick = (experience: Experience) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
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
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setSkillsModalMode('create')
    setEditingSkill(null)
    setIsSkillsModalOpen(true)
  }


  const handleSkillClick = (skill: Skill) => {
    setExpandedSkills(prev => {
      const newSet = new Set(prev)
      if (newSet.has(skill.id!)) {
        newSet.delete(skill.id!)
      } else {
        newSet.add(skill.id!)
      }
      return newSet
    })
  }

  const handleDeleteSkillClick = (skill: Skill) => {
    deleteSkillMutation.mutate(skill.id!)
    // Remove from expanded set after deletion
    setExpandedSkills(prev => {
      const newSet = new Set(prev)
      newSet.delete(skill.id!)
      return newSet
    })
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

  // Certifications handlers
  const handleAddCertificationClick = () => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setCertificationsModalMode('create')
    setEditingCertification(null)
    setIsCertificationsModalOpen(true)
  }

  const handleEditCertificationClick = (certification: Certification) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setCertificationsModalMode('edit')
    setEditingCertification(certification)
    setIsCertificationsModalOpen(true)
  }

  const handleDeleteCertificationClick = (certification: Certification) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setDeletingCertification(certification)
    setIsCertificationDeleteModalOpen(true)
  }

  const handleConfirmCertificationDelete = () => {
    if (deletingCertification) {
      deleteCertificationMutation.mutate(deletingCertification.id!)
    }
  }

  const handleCertificationSubmit = async (data: CreateCertificationRequest) => {
    if (certificationsModalMode === 'edit' && editingCertification) {
      await updateCertificationMutation.mutateAsync({ 
        id: editingCertification.id!, 
        data 
      })
    } else {
      await createCertificationMutation.mutateAsync(data)
    }
  }

  // Publications handlers
  const handleAddPublicationClick = () => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setPublicationsModalMode('create')
    setEditingPublication(null)
    setIsPublicationsModalOpen(true)
  }

  const handleEditPublicationClick = (publication: Publication) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setPublicationsModalMode('edit')
    setEditingPublication(publication)
    setIsPublicationsModalOpen(true)
  }

  const handleDeletePublicationClick = (publication: Publication) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setDeletingPublication(publication)
    setIsPublicationDeleteModalOpen(true)
  }

  const handleConfirmPublicationDelete = () => {
    if (deletingPublication) {
      deletePublicationMutation.mutate(deletingPublication.id!)
    }
  }

  const handlePublicationSubmit = async (data: CreatePublicationRequest) => {
    if (publicationsModalMode === 'edit' && editingPublication) {
      await updatePublicationMutation.mutateAsync({ 
        id: editingPublication.id!, 
        data 
      })
    } else {
      await createPublicationMutation.mutateAsync(data)
    }
  }

  // Education handlers
  const handleEducationEdit = (education: Education) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setEditingEducation(education)
    setEducationModalMode('edit')
    setIsEducationModalOpen(true)
  }

  const handleEducationDelete = (education: Education) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setDeletingEducation(education)
    setIsEducationDeleteModalOpen(true)
  }

  const handleConfirmEducationDelete = () => {
    if (deletingEducation) {
      deleteEducationMutation.mutate(deletingEducation.id!)
    }
  }

  const handleEducationSubmit = async (data: any) => {
    if (educationModalMode === 'edit' && editingEducation) {
      await updateEducationMutation.mutateAsync({ 
        id: editingEducation.id!, 
        data 
      })
    } else {
      await createEducationMutation.mutateAsync(data)
    }
  }

  // Website handlers
  const handleWebsiteEdit = (website: Website) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setEditingWebsite(website)
    setWebsiteModalMode('edit')
    setIsWebsiteModalOpen(true)
  }

  const handleWebsiteDelete = (website: Website) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setDeletingWebsite(website)
    setIsWebsiteDeleteModalOpen(true)
  }

  const handleConfirmWebsiteDelete = () => {
    if (deletingWebsite) {
      deleteWebsiteMutation.mutate(deletingWebsite.id!)
    }
  }

  const handleWebsiteSubmit = async (data: any) => {
    if (websiteModalMode === 'edit' && editingWebsite) {
      await updateWebsiteMutation.mutateAsync({ 
        id: editingWebsite.id!, 
        data 
      })
    } else {
      await createWebsiteMutation.mutateAsync(data)
    }
  }

  // Project handlers
  const handleProjectEdit = (project: Project) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setEditingProject(project)
    setProjectModalMode('edit')
    setIsProjectModalOpen(true)
  }

  const handleProjectDelete = (project: Project) => {
    // Capture scroll position immediately before any state changes
    const scrollY = window.scrollY
    ;(window as any).__savedScrollPosition = scrollY
    
    setDeletingProject(project)
    setIsProjectDeleteModalOpen(true)
  }

  const handleConfirmProjectDelete = () => {
    if (deletingProject) {
      deleteProjectMutation.mutate(deletingProject.id!)
    }
  }

  const handleProjectSubmit = async (data: CreateProjectRequest) => {
    if (projectModalMode === 'edit' && editingProject) {
      await updateProjectMutation.mutateAsync({ 
        id: editingProject.id!, 
        data 
      })
    } else {
      await createProjectMutation.mutateAsync(data)
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
    const isExpanded = expandedSkills.has(skill.id!)
    
    return (
      <div 
        className="inline-block bg-white border border-gray-200 rounded-lg mr-2 mb-2 hover:shadow-md transition-all duration-200 group overflow-hidden cursor-pointer"
        onClick={() => handleSkillClick(skill)}
      >
        <div className="flex items-center px-3 py-1.5">
          <span className="text-sm font-medium text-gray-900 whitespace-nowrap">{skill.name}</span>
          <div className={`${isExpanded ? 'w-8' : 'w-0'} group-hover:w-8 transition-all duration-200 overflow-hidden`}>
            <button 
              className="text-red-600 hover:text-red-800 hover:bg-red-50 ml-2 p-1 rounded-full"
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteSkillClick(skill)
              }}
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

  const CertificationCard = ({ certification }: { certification: Certification }) => {
    return (
      <div className="w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{certification.name}</h4>
            <p className="text-sm text-gray-600 mt-1">{certification.issuer}</p>
            <p className="text-xs text-gray-500 mt-1">
              Issued: {formatDate(certification.issue_date)}
              {certification.expiry_date && ` • Expires: ${formatDate(certification.expiry_date)}`}
            </p>
            {certification.credential_id && (
              <p className="text-xs text-gray-500 mt-1">ID: {certification.credential_id}</p>
            )}
          </div>
          <div className="flex space-x-1 ml-4">
            <button 
              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
              onClick={() => handleEditCertificationClick(certification)}
            >
              Edit
            </button>
            <button 
              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
              onClick={() => handleDeleteCertificationClick(certification)}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    )
  }

  const PublicationCard = ({ publication }: { publication: Publication }) => {
    return (
      <div className="w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{publication.title}</h4>
            {publication.co_authors && (
              <p className="text-sm text-gray-600 mt-1">Co-authors: {publication.co_authors}</p>
            )}
            {publication.publisher && (
              <p className="text-sm text-gray-600 mt-1">Publisher: {publication.publisher}</p>
            )}
            <div className="flex flex-wrap gap-2 mt-1">
              {publication.publication_type && (
                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  {publication.publication_type}
                </span>
              )}
              {publication.publication_date && (
                <span className="text-xs text-gray-500">
                  {formatDate(publication.publication_date)}
                </span>
              )}
            </div>
            {publication.url && (
              <a 
                href={publication.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:text-blue-800 mt-1 block"
              >
                View Publication →
              </a>
            )}
          </div>
          <div className="flex space-x-1 ml-4">
            <button 
              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
              onClick={() => handleEditPublicationClick(publication)}
            >
              Edit
            </button>
            <button 
              className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
              onClick={() => handleDeletePublicationClick(publication)}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    )
  }

  const SectionCard = ({ section }: { section: typeof sections[0] }) => {
    const isEducationSection = section.id === 'education'
    const isExperienceSection = section.id === 'experience'
    const isSkillsSection = section.id === 'skills'
    const isCertificationsSection = section.id === 'certifications'
    const isPublicationsSection = section.id === 'publications'
    const isWebsiteSection = section.id === 'websites'
    const isProjectSection = section.id === 'projects'
    const hasData = (isEducationSection && education.length > 0) || (isExperienceSection && experiences.length > 0) || (isSkillsSection && skills.length > 0) || (isCertificationsSection && certifications.length > 0) || (isPublicationsSection && publications.length > 0) || (isWebsiteSection && websites.length > 0) || (isProjectSection && projects.length > 0)

    return (
      <div className={`border-2 rounded-lg p-6 transition-all duration-200 ${section.color}`}>
        <div className="flex items-start justify-between w-full">
          <div className="flex items-start space-x-4 w-full">
            <div className="p-2 rounded-lg bg-white border text-2xl">
              {section.icon}
            </div>
            <div className="flex-1 w-full">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{section.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{section.description}</p>
              
              {/* Show existing education */}
              {isEducationSection && hasData && (
                <div className="mb-4 w-full">
                  {education.map((edu) => (
                    <EducationCard 
                      key={edu.id} 
                      education={edu}
                      onEdit={handleEducationEdit}
                      onDelete={handleEducationDelete}
                    />
                  ))}
                </div>
              )}

              {/* Show existing websites */}
              {isWebsiteSection && hasData && (
                <div className="mb-4 w-full">
                  {websites.map((website) => (
                    <WebsiteCard 
                      key={website.id} 
                      website={website}
                      onEdit={handleWebsiteEdit}
                      onDelete={handleWebsiteDelete}
                    />
                  ))}
                </div>
              )}

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

              {/* Show existing certifications */}
              {isCertificationsSection && hasData && (
                <div className="mb-4 w-full">
                  {certifications.map((certification) => (
                    <CertificationCard key={certification.id} certification={certification} />
                  ))}
                </div>
              )}

              {/* Show existing publications */}
              {isPublicationsSection && hasData && (
                <div className="mb-4 w-full">
                  {publications.map((publication) => (
                    <PublicationCard key={publication.id} publication={publication} />
                  ))}
                </div>
              )}

              {/* Show existing projects */}
              {isProjectSection && hasData && (
                <div className="mb-4 w-full">
                  {projects.map((project) => (
                    <ProjectCard 
                      key={project.id} 
                      project={project}
                      onEdit={handleProjectEdit}
                      onDelete={handleProjectDelete}
                    />
                  ))}
                </div>
              )}
              
              
              <div className="mt-4 flex items-center justify-between">
                {isEducationSection ? (
                  <span className="text-sm text-gray-500">
                    {hasData ? `${education.length} education entr${education.length !== 1 ? 'ies' : 'y'} added` : 'No education entries added yet'}
                  </span>
                ) : isExperienceSection ? (
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
                ) : isCertificationsSection ? (
                  <span className="text-sm text-gray-500">
                    {certificationsLoading ? 'Loading...' : 
                     certificationsError ? 'Error loading certifications' :
                     hasData ? `${certifications.length} certification${certifications.length !== 1 ? 's' : ''} added` : 'No certifications added yet'}
                  </span>
                ) : isPublicationsSection ? (
                  <span className="text-sm text-gray-500">
                    {publicationsLoading ? 'Loading...' : 
                     publicationsError ? 'Error loading publications' :
                     hasData ? `${publications.length} publication${publications.length !== 1 ? 's' : ''} added` : 'No publications added yet'}
                  </span>
                ) : isWebsiteSection ? (
                  <span className="text-sm text-gray-500">
                    {hasData ? `${websites.length} website${websites.length !== 1 ? 's' : ''} added` : 'No websites added yet'}
                  </span>
                ) : isProjectSection ? (
                  <span className="text-sm text-gray-500">
                    {projectsLoading ? 'Loading...' : 
                     projectsError ? 'Error loading projects' :
                     hasData ? `${projects.length} project${projects.length !== 1 ? 's' : ''} added` : 'No projects added yet'}
                  </span>
                ) : (
                  <span className="text-sm text-gray-500">No entries added yet</span>
                )}
              </div>
            </div>
          </div>
          <button 
            onClick={() => 
              isEducationSection ? handleAddClick(section.id) :
              isWebsiteSection ? handleAddClick(section.id) :
              isProjectSection ? handleAddClick(section.id) :
              isSkillsSection ? handleAddSkillClick() : 
              isCertificationsSection ? handleAddCertificationClick() : 
              isPublicationsSection ? handleAddPublicationClick() :
              handleAddClick(section.id)
            }
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
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Experience & Skills Catalogue</h2>
        <p className="text-gray-600 text-lg">
          Build your comprehensive professional profile by organizing your experience, skills, and achievements.
        </p>
      </div>

      <div className="space-y-6">
        {sections.map((section) => (
          <SectionCard key={section.id} section={section} />
        ))}
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

      {/* Certifications Modal */}
      <CertificationsModal
        isOpen={isCertificationsModalOpen}
        onClose={() => {
          setIsCertificationsModalOpen(false)
          setEditingCertification(null)
        }}
        onSubmit={handleCertificationSubmit}
        isLoading={createCertificationMutation.isPending || updateCertificationMutation.isPending}
        initialData={editingCertification || undefined}
        mode={certificationsModalMode}
      />

      {/* Certification Delete Confirmation Modal */}
      <CertificationDeleteConfirmationModal
        isOpen={isCertificationDeleteModalOpen}
        onClose={() => {
          setIsCertificationDeleteModalOpen(false)
          setDeletingCertification(null)
        }}
        onConfirm={handleConfirmCertificationDelete}
        certification={deletingCertification}
        isLoading={deleteCertificationMutation.isPending}
      />

      {/* Publications Modal */}
      <PublicationsModal
        isOpen={isPublicationsModalOpen}
        onClose={() => {
          setIsPublicationsModalOpen(false)
          setEditingPublication(null)
        }}
        onSubmit={handlePublicationSubmit}
        isLoading={createPublicationMutation.isPending || updatePublicationMutation.isPending}
        initialData={editingPublication || undefined}
        mode={publicationsModalMode}
      />

      {/* Publication Delete Confirmation Modal */}
      <PublicationsDeleteConfirmationModal
        isOpen={isPublicationDeleteModalOpen}
        onClose={() => {
          setIsPublicationDeleteModalOpen(false)
          setDeletingPublication(null)
        }}
        onConfirm={handleConfirmPublicationDelete}
        publication={deletingPublication}
        isLoading={deletePublicationMutation.isPending}
      />

      {/* Education Form Modal */}
      <EducationForm
        isOpen={isEducationModalOpen}
        onClose={() => {
          setIsEducationModalOpen(false)
          setEditingEducation(null)
        }}
        onSuccess={handleEducationSubmit}
        initialData={editingEducation}
      />

      {/* Education Delete Confirmation Modal */}
      {deletingEducation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => {
              setIsEducationDeleteModalOpen(false)
              setDeletingEducation(null)
            }}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Education</h3>
                <p className="text-sm text-gray-500">This action cannot be undone.</p>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-gray-700">
                Are you sure you want to delete <strong>{deletingEducation.degree}</strong> from <strong>{deletingEducation.institution}</strong>?
              </p>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setIsEducationDeleteModalOpen(false)
                  setDeletingEducation(null)
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmEducationDelete}
                disabled={deleteEducationMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {deleteEducationMutation.isPending ? 'Deleting...' : 'Delete Education'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Website Form Modal */}
      <WebsiteForm
        isOpen={isWebsiteModalOpen}
        onClose={() => {
          setIsWebsiteModalOpen(false)
          setEditingWebsite(null)
        }}
        onSuccess={handleWebsiteSubmit}
        initialData={editingWebsite}
      />

      {/* Website Delete Confirmation Modal */}
      {deletingWebsite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => {
              setIsWebsiteDeleteModalOpen(false)
              setDeletingWebsite(null)
            }}
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Website</h3>
                <p className="text-sm text-gray-500">This action cannot be undone.</p>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-gray-700">
                Are you sure you want to delete <strong>{deletingWebsite.site_name}</strong>?
              </p>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setIsWebsiteDeleteModalOpen(false)
                  setDeletingWebsite(null)
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmWebsiteDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-lg hover:bg-red-700 transition-colors duration-200"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Project Modal */}
      <ProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => {
          setIsProjectModalOpen(false)
          setEditingProject(null)
        }}
        onSubmit={handleProjectSubmit}
        isLoading={createProjectMutation.isPending || updateProjectMutation.isPending}
        initialData={editingProject ? {
          name: editingProject.name,
          description: editingProject.description || '',
          start_date: editingProject.start_date,
          end_date: editingProject.end_date || '',
          url: editingProject.url || '',
          is_current: editingProject.is_current,
          technologies: editingProject.technologies.map(t => ({
            technology: t.technology
          })),
          achievements: editingProject.achievements.map(a => ({
            description: a.description
          }))
        } : undefined}
        mode={projectModalMode}
      />

      {/* Project Delete Confirmation Modal */}
      <ProjectDeleteConfirmationModal
        isOpen={isProjectDeleteModalOpen}
        onClose={() => {
          setIsProjectDeleteModalOpen(false)
          setDeletingProject(null)
        }}
        onConfirm={handleConfirmProjectDelete}
        projectName={deletingProject?.name || ''}
        isLoading={deleteProjectMutation.isPending}
      />

    </div>
  )
}

export default ExperienceSkillsView

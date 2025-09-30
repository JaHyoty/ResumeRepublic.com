import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { resumeService } from '../../services/resumeService'
import { skillService } from '../../services/skillService'

interface KeywordAnalysisProps {
  jobDescription: string
  onComplete: (keywords: string[], selectedSkills: string[]) => void
  isCompleted?: boolean
  analyzedKeywords?: string[]
  selectedSkills?: string[]
}

const KeywordAnalysis: React.FC<KeywordAnalysisProps> = ({ 
  jobDescription, 
  onComplete,
  isCompleted = false,
  analyzedKeywords = [],
  selectedSkills = []
}) => {
  const [keywords, setKeywords] = useState<string[]>([])
  const [localSelectedSkills, setLocalSelectedSkills] = useState<Set<string>>(new Set())
  const [isAnalyzing, setIsAnalyzing] = useState(!isCompleted)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [isSavingSkills, setIsSavingSkills] = useState(false)

  // Get user's current skills
  const { data: userSkills = [], isLoading: skillsLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: skillService.getSkills,
  })

  // Initialize keywords from props if completed, otherwise analyze
  useEffect(() => {
    if (isCompleted && analyzedKeywords.length > 0) {
      setKeywords(analyzedKeywords)
      setIsAnalyzing(false)
    } else if (!isCompleted) {
      const analyzeKeywords = async () => {
        if (!jobDescription.trim()) {
          setAnalysisError('No job description provided')
          setIsAnalyzing(false)
          return
        }

        try {
          setIsAnalyzing(true)
          setAnalysisError(null)
          const extractedKeywords = await resumeService.analyzeKeywords(jobDescription)
          setKeywords(extractedKeywords)
        } catch (error) {
          console.error('Error analyzing keywords:', error)
          setAnalysisError(error instanceof Error ? error.message : 'Failed to analyze keywords')
        } finally {
          setIsAnalyzing(false)
        }
      }

      analyzeKeywords()
    }
  }, [jobDescription, isCompleted, analyzedKeywords])

  // Find missing skills (keywords not in user's current skills)
  const missingSkills = keywords.filter(keyword => 
    !userSkills.some(skill => 
      skill.name.toLowerCase() === keyword.toLowerCase()
    )
  )

  const handleSkillToggle = (skill: string) => {
    setLocalSelectedSkills(prev => {
      const newSet = new Set(prev)
      if (newSet.has(skill)) {
        newSet.delete(skill)
      } else {
        newSet.add(skill)
      }
      return newSet
    })
  }

  const handleSaveAndContinue = async () => {
    const selectedSkillsArray = Array.from(localSelectedSkills)
    
    if (selectedSkillsArray.length === 0) {
      onComplete(keywords, [])
      return
    }

    try {
      setIsSavingSkills(true)
      await skillService.createSkillsBulk(selectedSkillsArray)
      onComplete(keywords, selectedSkillsArray)
    } catch (error) {
      console.error('Error saving skills:', error)
      // Continue anyway, don't block the user
      onComplete(keywords, selectedSkillsArray)
    } finally {
      setIsSavingSkills(false)
    }
  }

  if (isAnalyzing) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Analyzing for keywords</h3>
          <p className="text-gray-600">
            Our AI is analyzing the job description to identify key skills and technologies...
          </p>
        </div>
      </div>
    )
  }

  if (analysisError) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Keyword Analysis Failed</h3>
          <p className="text-red-600 mb-6">{analysisError}</p>
          <div className="flex justify-center">
            <button
              onClick={() => onComplete([], [])}
              className="bg-blue-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Continue Without Analysis
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (skillsLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your current skills...</p>
        </div>
      </div>
    )
  }

  // If completed, show summary view
  if (isCompleted) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Keyword Analysis Summary</h3>
          <div className="text-sm text-gray-600">
            {selectedSkills.length > 0 && (
              <span className="text-green-600 font-medium">
                {selectedSkills.length} skill{selectedSkills.length !== 1 ? 's' : ''} added to profile
              </span>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {keywords.map((keyword) => {
            const isUserSkill = userSkills.some(skill => 
              skill.name.toLowerCase() === keyword.toLowerCase()
            )
            const wasSelected = selectedSkills.includes(keyword)
            
            return (
              <span
                key={keyword}
                className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${isUserSkill || wasSelected
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                  }
                `}
              >
                {keyword}
                {(isUserSkill || wasSelected) && (
                  <span className="ml-1">✓</span>
                )}
              </span>
            )
          })}
        </div>
        
        {selectedSkills.length > 0 && (
          <div className="mt-4 p-3 bg-green-50 rounded-lg">
            <p className="text-sm text-green-800">
              <strong>Added to your profile:</strong> {selectedSkills.join(', ')}
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-8">
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Keyword Analysis Complete</h3>
        <p className="text-gray-600">
          We found {keywords.length} key skills in the job description
        </p>
      </div>

      {missingSkills.length > 0 ? (
        <div>
          <div className="mb-6">
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Key skills missing from your profile
            </h4>
            <p className="text-gray-600 mb-4">
              Strengthen your application by clicking on the skills that you wish to add to your profile
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
            {missingSkills.map((skill) => (
              <button
                key={skill}
                onClick={() => handleSkillToggle(skill)}
                className={`
                  px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200
                  ${localSelectedSkills.has(skill)
                    ? 'bg-green-100 text-green-800 border-2 border-green-300'
                    : 'bg-red-50 text-red-700 border-2 border-red-200 hover:bg-red-100'
                  }
                `}
              >
                {skill}
                {localSelectedSkills.has(skill) && (
                  <span className="ml-2">✓</span>
                )}
              </button>
            ))}
          </div>

          <div className="flex justify-center">
            <button
              onClick={handleSaveAndContinue}
              disabled={isSavingSkills}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSavingSkills ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {localSelectedSkills.size > 0 ? 'Saving Skills...' : 'Continuing...'}
                </div>
              ) : (
                'Continue Generating Resume'
              )}
            </button>
          </div>

          {localSelectedSkills.size > 0 && (
            <div className="mt-4 text-center text-sm text-gray-600">
              {localSelectedSkills.size} skill{localSelectedSkills.size !== 1 ? 's' : ''} selected
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="text-center mb-6">
            <div className="text-green-500 text-6xl mb-4">✅</div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Great! You already have all the key skills
            </h4>
            <p className="text-gray-600">
              Your profile contains all the important skills mentioned in the job description.
            </p>
          </div>

          <div className="flex justify-center">
            <button
              onClick={() => onComplete(keywords, [])}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Continue Generating Resume
            </button>
          </div>
        </div>
      )}

      {keywords.length > 0 && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h5 className="text-sm font-medium text-gray-700 mb-3">All identified keywords:</h5>
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword) => (
              <span
                key={keyword}
                className={`
                  px-3 py-1 rounded-full text-xs font-medium
                  ${userSkills.some(skill => skill.name.toLowerCase() === keyword.toLowerCase())
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                  }
                `}
              >
                {keyword}
                {userSkills.some(skill => skill.name.toLowerCase() === keyword.toLowerCase()) && (
                  <span className="ml-1">✓</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default KeywordAnalysis

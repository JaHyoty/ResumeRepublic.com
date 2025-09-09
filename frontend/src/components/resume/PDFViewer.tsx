import React, { useState, useEffect } from 'react'

interface PDFViewerProps {
  pdfUrl: string
  className?: string
  id?: string
  onReady?: () => void
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, className = '', id, onReady }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    console.log('PDFViewer: pdfUrl changed to:', pdfUrl)
    if (pdfUrl) {
      setLoading(true)
      setError(null)
      
      // Test if the blob URL is accessible
      fetch(pdfUrl)
        .then(response => {
          console.log('PDF blob fetch response:', response.status, response.ok)
          if (!response.ok) {
            throw new Error(`Failed to fetch PDF: ${response.status}`)
          }
          return response.blob()
        })
        .then(blob => {
          console.log('PDF blob size:', blob.size, 'type:', blob.type)
          if (blob.size === 0) {
            throw new Error('PDF blob is empty')
          }
          setLoading(false)
          // Notify parent that PDF viewer is ready
          if (onReady) {
            onReady()
          }
        })
        .catch(err => {
          console.error('PDF blob fetch error:', err)
          setError('Failed to load PDF blob')
          setLoading(false)
        })
    }
  }, [pdfUrl])

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-96 bg-gray-100 rounded-lg ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading PDF...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-96 bg-red-50 rounded-lg ${className}`}>
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div id={id} className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* PDF Content using iframe */}
      <div className="p-4 bg-gray-100 flex justify-center">
        <div className="w-full max-w-4xl">
          <div className="relative w-full overflow-hidden rounded-lg shadow-lg" style={{ aspectRatio: '8.5/11' }}>
            <iframe
              src={`${pdfUrl}#view=FitH&zoom=FitH`}
              className="absolute inset-0 w-full h-full border-0"
              title="Resume PDF Preview"
              style={{
                border: 'none',
                borderRadius: '8px',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
                overflow: 'hidden',
                width: '100%',
                height: '100%',
                objectFit: 'contain'
              }}
              onLoad={() => {
                console.log('PDF iframe loaded successfully')
                setLoading(false)
              }}
              onError={() => {
                console.error('PDF iframe failed to load')
                setError('Failed to load PDF in iframe')
                setLoading(false)
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default PDFViewer

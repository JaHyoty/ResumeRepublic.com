import React from 'react'
import { type Website } from '../../services/websiteService'

interface WebsiteCardProps {
  website: Website
  onEdit: (website: Website) => void
  onDelete: (website: Website) => void
}

const WebsiteCard: React.FC<WebsiteCardProps> = ({
  website,
  onEdit,
  onDelete
}) => {
  return (
    <div className="w-full bg-white border rounded-lg p-3 mb-2 hover:shadow-md transition-all">
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{website.site_name}</h4>
          <p className="text-sm text-blue-600 mt-1">
            <a
              href={website.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-800 transition-colors duration-200"
            >
              {website.url}
            </a>
          </p>
        </div>
        <div className="flex space-x-1 ml-4">
          <button
            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
            onClick={(e) => {
              e.stopPropagation()
              onEdit(website)
            }}
          >
            Edit
          </button>
          <button
            className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(website)
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default WebsiteCard

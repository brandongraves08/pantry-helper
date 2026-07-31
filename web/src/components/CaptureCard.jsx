import { Camera, Clock, MapPin, Calendar } from 'lucide-react'
import { format } from 'date-fns'

const CaptureCard = ({ capture }) => {
  if (!capture) return null

  const { 
    id, 
    image_url, 
    device_id, 
    zone_id,
    notes,
    created_at,
    analysis_result
  } = capture

  const formattedDate = created_at 
    ? format(new Date(created_at), 'MMM d, yyyy - h:mm a')
    : 'Unknown date'

  return (
    <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {image_url && (
        <div className="aspect-video bg-gray-100">
          <img 
            src={image_url} 
            alt={`Capture ${id}`}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      )}
      
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Camera size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-900">
              Capture #{id.slice(0, 8)}
            </span>
          </div>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            analysis_result 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {analysis_result ? 'Analyzed' : 'Pending'}
          </span>
        </div>

        {notes && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {notes}
          </p>
        )}

        <div className="space-y-2 text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <Calendar size={14} />
            <span>{formattedDate}</span>
          </div>
          
          {device_id && (
            <div className="flex items-center gap-2">
              <Camera size={14} />
              <span>Device: {device_id.slice(0, 8)}</span>
            </div>
          )}
          
          {zone_id && (
            <div className="flex items-center gap-2">
              <MapPin size={14} />
              <span>Zone: {zone_id.slice(0, 8)}</span>
            </div>
          )}
        </div>

        {analysis_result && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-700 mb-2">
              Analysis: {analysis_result.detected_items?.length || 0} items
            </p>
            {analysis_result.detected_items?.slice(0, 3).map((item, idx) => (
              <div key={idx} className="inline-block mr-2 mb-1">
                <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                  {item}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default CaptureCard

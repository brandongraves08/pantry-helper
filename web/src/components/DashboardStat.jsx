import { use } from 'react'

/**
 * DashboardStat - A stat card component
 */
const DashboardStat = ({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  iconColor = 'text-blue-600', 
  loading = false 
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="mt-2">
            {loading ? (
              <div className="h-6 bg-gray-200 rounded w-24 skeleton" />
            ) : (
              <p className="text-2xl font-semibold text-gray-900">{value}</p>
            )}
          </div>
          <p className="mt-1 text-xs text-gray-500">{subtitle}</p>
        </div>
        <div className={`p-3 rounded-full bg-blue-50 ${iconColor}`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  )
}

export default DashboardStat

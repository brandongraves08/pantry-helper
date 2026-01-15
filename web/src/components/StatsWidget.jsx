import React from 'react'
import { TrendingUp, AlertCircle, Package, Clock } from 'lucide-react'

const StatsWidget = ({ title, value, icon: Icon, color = 'blue', trend = null }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    red: 'bg-red-50 text-red-600 border-red-200',
  }

  return (
    <div className={`${colorClasses[color]} rounded-lg border p-6 shadow-sm`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold">{value}</p>
          {trend && (
            <p className="mt-1 flex items-center text-sm text-green-600">
              <TrendingUp className="mr-1 h-4 w-4" />
              {trend}
            </p>
          )}
        </div>
        <div className="text-4xl opacity-20">
          <Icon className="h-12 w-12" />
        </div>
      </div>
    </div>
  )
}

export default StatsWidget

import React, { useState, useEffect } from 'react'
import { CheckCircle, AlertCircle, Clock, Loader } from 'lucide-react'
import api from '../api'

const TaskMonitor = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchTasks = async () => {
    try {
      const response = await api.get('/v1/admin/tasks')
      setTasks(response.data.tasks || [])
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'FAILURE':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'PENDING':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'STARTED':
        return <Loader className="h-5 w-5 animate-spin text-blue-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'SUCCESS':
        return 'bg-green-50 border-green-200'
      case 'FAILURE':
        return 'bg-red-50 border-red-200'
      case 'PENDING':
      case 'STARTED':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const filteredTasks = tasks.filter((task) => {
    if (filter === 'all') return true
    return task.status.toLowerCase() === filter.toLowerCase()
  })

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Task Queue</h3>
        <button
          onClick={fetchTasks}
          className="px-3 py-1 rounded text-sm font-medium bg-blue-500 text-white hover:bg-blue-600"
        >
          Refresh
        </button>
      </div>

      <div className="mb-4 flex gap-2">
        {['all', 'pending', 'started', 'success', 'failure'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm font-medium capitalize ${
              filter === f ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="max-h-96 space-y-2 overflow-y-auto">
        {filteredTasks.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-gray-500">No tasks found</p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div key={task.id} className={`border rounded-lg p-4 flex items-center justify-between ${getStatusColor(task.status)}`}>
              <div className="flex items-center gap-3">
                {getStatusIcon(task.status)}
                <div>
                  <p className="font-medium text-gray-900">{task.name}</p>
                  <p className="text-xs text-gray-500">{task.id}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold text-gray-600">{task.status}</p>
                <p className="text-xs text-gray-500">
                  {task.created_at ? new Date(task.created_at).toLocaleTimeString() : '—'}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default TaskMonitor

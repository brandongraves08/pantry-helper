import { useState, useEffect } from 'react'
import { Activity, Battery, Wifi, Camera, AlertCircle, CheckCircle, Clock, Trash2 } from 'lucide-react'
import api from '../api'

const DeviceDashboard = () => {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [healthData, setHealthData] = useState(null)

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchDevices = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/v1/devices')
      setDevices(response.data.items || [])
    } catch (err) {
      setError('Failed to load devices: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchDeviceHealth = async (deviceId) => {
    try {
      const response = await api.get(`/v1/devices/${deviceId}/health`)
      setHealthData(response.data)
    } catch (err) {
      console.error('Failed to load device health:', err)
    }
  }

  const handleDeviceClick = async (device) => {
    setSelectedDevice(device)
    await fetchDeviceHealth(device.id)
  }

  const handleDeleteDevice = async (deviceId) => {
    if (!confirm('Are you sure you want to delete this device?')) return
    
    try {
      await api.delete(`/v1/devices/${deviceId}`)
      setDevices(devices.filter(d => d.id !== deviceId))
      if (selectedDevice?.id === deviceId) {
        setSelectedDevice(null)
        setHealthData(null)
      }
    } catch (err) {
      alert('Failed to delete device: ' + err.message)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100'
      case 'idle':
        return 'text-yellow-600 bg-yellow-100'
      case 'inactive':
        return 'text-orange-600 bg-orange-100'
      case 'offline':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5" />
      case 'idle':
        return <Clock className="w-5 h-5" />
      case 'inactive':
      case 'offline':
        return <AlertCircle className="w-5 h-5" />
      default:
        return <Activity className="w-5 h-5" />
    }
  }

  const getBatteryColor = (percentage) => {
    if (percentage >= 60) return 'text-green-600'
    if (percentage >= 30) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  if (loading && devices.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading devices...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Device List */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Camera className="w-6 h-6" />
            Devices ({devices.length})
          </h2>
          
          {devices.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              No devices registered
            </div>
          ) : (
            <div className="space-y-3">
              {devices.map((device) => (
                <div
                  key={device.id}
                  onClick={() => handleDeviceClick(device)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                    selectedDevice?.id === device.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{device.name}</div>
                      <div className="text-sm text-gray-500 font-mono mt-1">
                        {device.id}
                      </div>
                    </div>
                    
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
                      {getStatusIcon(device.status)}
                      {device.status}
                    </div>
                  </div>

                  <div className="mt-3 flex items-center gap-4 text-sm text-gray-600">
                    {device.battery_pct !== null && (
                      <div className={`flex items-center gap-1 ${getBatteryColor(device.battery_pct)}`}>
                        <Battery className="w-4 h-4" />
                        {device.battery_pct}%
                      </div>
                    )}
                    
                    {device.rssi && (
                      <div className="flex items-center gap-1">
                        <Wifi className="w-4 h-4" />
                        {device.rssi} dBm
                      </div>
                    )}
                  </div>

                  {device.last_seen_at && (
                    <div className="mt-2 text-xs text-gray-500">
                      Last seen: {formatDate(device.last_seen_at)}
                    </div>
                  )}

                  <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                    <span>{device.capture_count || 0} captures</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteDevice(device.id)
                      }}
                      className="text-red-600 hover:text-red-800 p-1"
                      title="Delete device"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Device Details & Health */}
      <div className="lg:col-span-2">
        {selectedDevice ? (
          <div className="space-y-6">
            {/* Device Info Card */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-bold mb-4">Device Details</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Device ID</label>
                  <div className="font-mono text-sm mt-1">{selectedDevice.id}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Name</label>
                  <div className="font-medium mt-1">{selectedDevice.name}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Status</label>
                  <div className="mt-1">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedDevice.status)}`}>
                      {getStatusIcon(selectedDevice.status)}
                      {selectedDevice.status}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Registered</label>
                  <div className="text-sm mt-1">
                    {new Date(selectedDevice.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Health Metrics */}
            {healthData && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Health Metrics
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Battery</div>
                    <div className={`text-2xl font-bold ${getBatteryColor(healthData.battery_pct || 0)}`}>
                      {healthData.battery_pct || 0}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {healthData.battery_v?.toFixed(2) || 0}V
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Signal</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {healthData.rssi || 0}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">dBm</div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Captures (7d)</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {healthData.captures_7d || 0}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {healthData.success_rate_7d || 0}% success
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Captures (24h)</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {healthData.captures_24h || 0}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {healthData.success_rate_24h || 0}% success
                    </div>
                  </div>
                </div>

                <div className={`flex items-center gap-2 p-4 rounded-lg ${
                  healthData.is_healthy 
                    ? 'bg-green-50 text-green-800' 
                    : 'bg-red-50 text-red-800'
                }`}>
                  {healthData.is_healthy ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <AlertCircle className="w-5 h-5" />
                  )}
                  <span className="font-medium">
                    {healthData.is_healthy ? 'Device is healthy' : 'Device requires attention'}
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12">
            <div className="text-center text-gray-500">
              <Camera className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Select a device to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DeviceDashboard

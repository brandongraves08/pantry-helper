import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Health Check
export const checkHealth = async () => {
  const { data } = await apiClient.get('/health')
  return data
}

// Ingest API - Image Upload
export const uploadImage = async (file, metadata = {}) => {
  const formData = new FormData()
  formData.append('file', file)
  
  if (metadata.deviceId) {
    formData.append('device_id', metadata.deviceId)
  }
  if (metadata.zoneId) {
    formData.append('zone_id', metadata.zoneId)
  }
  if (metadata.notes) {
    formData.append('notes', metadata.notes)
  }

  const { data } = await apiClient.post('/v1/ingest', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

// Devices API
export const listDevices = async () => {
  const { data } = await apiClient.get('/v1/devices')
  return data
}

export const getDevice = async (id) => {
  const { data } = await apiClient.get(`/v1/devices/${id}`)
  return data
}

// Inventory API
export const listInventory = async (params = {}) => {
  const { data } = await apiClient.get('/v1/inventory', { params })
  return data
}

export const getInventoryItem = async (id) => {
  const { data } = await apiClient.get(`/v1/inventory/${id}`)
  return data
}

// Captures API
export const listCaptures = async (params = {}) => {
  const { data } = await apiClient.get('/v1/captures', { params })
  return data
}

export const getCapture = async (id) => {
  const { data } = await apiClient.get(`/v1/captures/${id}`)
  return data
}

export const deleteCapture = async (id) => {
  const { data } = await apiClient.delete(`/v1/captures/${id}`)
  return data
}

// Zones API
export const listZones = async () => {
  const { data } = await apiClient.get('/v1/zones')
  return data
}

export const getZonesByDevice = async (deviceId) => {
  const { data } = await apiClient.get(`/v1/zones/device/${deviceId}`)
  return data
}

export const getZone = async (id) => {
  const { data } = await apiClient.get(`/v1/zones/${id}`)
  return data
}

// Household API
export const listMembers = async () => {
  const { data } = await apiClient.get('/v1/household/members')
  return data
}

export default apiClient

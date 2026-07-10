import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

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
  formData.append('image', file)
  
  if (metadata.deviceId) {
    formData.append('device_id', metadata.deviceId)
  }
  if (metadata.notes) {
    formData.append('notes', metadata.notes)
  }

  const { data } = await apiClient.post('/v1/captures/manual', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export const overrideInventory = async (payload) => {
  const { data } = await apiClient.post('/v1/inventory/override', payload)
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

// Barcode API
export const lookupBarcode = async (barcode) => {
  const { data } = await apiClient.get(`/v1/barcode/${encodeURIComponent(barcode)}`)
  return data
}

export const linkBarcodeToItem = async (barcode, inventoryItemName) => {
  const { data } = await apiClient.post('/v1/barcode/link', { barcode, inventory_item_name: inventoryItemName })
  return data
}

export const addBarcodeToInventory = async (payload) => {
  const { data } = await apiClient.post('/v1/barcode/add-to-inventory', payload)
  return data
}

// ── Detections API (per-item vision review) ────────────────────────

export const listDetections = async (captureId) => {
  const { data } = await apiClient.get(`/v1/captures/${captureId}/detections`)
  return data
}

export const approveDetection = async (captureId, index, overrides = {}) => {
  const { data } = await apiClient.post(`/v1/captures/${captureId}/detections/${index}/approve`, overrides)
  return data
}

export const rejectDetection = async (captureId, index) => {
  const { data } = await apiClient.post(`/v1/captures/${captureId}/detections/${index}/reject`)
  return data
}

export const editDetection = async (captureId, index, payload) => {
  const { data } = await apiClient.post(`/v1/captures/${captureId}/detections/${index}/edit`, payload)
  return data
}

// ── Nutrition API ───────────────────────────────────────────────────

export const lookupNutrition = async (query, limit = 5) => {
  const { data } = await apiClient.get('/v1/nutrition/lookup', { params: { q: query, limit } })
  return data
}

export const getItemNutrition = async (itemId) => {
  const { data } = await apiClient.get(`/v1/inventory/${itemId}/nutrition`)
  return data
}

export const saveItemNutrition = async (itemId, payload) => {
  const { data } = await apiClient.post(`/v1/inventory/${itemId}/nutrition`, payload)
  return data
}

export default apiClient

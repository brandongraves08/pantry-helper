import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const getHealth = () => api.get('/health');

// Devices
export const getDevices = () => api.get('/v1/devices');

// Ingest - Image upload
export const uploadImage = (formData) => api.post('/v1/ingest', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});

// Captures
export const getCaptures = (params) => api.get('/v1/captures', { params });
export const getCapture = (id) => api.get(`/v1/captures/${id}`);

// Inventory
export const getInventory = () => api.get('/v1/inventory');
export const getInventoryItem = (id) => api.get(`/v1/inventory/${id}`);

// Zones
export const getZones = (deviceId) => api.get(`/v1/zones/device/${deviceId}`);
export const createZone = (deviceId, data) => api.post(`/v1/zones/device/${deviceId}`, data);
export const deleteZone = (zoneId) => api.delete(`/v1/zones/${zoneId}`);
export const getZonePatterns = (zoneId) => api.get(`/v1/zones/${zoneId}/patterns`);

// Reviews
export const getPendingReviews = () => api.get('/v1/reviews/pending');
export const approveReview = (id, data) => api.post(`/v1/reviews/${id}/approve`, data);
export const rejectReview = (id, data) => api.post(`/v1/reviews/${id}/reject`, data);

// Household
export const getMembers = () => api.get('/v1/household/members');
export const createMember = (data) => api.post('/v1/household/members', data);
export const updateMember = (id, data) => api.patch(`/v1/household/members/${id}`, data);
export const deleteMember = (id) => api.delete(`/v1/household/members/${id}`);
export const getMemberRestrictions = (id) => api.get(`/v1/household/members/${id}/restrictions`);
export const addRestriction = (id, data) => api.post(`/v1/household/members/${id}/restrictions`, data);
export const getNutritionTarget = (id) => api.get(`/v1/household/members/${id}/nutrition`);
export const setNutritionTarget = (id, data) => api.post(`/v1/household/members/${id}/nutrition`, data);

// Supply forecasting (future)
export const getConsumption = (params) => api.get('/v1/consumption', { params });

export default api;

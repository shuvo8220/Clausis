import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Document APIs
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await api.delete(`/documents/${documentId}`);
  return response.data;
};

// Draft APIs
export const generateDraft = async (payload) => {
  const response = await api.post('/drafts/generate', payload);
  return response.data;
};

export const getDraft = async (draftId) => {
  const response = await api.get(`/drafts/${draftId}`);
  return response.data;
};

export const submitEdit = async (draftId, editData) => {
  const response = await api.post(`/drafts/${draftId}/edit`, editData);
  return response.data;
};

// Pattern APIs
export const getPatterns = async () => {
  const response = await api.get('/patterns');
  return response.data;
};

export const extractPatterns = async (payload) => {
  const response = await api.post('/patterns/extract', payload);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;

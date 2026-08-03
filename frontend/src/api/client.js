import axios from 'axios';

// Base API configuration pointing to FastAPI server
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes timeout for AI vision inference
});

// Helper API methods
export const api = {
  // Check API health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Submit classroom image and metadata for analysis
  analyzeClassroom: async (formData) => {
    const res = await apiClient.post('/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // Fetch list of past analysis sessions
  getSessions: async (params = {}) => {
    const res = await apiClient.get('/sessions', { params });
    return res.data;
  },

  // Fetch details for a specific session
  getSessionDetails: async (sessionId) => {
    const res = await apiClient.get(`/sessions/${sessionId}`);
    return res.data;
  },

  // Fetch all unique institutions
  getInstitutions: async () => {
    const res = await apiClient.get('/institutions');
    return res.data;
  },

  // Fetch institution summary metrics
  getInstitutionSummary: async (institutionName) => {
    const res = await apiClient.get(`/institutions/${encodeURIComponent(institutionName)}/summary`);
    return res.data;
  },
};

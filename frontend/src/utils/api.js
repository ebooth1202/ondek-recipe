// frontend/src/utils/api.js - Updated with missing endpoints
import axios from 'axios';

// API Configuration
export const API_BASE_URL = 'http://127.0.0.1:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  ME: '/auth/me',
  LOGOUT: '/auth/logout',

  // Recipe endpoints
  RECIPES: '/recipes',
  RECIPE_BY_ID: (id) => `/recipes/${id}`,
  RECIPE_RATINGS: (id) => `/recipes/${id}/ratings`,
  RECIPE_RATINGS_SUMMARY: (id) => `/recipes/${id}/ratings/summary`,
  RECIPE_FAVORITE: (id) => `/recipes/${id}/favorite`,
  RECIPE_FAVORITE_STATUS: (id) => `/recipes/${id}/favorite-status`,

  // User endpoints
  USERS: '/users',
  USER_BY_ID: (id) => `/users/${id}`,
  USER_FAVORITES: '/users/me/favorites',

  // AI endpoints (ADDED)
  AI_CHAT: '/ai/chat',
  AI_STATUS: '/ai/status',
  AI_UPLOAD_FILE: '/ai/upload-recipe-file',
  AI_RECIPE_SUGGESTIONS: '/ai/recipe-suggestions',
  AI_PARSE_RECIPE: '/ai/parse-recipe',

  // Temp recipe endpoints (ADDED)
  TEMP_RECIPE: (id) => `/temp-recipe/${id}`,
  STORE_TEMP_RECIPE: '/store-temp-recipe',

  // Utility endpoints
  MEASURING_UNITS: '/measuring-units',
  GENRES: '/genres',
  HEALTH: '/health' // ADDED for testing
};

// Helper function to build full URL
export const buildApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`;
};

// Axios instance configuration (optional - for future use)
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Connection test helper (ADDED)
export const testConnection = async () => {
  console.log('🔍 Testing backend connection...');
  console.log('API Base URL:', API_BASE_URL);

  try {
    // Test health endpoint
    const response = await axios.get(buildApiUrl(API_ENDPOINTS.HEALTH));
    console.log('✅ Backend connection successful:', response.data);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('❌ Backend connection failed:', error.message);
    return {
      success: false,
      error: error.message,
      suggestions: [
        'Make sure backend is running: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000',
        'Check if port 8000 is accessible',
        'Verify backend URL: ' + API_BASE_URL
      ]
    };
  }
};
// frontend/src/utils/api.js - Updated for production deployment
import axios from 'axios';

// API Configuration - Updated to work in both development and production
export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? window.location.origin  // Use same domain in production
  : 'http://127.0.0.1:8000'; // Local development

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
  USER_ROLE: (id) => `/users/${id}/role`,

  // AI endpoints
  AI_CHAT: '/ai/chat',
  AI_STATUS: '/ai/status',
  AI_UPLOAD_FILE: '/ai/upload-recipe-file',
  AI_RECIPE_SUGGESTIONS: '/ai/recipe-suggestions',
  AI_PARSE_RECIPE: '/ai/parse-recipe',

  // Temp recipe endpoints
  TEMP_RECIPE: (id) => `/temp-recipe/${id}`,
  STORE_TEMP_RECIPE: '/store-temp-recipe',

  // Utility endpoints
  MEASURING_UNITS: '/measuring-units',
  GENRES: '/genres',
  HEALTH: '/health',
  ISSUES: '/issues/',
  REPORT_ISSUE: '/issues/report',
  MY_REPORTS: '/issues/my-reports',
  ISSUE_STATS: '/issues/stats/summary',
};

// Helper function to build full URL
export const buildApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`;
};

// Axios instance configuration
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
//Test
// Connection test helper
export const testConnection = async () => {
  console.log('🔍 Testing backend connection...');
  console.log('API Base URL:', API_BASE_URL);

  try {
    const response = await axios.get(buildApiUrl(API_ENDPOINTS.HEALTH));
    console.log('✅ Backend connection successful:', response.data);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('❌ Backend connection failed:', error.message);
    return {
      success: false,
      error: error.message,
      suggestions: [
        'Make sure backend is running',
        'Check network connectivity',
        'Verify backend URL: ' + API_BASE_URL
      ]
    };
  }
};
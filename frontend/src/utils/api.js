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

  // Utility endpoints
  MEASURING_UNITS: '/measuring-units',
  GENRES: '/genres'
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

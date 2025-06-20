// frontend/src/context/AuthContext.jsx - Fixed version with correct import order
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS } from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Set up axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check if user is logged in on app start
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(buildApiUrl(API_ENDPOINTS.ME));
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = async (username, password) => {
    try {
      console.log('Attempting login to:', buildApiUrl(API_ENDPOINTS.LOGIN));
      const response = await axios.post(buildApiUrl(API_ENDPOINTS.LOGIN), {
        username,
        password,
      });

      const { access_token, user: userData } = response.data;

      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      console.log('Login successful:', userData);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || error.message || 'Network error - backend may not be running';
      return { success: false, error: message };
    }
  };

  const register = async (username, email, password) => {
    try {
      console.log('Attempting registration to:', buildApiUrl(API_ENDPOINTS.REGISTER));
      const response = await axios.post(buildApiUrl(API_ENDPOINTS.REGISTER), {
        username,
        email,
        password,
      });

      console.log('Registration successful, now logging in...');
      // Auto-login after successful registration
      const loginResult = await login(username, password);
      return loginResult;
    } catch (error) {
      console.error('Registration error:', error);
      const message = error.response?.data?.detail || error.message || 'Registration failed';
      return { success: false, error: message };
    }
  };

  const logout = () => {
    console.log('Logging out user');
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  const updateUser = (updatedUserData) => {
    setUser(prevUser => ({
      ...prevUser,
      ...updatedUserData
    }));
  };

  const value = {
    user,
    setUser: updateUser,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated,
    hasRole,
    apiBaseUrl: API_BASE_URL, // Use the centralized API_BASE_URL
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f0f8ff'
      }}>
        <div style={{
          padding: '2rem',
          backgroundColor: 'white',
          borderRadius: '15px',
          border: '2px solid #003366',
          textAlign: 'center'
        }}>
          <h2 style={{ color: '#003366' }}>Loading...</h2>
          <p>Checking authentication status</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
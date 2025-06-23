import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Navbar = () => {
  const { user, logout, isAuthenticated, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  // Helper function to get profile link text based on user role
  const getProfileLinkText = () => {
    if (hasRole(['admin', 'owner'])) {
      return '👥 Users';
    }
    return '👤 My Profile';
  };

  return (
    <nav style={{
      backgroundColor: '#003366',
      color: 'white',
      padding: '1rem 0',
      boxShadow: '0 2px 4px rgba(0, 51, 102, 0.3)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Link
          to="/"
          style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            textDecoration: 'none',
            color: 'white'
          }}
        >
          🍳 onDEK Recipe
        </Link>

        <ul style={{
          display: 'flex',
          listStyle: 'none',
          gap: '1.5rem', // Reduced gap from 2rem to 1.5rem
          alignItems: 'center',
          margin: 0,
          padding: 0
        }}>
          {isAuthenticated() ? (
            <>
              <li>
                <Link
                  to="/dashboard"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 0.75rem', // Reduced padding
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/dashboard') ? '#0066cc' : 'transparent',
                    fontSize: '0.9rem' // Slightly smaller font
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/dashboard')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/dashboard')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  🏠 Dashboard
                </Link>
              </li>

              <li>
                <Link
                  to="/recipes"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/recipes') ? '#0066cc' : 'transparent',
                    fontSize: '0.9rem'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/recipes')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/recipes')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  🔍 Recipes
                </Link>
              </li>

              <li>
                <Link
                  to="/add-recipe"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/add-recipe') ? '#0066cc' : 'transparent',
                    fontSize: '0.9rem'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/add-recipe')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/add-recipe')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  ➕ Add Recipe
                </Link>
              </li>

              {/* AI Chat Link */}
              <li>
                <Link
                  to="/ai-chat"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/ai-chat') ? '#0066cc' : 'transparent',
                    fontSize: '0.9rem'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/ai-chat')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/ai-chat')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  🤖 AI Rupert
                </Link>
              </li>

              {/* Profile Link - Now available for ALL authenticated users */}
              <li>
                <Link
                  to="/users"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/users') ? '#0066cc' : 'transparent',
                    fontSize: '0.9rem'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/users')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/users')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  {getProfileLinkText()}
                </Link>
              </li>

              <li>
                <button
                  onClick={handleLogout}
                  style={{
                    backgroundColor: '#f0f8ff',
                    color: '#003366',
                    border: '2px solid #f0f8ff',
                    borderRadius: '8px',
                    padding: '0.5rem 0.75rem',
                    cursor: 'pointer',
                    fontSize: '0.85rem', // Slightly smaller font
                    fontWeight: '500',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.color = 'white';
                    e.target.style.borderColor = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.color = '#003366';
                    e.target.style.borderColor = '#f0f8ff';
                  }}
                >
                  🚪 Logout
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link
                  to="/login"
                  style={{
                    color: 'white',
                    textDecoration: 'none',
                    padding: '0.5rem 1rem',
                    borderRadius: '8px',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: isActive('/login') ? '#0066cc' : 'transparent'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive('/login')) {
                      e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive('/login')) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  🔑 Login
                </Link>
              </li>
              <li>
                <Link
                  to="/register"
                  style={{
                    color: '#003366',
                    textDecoration: 'none',
                    padding: '0.5rem 1rem',
                    borderRadius: '8px',
                    backgroundColor: '#f0f8ff',
                    border: '2px solid #f0f8ff',
                    transition: 'all 0.3s ease',
                    fontWeight: '500'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'white';
                    e.target.style.borderColor = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.borderColor = '#f0f8ff';
                  }}
                >
                  👤 Register
                </Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Home = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div style={{
      padding: '2rem',
      backgroundColor: '#f0f8ff',
      minHeight: 'calc(100vh - 80px)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          background: 'white',
          border: '2px solid #003366',
          borderRadius: '15px',
          marginBottom: '3rem',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
        }}>
          <h1 style={{
            color: '#003366',
            fontSize: '3rem',
            marginBottom: '1rem'
          }}>
            Welcome to onDEK Recipe! 🍳
          </h1>

          {isAuthenticated() ? (
            <div>
              <p style={{
                fontSize: '1.3rem',
                color: '#666',
                marginBottom: '2rem'
              }}>
                Hello <strong style={{ color: '#003366' }}>{user?.username}</strong>!
                Ready to explore some delicious recipes?
              </p>

              <div style={{
                display: 'flex',
                gap: '1.5rem',
                justifyContent: 'center',
                flexWrap: 'wrap',
                marginTop: '2rem'
              }}>
                <Link
                  to="/dashboard"
                  style={{
                    display: 'inline-block',
                    padding: '12px 24px',
                    backgroundColor: '#003366',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '10px',
                    fontWeight: '500',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#0066cc';
                    e.target.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.transform = 'translateY(0)';
                  }}
                >
                  🏠 Go to Dashboard
                </Link>

                <button
                  onClick={() => alert('Recipe browsing coming soon! 🚧')}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#f0f8ff',
                    color: '#003366',
                    border: '2px solid #003366',
                    borderRadius: '10px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.color = '#003366';
                  }}
                >
                  🔍 Browse Recipes (Coming Soon)
                </button>
              </div>
            </div>
          ) : (
            <div>
              <p style={{
                fontSize: '1.3rem',
                color: '#666',
                marginBottom: '3rem'
              }}>
                Your comprehensive recipe management solution with AI assistance!
              </p>

              <div style={{
                display: 'flex',
                gap: '1.5rem',
                justifyContent: 'center',
                flexWrap: 'wrap',
                marginTop: '2rem'
              }}>
                <Link
                  to="/login"
                  style={{
                    display: 'inline-block',
                    padding: '12px 24px',
                    backgroundColor: '#003366',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '10px',
                    fontWeight: '500',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#0066cc';
                    e.target.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.transform = 'translateY(0)';
                  }}
                >
                  🔑 Login
                </Link>

                <Link
                  to="/register"
                  style={{
                    display: 'inline-block',
                    padding: '12px 24px',
                    backgroundColor: '#f0f8ff',
                    color: '#003366',
                    textDecoration: 'none',
                    border: '2px solid #003366',
                    borderRadius: '10px',
                    fontWeight: '500',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.color = '#003366';
                  }}
                >
                  👤 Create Account
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Features Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem',
          marginBottom: '3rem'
        }}>
          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>📝 Recipe Management</h3>
            <p>Store and organize all your favorite recipes with ingredients, instructions, and serving sizes.</p>
          </div>

          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>🔍 Smart Search</h3>
            <p>Find recipes quickly with real-time search and filtering by genre, ingredients, and more.</p>
          </div>

          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>🤖 AI Assistant</h3>
            <p>Get cooking help, recipe suggestions, and ingredient substitutions from RUPERT, our AI assistant.</p>
          </div>

          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>👥 User Roles</h3>
            <p>Secure access with different user levels - Owner, Admin, and User permissions.</p>
          </div>

          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>📱 Modern Design</h3>
            <p>Beautiful, responsive interface with a clean blue theme and intuitive navigation.</p>
          </div>

          <div className="card">
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>🍽️ Categories</h3>
            <p>Organize recipes by meal type: breakfast, lunch, dinner, snacks, desserts, and appetizers.</p>
          </div>
        </div>

        {/* App Status */}
        <div style={{
          background: 'white',
          border: '2px solid #003366',
          borderRadius: '15px',
          padding: '2rem',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
        }}>
          <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>
            🚀 Development Status
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
            textAlign: 'left',
            marginTop: '2rem'
          }}>
            <div style={{
              padding: '1rem',
              background: '#f0f8ff',
              borderRadius: '10px',
              border: '1px solid #003366'
            }}>
              <h4 style={{ color: '#28a745', marginBottom: '0.5rem' }}>
                ✅ Completed Features
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                <li>Backend API with authentication</li>
                <li>User registration and login</li>
                <li>Navigation and routing</li>
                <li>Role-based access control</li>
              </ul>
            </div>

            <div style={{
              padding: '1rem',
              background: '#f0f8ff',
              borderRadius: '10px',
              border: '1px solid #003366'
            }}>
              <h4 style={{ color: '#ffc107', marginBottom: '0.5rem' }}>
                🚧 Coming Next
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                <li>Recipe browsing and management</li>
                <li>Dynamic recipe creation forms</li>
                <li>Search and filtering</li>
                <li>AI assistant integration</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
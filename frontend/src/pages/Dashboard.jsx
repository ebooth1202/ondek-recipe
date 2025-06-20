import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const Dashboard = () => {
  const navigate = useNavigate(); // Initialize useNavigate
  const { user, hasRole } = useAuth();
  const [stats, setStats] = useState({
    totalRecipes: 0,
    favoriteRecipes: 0
  });
  const [loading, setLoading] = useState(true);

  // Fetch recipe stats when component mounts
  useEffect(() => {
    fetchRecipeStats();
  }, []);

  const fetchRecipeStats = async () => {
    try {
      // Get total recipes count
      const recipesResponse = await axios.get('http://127.0.0.1:8000/recipes');
      const totalRecipes = recipesResponse.data.length;

      // Get user's favorite recipes
      const favoritesResponse = await axios.get('http://127.0.0.1:8000/users/me/favorites');
      const favoriteRecipes = favoritesResponse.data.length;

      setStats({
        totalRecipes,
        favoriteRecipes
      });
    } catch (error) {
      console.error('Error fetching recipe stats:', error);
    } finally {
      setLoading(false);
    }
  };

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
        {/* Welcome Header */}
        <div style={{
          background: 'white',
          border: '2px solid #003366',
          borderRadius: '15px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
          textAlign: 'center'
        }}>
          <h1 style={{
            color: '#003366',
            fontSize: '2.5rem',
            marginBottom: '1rem'
          }}>
            🏠 Welcome to Your Dashboard
          </h1>
          <p style={{
            fontSize: '1.2rem',
            color: '#666',
            marginBottom: '1rem'
          }}>
            Hello <strong style={{ color: '#003366' }}>{user?.username}</strong>!
            You're logged in as <span style={{
              background: '#0066cc',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '0.9rem',
              textTransform: 'uppercase',
              fontWeight: 'bold'
            }}>{user?.role}</span>
          </p>
          <p style={{ color: '#666' }}>
            Email: {user?.email}
          </p>
        </div>

        {/* Quick Actions */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem',
          marginBottom: '2rem'
        }}>
          <div style={{
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            padding: '2rem',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'transform 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
          }}
          onClick={() => navigate('/recipes')}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
              🔍 Browse Recipes
            </h3>
            <p>Search and filter through your recipe collection</p>
            <div style={{
              background: '#f0f8ff',
              color: '#003366',
              padding: '8px 16px',
              borderRadius: '8px',
              display: 'inline-block',
              marginTop: '1rem',
              fontSize: '0.9rem'
            }}>
              Explore Now
            </div>
          </div>

          <div style={{
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            padding: '2rem',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'transform 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
          }}
          onClick={() => navigate('/add-recipe')}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
              ➕ Add Recipe
            </h3>
            <p>Create a new recipe with ingredients and instructions</p>
            <div style={{
              background: '#f0f8ff',
              color: '#003366',
              padding: '8px 16px',
              borderRadius: '8px',
              display: 'inline-block',
              marginTop: '1rem',
              fontSize: '0.9rem'
            }}>
              Create Now
            </div>
          </div>

          {/* Updated AI Assistant Card */}
          <div style={{
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            padding: '2rem',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'transform 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
          }}
          onClick={() => navigate('/ai-chat')}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
              🤖 AI Assistant
            </h3>
            <p>Get cooking help and recipe suggestions from your personal AI assistant</p>
            <div style={{
              background: '#f0f8ff',
              color: '#003366',
              padding: '8px 16px',
              borderRadius: '8px',
              display: 'inline-block',
              marginTop: '1rem',
              fontSize: '0.9rem'
            }}>
              Chat Now
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div style={{
          background: 'white',
          border: '2px solid #003366',
          borderRadius: '15px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
        }}>
          <h2 style={{
            color: '#003366',
            marginBottom: '1.5rem',
            textAlign: 'center'
          }}>
            📊 Your Recipe Stats
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1.5rem'
          }}>
            <div style={{
              background: '#f0f8ff',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #003366'
            }}>
              <h3 style={{ color: '#003366', fontSize: '2rem', margin: '0' }}>
                {loading ? '...' : stats.totalRecipes}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Total Recipes</p>
            </div>

            <div style={{
              background: '#f0f8ff',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #003366'
            }}>
              <h3 style={{ color: '#003366', fontSize: '2rem', margin: '0' }}>
                {loading ? '...' : stats.favoriteRecipes}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Favorite Recipes</p>
            </div>

            <div style={{
              background: '#f0f8ff',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #003366'
            }}>
              <h3 style={{ color: '#003366', fontSize: '2rem', margin: '0' }}>6</h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Recipe Categories</p>
            </div>

            <div style={{
              background: '#f0f8ff',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #003366'
            }}>
              <h3 style={{ color: '#003366', fontSize: '2rem', margin: '0' }}>🔥</h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Ready to Cook!</p>
            </div>
          </div>
        </div>

        {/* Admin Section */}
        {hasRole(['admin', 'owner']) && (
          <div style={{
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            padding: '2rem',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
          }}>
            <h2 style={{
              color: '#003366',
              marginBottom: '1.5rem',
              textAlign: 'center'
            }}>
              👑 Admin Features
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1.5rem'
            }}>
              <div style={{
                background: '#fff3cd',
                padding: '1.5rem',
                borderRadius: '10px',
                textAlign: 'center',
                border: '1px solid #856404',
                cursor: 'pointer'
              }}
              onClick={() => navigate('/user-management')}> {/* Update this line to navigate to user-management */}
                <h4 style={{ color: '#856404', marginBottom: '0.5rem' }}>
                  👥 Manage Users
                </h4>
                <p style={{ color: '#856404', fontSize: '0.9rem', margin: 0 }}>
                  Add, edit, or remove user accounts
                </p>
              </div>

              <div style={{
                background: '#d1ecf1',
                padding: '1.5rem',
                borderRadius: '10px',
                textAlign: 'center',
                border: '1px solid #0c5460',
                cursor: 'pointer'
              }}
              onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
                <h4 style={{ color: '#0c5460', marginBottom: '0.5rem' }}>
                  📖 API Documentation
                </h4>
                <p style={{ color: '#0c5460', fontSize: '0.9rem', margin: 0 }}>
                  View the FastAPI documentation
                </p>
              </div>

              {hasRole('owner') && (
                <div style={{
                  background: '#d4edda',
                  padding: '1.5rem',
                  borderRadius: '10px',
                  textAlign: 'center',
                  border: '1px solid #155724',
                  cursor: 'pointer'
                }}
                onClick={() => alert('System settings coming soon! ⚙️')}>
                  <h4 style={{ color: '#155724', marginBottom: '0.5rem' }}>
                    ⚙️ System Settings
                  </h4>
                  <p style={{ color: '#155724', fontSize: '0.9rem', margin: 0 }}>
                    Configure application settings
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
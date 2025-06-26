import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL, API_ENDPOINTS, apiClient } from '../utils/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const [stats, setStats] = useState({
    totalRecipes: 0,
    favoriteRecipes: 0
  });
  const [loading, setLoading] = useState(true);

  // Bug reporting state
  const [showBugReportModal, setShowBugReportModal] = useState(false);
  const [showFeatureRequestModal, setShowFeatureRequestModal] = useState(false);
  const [showImprovementModal, setShowImprovementModal] = useState(false);
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportMessage, setReportMessage] = useState('');
  const [reportError, setReportError] = useState('');

  // Fetch recipe stats when component mounts
  useEffect(() => {
    fetchRecipeStats();
  }, []);

  const fetchRecipeStats = async () => {
    try {
      // Get total recipes count
      const recipesResponse = await apiClient.get(API_ENDPOINTS.RECIPES);
      const totalRecipes = recipesResponse.data.length;

      // Get user's favorite recipes
      const favoritesResponse = await apiClient.get(API_ENDPOINTS.USER_FAVORITES);
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

  // Bug reporting functions
  const submitReport = async (type, title, description, severity = 'medium') => {
    setReportSubmitting(true);
    setReportError('');

    try {
      const reportData = {
        type,
        title,
        description,
        severity,
        context: {
          page: '/dashboard',
          actions: ['opened_dashboard', 'clicked_report_button']
        },
        tags: []
      };

      const response = await apiClient.post('/issues/report', reportData);

      setReportMessage('Thank you! Your report has been submitted successfully. We\'ll review it soon.');

      // Close all modals
      setShowBugReportModal(false);
      setShowFeatureRequestModal(false);
      setShowImprovementModal(false);

      // Clear message after 5 seconds
      setTimeout(() => setReportMessage(''), 5000);

    } catch (error) {
      console.error('Error submitting report:', error);
      setReportError(error.response?.data?.detail || 'Failed to submit report. Please try again.');
    } finally {
      setReportSubmitting(false);
    }
  };

  const handleBugReport = (formData) => {
    submitReport('bug_report', formData.title, formData.description, formData.severity);
  };

  const handleFeatureRequest = (formData) => {
    submitReport('feature_request', formData.title, formData.description, 'medium');
  };

  const handleImprovement = (formData) => {
    submitReport('improvement', formData.title, formData.description, 'low');
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
            Hello, <strong style={{ color: '#003366' }}>{user?.username}</strong>!
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
              🤖 Rupert
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

        {/* Help & Feedback Section */}
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
            💬 Help & Feedback
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem'
          }}>
            <div style={{
              background: '#f8d7da',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #dc3545',
              cursor: 'pointer',
              transition: 'transform 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            onClick={() => setShowBugReportModal(true)}>
              <h4 style={{ color: '#dc3545', marginBottom: '0.5rem' }}>
                🐛 Report a Bug
              </h4>
              <p style={{ color: '#dc3545', fontSize: '0.9rem', margin: 0 }}>
                Found something broken? Let us know!
              </p>
            </div>

            <div style={{
              background: '#d4edda',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #28a745',
              cursor: 'pointer',
              transition: 'transform 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            onClick={() => setShowFeatureRequestModal(true)}>
              <h4 style={{ color: '#28a745', marginBottom: '0.5rem' }}>
                💡 Request Feature
              </h4>
              <p style={{ color: '#28a745', fontSize: '0.9rem', margin: 0 }}>
                Have an idea? We'd love to hear it!
              </p>
            </div>

            <div style={{
              background: '#fff3cd',
              padding: '1.5rem',
              borderRadius: '10px',
              textAlign: 'center',
              border: '1px solid #ffc107',
              cursor: 'pointer',
              transition: 'transform 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            onClick={() => setShowImprovementModal(true)}>
              <h4 style={{ color: '#856404', marginBottom: '0.5rem' }}>
                ⚡ Suggest Improvement
              </h4>
              <p style={{ color: '#856404', fontSize: '0.9rem', margin: 0 }}>
                How can we make it better?
              </p>
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
              onClick={() => navigate('/user-management')}>
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
              onClick={() => window.open(`${API_BASE_URL.replace(':8000', ':8000/docs')}`, '_blank')}>
                <h4 style={{ color: '#0c5460', marginBottom: '0.5rem' }}>
                  📖 API Documentation
                </h4>
                <p style={{ color: '#0c5460', fontSize: '0.9rem', margin: 0 }}>
                  View the FastAPI documentation
                </p>
              </div>

              <div style={{
                background: '#f8d7da',
                padding: '1.5rem',
                borderRadius: '10px',
                textAlign: 'center',
                border: '1px solid #dc3545',
                cursor: 'pointer'
              }}
              onClick={() => navigate('/admin/issues')}>
                <h4 style={{ color: '#dc3545', marginBottom: '0.5rem' }}>
                  🎯 Issue Tracker
                </h4>
                <p style={{ color: '#dc3545', fontSize: '0.9rem', margin: 0 }}>
                  View and manage reported issues
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

      {/* Success/Error Messages */}
      {reportMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#d4edda',
          color: '#155724',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #c3e6cb',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1001,
          maxWidth: '400px'
        }}>
          <strong>Success!</strong> {reportMessage}
        </div>
      )}

      {reportError && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: '#f8d7da',
          color: '#721c24',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #f5c6cb',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1001,
          maxWidth: '400px'
        }}>
          <strong>Error:</strong> {reportError}
        </div>
      )}

      {/* Bug Report Modal */}
      {showBugReportModal && (
        <ReportModal
          type="bug_report"
          title="Report a Bug"
          description="Found something that's not working correctly? Help us fix it!"
          onSubmit={handleBugReport}
          onClose={() => setShowBugReportModal(false)}
          isSubmitting={reportSubmitting}
          showSeverity={true}
        />
      )}

      {/* Feature Request Modal */}
      {showFeatureRequestModal && (
        <ReportModal
          type="feature_request"
          title="Request a Feature"
          description="Have an idea for a new feature? We'd love to hear about it!"
          onSubmit={handleFeatureRequest}
          onClose={() => setShowFeatureRequestModal(false)}
          isSubmitting={reportSubmitting}
          showSeverity={false}
        />
      )}

      {/* Improvement Modal */}
      {showImprovementModal && (
        <ReportModal
          type="improvement"
          title="Suggest an Improvement"
          description="How can we make the existing features better?"
          onSubmit={handleImprovement}
          onClose={() => setShowImprovementModal(false)}
          isSubmitting={reportSubmitting}
          showSeverity={false}
        />
      )}
    </div>
  );
};

// Report Modal Component
const ReportModal = ({ type, title, description, onSubmit, onClose, isSubmitting, showSeverity }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'medium'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.title.trim() && formData.description.trim()) {
      onSubmit(formData);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const modalBackdropStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000
  };

  const modalContentStyle = {
    backgroundColor: 'white',
    borderRadius: '15px',
    padding: '2rem',
    width: '100%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
    position: 'relative'
  };

  const formGroupStyle = {
    marginBottom: '1.5rem'
  };

  const labelStyle = {
    display: 'block',
    color: '#003366',
    marginBottom: '0.5rem',
    fontWeight: '500'
  };

  const inputStyle = {
    width: '100%',
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid #ccc',
    fontSize: '1rem',
    boxSizing: 'border-box'
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '120px',
    resize: 'vertical'
  };

  const buttonStyle = {
    backgroundColor: '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '0.75rem 1.5rem',
    cursor: 'pointer',
    fontSize: '1rem',
    marginRight: '1rem'
  };

  const cancelButtonStyle = {
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '0.75rem 1.5rem',
    cursor: 'pointer',
    fontSize: '1rem'
  };

  return (
    <div style={modalBackdropStyle} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={modalContentStyle}>
        <h2 style={{ color: '#003366', marginBottom: '0.5rem' }}>{title}</h2>
        <p style={{ color: '#666', marginBottom: '2rem' }}>{description}</p>

        <form onSubmit={handleSubmit}>
          <div style={formGroupStyle}>
            <label style={labelStyle} htmlFor="title">
              Title <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <input
              id="title"
              name="title"
              type="text"
              style={inputStyle}
              value={formData.title}
              onChange={handleChange}
              placeholder="Brief description of the issue/request"
              required
              maxLength={200}
            />
          </div>

          <div style={formGroupStyle}>
            <label style={labelStyle} htmlFor="description">
              Description <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <textarea
              id="description"
              name="description"
              style={textareaStyle}
              value={formData.description}
              onChange={handleChange}
              placeholder={
                type === 'bug_report'
                  ? "Please describe what happened, what you expected to happen, and steps to reproduce the issue..."
                  : type === 'feature_request'
                  ? "Describe the feature you'd like to see, how it would work, and why it would be useful..."
                  : "Describe what could be improved and how you think it should work..."
              }
              required
              maxLength={2000}
            />
            <small style={{ color: '#666' }}>
              {formData.description.length}/2000 characters
            </small>
          </div>

          {showSeverity && (
            <div style={formGroupStyle}>
              <label style={labelStyle} htmlFor="severity">
                How severe is this issue?
              </label>
              <select
                id="severity"
                name="severity"
                style={inputStyle}
                value={formData.severity}
                onChange={handleChange}
              >
                <option value="low">Low - Minor inconvenience</option>
                <option value="medium">Medium - Affects normal use</option>
                <option value="high">High - Blocks important functionality</option>
                <option value="critical">Critical - App is unusable</option>
              </select>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem' }}>
            <button
              type="button"
              style={cancelButtonStyle}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                ...buttonStyle,
                opacity: isSubmitting ? 0.6 : 1,
                cursor: isSubmitting ? 'not-allowed' : 'pointer'
              }}
              disabled={isSubmitting || !formData.title.trim() || !formData.description.trim()}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Dashboard;
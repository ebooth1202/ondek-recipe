import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../utils/api';

const AdminTracker = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated } = useAuth();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [stats, setStats] = useState(null);

  // Filtering state
  const [filters, setFilters] = useState({
    activity_type: '',
    category: '',
    user_id: '',
    username: '',
    date_from: '',
    date_to: ''
  });

  // Modal state
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [showActivityModal, setShowActivityModal] = useState(false);

  // Check authentication and permissions
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    if (!hasRole(['admin', 'owner'])) {
      navigate('/dashboard');
      return;
    }

    fetchActivities();
    fetchStats();
  }, [isAuthenticated, hasRole, navigate]);

  // Fetch activities when filters change
  useEffect(() => {
    if (hasRole(['admin', 'owner'])) {
      fetchActivities();
    }
  }, [filters]);

  const fetchActivities = async () => {
    try {
      setLoading(true);

      // Build query parameters
      const params = new URLSearchParams();

      if (filters.activity_type) params.append('activity_type', filters.activity_type);
      if (filters.category) params.append('category', filters.category);
      if (filters.user_id) params.append('user_id', filters.user_id);
      if (filters.username) params.append('username', filters.username);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);

      // Default pagination
      params.append('limit', '100');

      console.log('Fetching activities with params:', params.toString());
      const response = await apiClient.get(`/activities/?${params.toString()}`);
      console.log('Activities response:', response.data);

      setActivities(response.data);

    } catch (error) {
      console.error('Error fetching activities:', error.response || error);
      setError(`Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/activities/stats/summary');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching activity stats:', error);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setFilters({
      ...filters,
      [filterName]: value
    });
  };

  const handleActivityClick = (activity) => {
    setSelectedActivity(activity);
    setShowActivityModal(true);
  };

  // Helper functions
  const getActivityIcon = (type) => {
    switch (type) {
      case 'login': return '🔑';
      case 'logout': return '👋';
      case 'create_recipe': return '➕';
      case 'update_recipe': return '✏️';
      case 'delete_recipe': return '🗑️';
      case 'view_recipe': return '👀';
      case 'favorite_recipe': return '❤️';
      case 'unfavorite_recipe': return '💔';
      case 'search_recipes': return '🔍';
      case 'upload_file': return '📤';
      case 'view_admin': return '👑';
      case 'api_access': return '🔌';
      default: return '📊';
    }
  };

  const getActivityLabel = (type) => {
    switch (type) {
      case 'login': return 'Login';
      case 'logout': return 'Logout';
      case 'create_recipe': return 'Created Recipe';
      case 'update_recipe': return 'Updated Recipe';
      case 'delete_recipe': return 'Deleted Recipe';
      case 'view_recipe': return 'Viewed Recipe';
      case 'favorite_recipe': return 'Favorited Recipe';
      case 'unfavorite_recipe': return 'Unfavorited Recipe';
      case 'search_recipes': return 'Searched Recipes';
      case 'upload_file': return 'Uploaded File';
      case 'view_admin': return 'Admin Access';
      case 'api_access': return 'API Access';
      default: return type.replace('_', ' ');
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'authentication': return '#007bff';
      case 'recipe_management': return '#28a745';
      case 'search_browse': return '#ffc107';
      case 'admin_action': return '#dc3545';
      case 'file_operation': return '#6f42c1';
      case 'user_management': return '#fd7e14';
      default: return '#6c757d';
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (milliseconds) => {
    if (!milliseconds) return 'N/A';
    if (milliseconds < 1000) return `${milliseconds}ms`;
    return `${(milliseconds / 1000).toFixed(1)}s`;
  };

  // Styles (same as AdminIssues)
  const containerStyle = {
    padding: '2rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)'
  };

  const headerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    marginBottom: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    textAlign: 'center'
  };

  const statsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem'
  };

  const statCardStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '10px',
    padding: '1.5rem',
    textAlign: 'center',
    boxShadow: '0 2px 8px rgba(0, 51, 102, 0.1)'
  };

  const filterContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.5rem',
    marginBottom: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
  };

  const activitiesContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
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
    width: '90%',
    maxWidth: '800px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
  };

  if (loading && activities.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '50vh'
          }}>
            <div style={{
              width: '50px',
              height: '50px',
              border: '4px solid #f0f8ff',
              borderTop: '4px solid #003366',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
          </div>
        </div>
        <style>
          {`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}
        </style>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={headerStyle}>
          <h1 style={{ color: '#003366', fontSize: '2.5rem', marginBottom: '1rem' }}>
            📊 Activity Tracker
          </h1>
          <p style={{ fontSize: '1.1rem', color: '#666' }}>
            Monitor user activities and system usage patterns
          </p>
        </div>

        {/* Messages */}
        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {successMessage && (
          <div style={{
            background: '#d4edda',
            color: '#155724',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            textAlign: 'center'
          }}>
            {successMessage}
          </div>
        )}

        {/* Statistics */}
        {stats && (
          <div style={statsContainerStyle}>
            <div style={statCardStyle}>
              <h3 style={{ color: '#003366', fontSize: '2rem', margin: '0' }}>
                {stats.total_activities}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Total Activities</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#007bff', fontSize: '2rem', margin: '0' }}>
                {stats.unique_users}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Unique Users</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#28a745', fontSize: '2rem', margin: '0' }}>
                {stats.activities_today}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Today</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#ffc107', fontSize: '2rem', margin: '0' }}>
                {stats.activities_this_week}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>This Week</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div style={filterContainerStyle}>
          <h3 style={{ color: '#003366', marginBottom: '1rem' }}>Filter Activities</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Activity Type
              </label>
              <select
                value={filters.activity_type}
                onChange={(e) => handleFilterChange('activity_type', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              >
                <option value="">All Types</option>
                <option value="login">Login</option>
                <option value="logout">Logout</option>
                <option value="create_recipe">Create Recipe</option>
                <option value="update_recipe">Update Recipe</option>
                <option value="delete_recipe">Delete Recipe</option>
                <option value="view_recipe">View Recipe</option>
                <option value="favorite_recipe">Favorite Recipe</option>
                <option value="search_recipes">Search Recipes</option>
                <option value="upload_file">Upload File</option>
                <option value="view_admin">Admin Access</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              >
                <option value="">All Categories</option>
                <option value="authentication">Authentication</option>
                <option value="recipe_management">Recipe Management</option>
                <option value="search_browse">Search & Browse</option>
                <option value="admin_action">Admin Action</option>
                <option value="file_operation">File Operation</option>
                <option value="user_management">User Management</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Username
              </label>
              <input
                type="text"
                value={filters.username}
                onChange={(e) => handleFilterChange('username', e.target.value)}
                placeholder="Search by username"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Date From
              </label>
              <input
                type="datetime-local"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Date To
              </label>
              <input
                type="datetime-local"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'end' }}>
              <button
                onClick={() => setFilters({
                  activity_type: '',
                  category: '',
                  user_id: '',
                  username: '',
                  date_from: '',
                  date_to: ''
                })}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  padding: '0.5rem 1rem',
                  cursor: 'pointer',
                  width: '100%'
                }}
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Activities List */}
        <div style={activitiesContainerStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ color: '#003366', margin: 0 }}>
              Activities ({activities.length})
            </h2>
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                backgroundColor: '#003366',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '0.75rem 1.5rem',
                cursor: 'pointer'
              }}
            >
              🏠 Back to Dashboard
            </button>
          </div>

          {activities.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              <h3>No activities found</h3>
              <p>No activities match your current filters.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Activity
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      User
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Category
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Resource
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Time
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Duration
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {activities.map((activity) => (
                    <tr key={activity.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontSize: '1.2rem', marginRight: '0.5rem' }}>
                          {getActivityIcon(activity.activity_type)}
                        </span>
                        {getActivityLabel(activity.activity_type)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div>
                          <strong>{activity.user_info.username}</strong>
                          <br />
                          <small style={{ color: '#666' }}>({activity.user_info.role})</small>
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {activity.category ? (
                          <span
                            style={{
                              backgroundColor: getCategoryColor(activity.category),
                              color: 'white',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '0.8rem',
                              textTransform: 'uppercase'
                            }}
                          >
                            {activity.category.replace('_', ' ')}
                          </span>
                        ) : (
                          <span style={{ color: '#999', fontStyle: 'italic' }}>No Category</span>
                        )}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {activity.details?.resource_id ? (
                          <div>
                            <strong>{activity.details.resource_type || 'Unknown'}</strong>
                            <br />
                            <small style={{ color: '#666' }}>{activity.details.resource_id}</small>
                          </div>
                        ) : (
                          <span style={{ color: '#666' }}>-</span>
                        )}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {formatDateTime(activity.created_at)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {formatDuration(activity.details?.response_time_ms)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <button
                          onClick={() => handleActivityClick(activity)}
                          style={{
                            backgroundColor: '#003366',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '0.5rem 1rem',
                            cursor: 'pointer',
                            fontSize: '0.8rem'
                          }}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Activity Detail Modal */}
      {showActivityModal && selectedActivity && (
        <div style={modalBackdropStyle} onClick={(e) => e.target === e.currentTarget && setShowActivityModal(false)}>
          <div style={modalContentStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#003366', margin: 0 }}>
                {getActivityIcon(selectedActivity.activity_type)} Activity Details
              </h2>
              <button
                onClick={() => setShowActivityModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ color: '#003366' }}>{getActivityLabel(selectedActivity.activity_type)}</h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <strong>User:</strong> {selectedActivity.user_info.username} ({selectedActivity.user_info.role})
                </div>
                <div>
                  <strong>Category:</strong>
                  {selectedActivity.category ? (
                    <span
                      style={{
                        backgroundColor: getCategoryColor(selectedActivity.category),
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        marginLeft: '0.5rem'
                      }}
                    >
                      {selectedActivity.category.replace('_', ' ')}
                    </span>
                  ) : (
                    <span style={{ color: '#999', marginLeft: '0.5rem' }}>No Category</span>
                  )}
                </div>
                <div>
                  <strong>Time:</strong> {formatDateTime(selectedActivity.created_at)}
                </div>
                <div>
                  <strong>Duration:</strong> {formatDuration(selectedActivity.details?.response_time_ms)}
                </div>
                <div>
                  <strong>Method:</strong> {selectedActivity.details?.method || 'N/A'}
                </div>
                <div>
                  <strong>Endpoint:</strong> {selectedActivity.details?.endpoint || 'N/A'}
                </div>
              </div>

              {selectedActivity.description && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Description:</strong>
                  <div style={{
                    backgroundColor: '#f8f9fa',
                    padding: '1rem',
                    borderRadius: '8px',
                    marginTop: '0.5rem',
                    border: '1px solid #dee2e6'
                  }}>
                    {selectedActivity.description}
                  </div>
                </div>
              )}

              {selectedActivity.context && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Context:</strong>
                  <ul>
                    {selectedActivity.context.ip_address && <li>IP: {selectedActivity.context.ip_address}</li>}
                    {selectedActivity.context.browser && <li>Browser: {selectedActivity.context.browser}</li>}
                    {selectedActivity.context.page && <li>Page: {selectedActivity.context.page}</li>}
                  </ul>
                </div>
              )}

              {selectedActivity.details?.resource_id && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Resource:</strong>
                  <div style={{
                    backgroundColor: '#e3f2fd',
                    padding: '1rem',
                    borderRadius: '8px',
                    marginTop: '0.5rem',
                    border: '1px solid #bbdefb'
                  }}>
                    Type: {selectedActivity.details.resource_type || 'Unknown'}<br />
                    ID: {selectedActivity.details.resource_id}
                  </div>
                </div>
              )}

              {selectedActivity.tags && selectedActivity.tags.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Tags:</strong>
                  <div style={{ marginTop: '0.5rem' }}>
                    {selectedActivity.tags.map((tag, index) => (
                      <span
                        key={index}
                        style={{
                          backgroundColor: '#e9ecef',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '0.8rem',
                          marginRight: '0.5rem'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowActivityModal(false)}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminTracker;
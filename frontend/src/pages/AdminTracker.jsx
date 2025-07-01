import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../utils/api';

const AdminTracker = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState([]);
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
  const [selectedSession, setSelectedSession] = useState(null);
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

      // Group activities into sessions
      const groupedSessions = groupActivitiesIntoSessions(response.data);
      setSessions(groupedSessions);

    } catch (error) {
      console.error('Error fetching activities:', error.response || error);
      setError(`Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const groupActivitiesIntoSessions = (activities) => {
    // Group activities by user first
    const userGroups = {};

    activities.forEach(activity => {
      const username = activity.user_info.username;
      if (!userGroups[username]) {
        userGroups[username] = [];
      }
      userGroups[username].push(activity);
    });

    // For each user, group activities into sessions
    const sessions = [];

    Object.entries(userGroups).forEach(([username, userActivities]) => {
      // Sort activities by time
      const sortedActivities = userActivities.sort((a, b) =>
        new Date(a.created_at) - new Date(b.created_at)
      );

      // Group into sessions (activities within 2 hours of each other are same session)
      let currentSession = null;
      const SESSION_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours in milliseconds

      sortedActivities.forEach(activity => {
        const activityTime = new Date(activity.created_at);

        if (!currentSession ||
            (activityTime - new Date(currentSession.lastActivity)) > SESSION_TIMEOUT) {

          // Start new session
          if (currentSession) {
            sessions.push(currentSession);
          }

          currentSession = {
            id: `${username}-${activityTime.getTime()}`,
            username: username,
            user_info: activity.user_info,
            startTime: activityTime,
            lastActivity: activityTime,
            activities: [activity],
            status: 'active'
          };
        } else {
          // Add to current session
          currentSession.activities.push(activity);
          currentSession.lastActivity = activityTime;
        }
      });

      // Don't forget the last session
      if (currentSession) {
        sessions.push(currentSession);
      }
    });

    // Determine session status and calculate metrics
    sessions.forEach(session => {
      const hasLogout = session.activities.some(a => a.activity_type === 'logout');
      const lastActivityAge = Date.now() - new Date(session.lastActivity);
      const ACTIVE_THRESHOLD = 30 * 60 * 1000; // 30 minutes

      if (hasLogout) {
        session.status = 'completed';
        session.endTime = session.lastActivity;
      } else if (lastActivityAge > ACTIVE_THRESHOLD) {
        session.status = 'expired';
        session.endTime = session.lastActivity;
      } else {
        session.status = 'active';
      }

      // Calculate duration
      const start = new Date(session.startTime);
      const end = session.endTime ? new Date(session.endTime) : new Date();
      session.duration = end - start;

      // Count page visits
      session.pageVisits = session.activities.filter(a => a.activity_type === 'page_navigation').length;

      // Get unique pages visited
      session.pagesVisited = [...new Set(
        session.activities
          .filter(a => a.activity_type === 'page_navigation')
          .map(a => getPageName(a.details?.endpoint))
      )];
    });

    // Sort sessions by start time (newest first)
    return sessions.sort((a, b) => new Date(b.startTime) - new Date(a.startTime));
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

  const handleActivityClick = (session) => {
    setSelectedSession(session);
    setShowActivityModal(true);
  };

  // Helper functions
  const getActivityIcon = (type) => {
    switch (type) {
      case 'login': return '🔑';
      case 'logout': return '👋';
      case 'page_navigation': return '🧭';
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
      case 'login': return 'Logged In';
      case 'logout': return 'Logged Out';
      case 'page_navigation': return 'Visited Page';
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
      case 'navigation': return '#17a2b8';
      case 'recipe_management': return '#28a745';
      case 'search_browse': return '#ffc107';
      case 'admin_action': return '#dc3545';
      case 'file_operation': return '#6f42c1';
      case 'user_management': return '#fd7e14';
      default: return '#6c757d';
    }
  };

  const getPageName = (path) => {
  const pageNames = {
    '/': 'Dashboard',
    '/recipes': 'Recipes',
    '/favorites': 'Favorites',
    '/admin': 'Admin Dashboard',
    '/admin/activities': 'Activity Tracker',
    '/admin/issues': 'Issue Tracker',
    '/ai-chat': 'AI Chat',          // ADD THIS
    '/add-recipe': 'Add Recipe'     // ADD THIS
  };
  return pageNames[path] || path;
};

  const getStatusColor = (status) => {
    const colors = {
      'active': '#28a745',
      'completed': '#007bff',
      'expired': '#6c757d'
    };
    return colors[status] || '#6c757d';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'active': '🟢',
      'completed': '✅',
      'expired': '⚪'
    };
    return icons[status] || '❓';
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      timeZone: 'America/New_York',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      timeZone: 'America/New_York',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (milliseconds) => {
    if (!milliseconds || milliseconds < 1000) return '< 1 min';
    const minutes = Math.floor(milliseconds / (1000 * 60));
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  // Styles (same as original)
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

  const sessionCardStyle = {
    background: 'white',
    border: '2px solid #dee2e6',
    borderRadius: '12px',
    padding: '1.5rem',
    marginBottom: '1rem',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s'
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

  if (loading && sessions.length === 0) {
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
            Monitor user sessions and navigation patterns
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
                {sessions.length}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>User Sessions</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#007bff', fontSize: '2rem', margin: '0' }}>
                {stats.unique_users}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Unique Users</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#28a745', fontSize: '2rem', margin: '0' }}>
                {sessions.filter(s => s.status === 'active').length}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Currently Active</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#ffc107', fontSize: '2rem', margin: '0' }}>
                {sessions.filter(s => s.status === 'completed').length}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Completed Sessions</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div style={filterContainerStyle}>
          <h3 style={{ color: '#003366', marginBottom: '1rem' }}>Filter Sessions</h3>
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
                <option value="page_navigation">Page Visit</option>
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
                <option value="navigation">Navigation</option>
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

        {/* Sessions List */}
        <div style={activitiesContainerStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ color: '#003366', margin: 0 }}>
              User Sessions ({sessions.length})
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

          {sessions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              <h3>No sessions found</h3>
              <p>No user sessions match your current filters.</p>
            </div>
          ) : (
            <div>
              {sessions.map((session) => (
                <div
                  key={session.id}
                  style={sessionCardStyle}
                  onClick={() => handleActivityClick(session)}
                  onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                    e.target.style.borderColor = '#003366';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                    e.target.style.borderColor = '#dee2e6';
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ fontSize: '1.5rem' }}>🔑</span>
                      <div>
                        <h3 style={{ margin: 0, color: '#003366' }}>
                          {session.username}
                        </h3>
                        <p style={{ margin: 0, color: '#666', fontSize: '0.9rem' }}>
                          {session.user_info.role} • Started {formatDateTime(session.startTime)}
                        </p>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>{getStatusIcon(session.status)}</span>
                      <span style={{
                        color: getStatusColor(session.status),
                        fontWeight: 'bold',
                        textTransform: 'capitalize'
                      }}>
                        {session.status}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    <div>
                      <strong>Duration:</strong>
                      <div>{formatDuration(session.duration)}</div>
                    </div>
                    <div>
                      <strong>Pages Visited:</strong>
                      <div>{session.pageVisits} visits</div>
                    </div>
                    <div>
                      <strong>Activities:</strong>
                      <div>{session.activities.length} total</div>
                    </div>
                    <div>
                      <strong>Pages:</strong>
                      <div style={{ fontSize: '0.9rem', color: '#666' }}>
                        {session.pagesVisited.slice(0, 2).join(', ')}
                        {session.pagesVisited.length > 2 && ` +${session.pagesVisited.length - 2} more`}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Activity Detail Modal */}
      {showActivityModal && selectedSession && (
        <div style={modalBackdropStyle} onClick={(e) => e.target === e.currentTarget && setShowActivityModal(false)}>
          <div style={modalContentStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#003366', margin: 0 }}>
                {getActivityIcon('login')} Session Details - {selectedSession.username}
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

            <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <strong>User:</strong> {selectedSession.username} ({selectedSession.user_info.role})
                </div>
                <div>
                  <strong>Status:</strong>
                  <span style={{
                    color: getStatusColor(selectedSession.status),
                    marginLeft: '0.5rem',
                    textTransform: 'capitalize'
                  }}>
                    {getStatusIcon(selectedSession.status)} {selectedSession.status}
                  </span>
                </div>
                <div>
                  <strong>Started:</strong> {formatDateTime(selectedSession.startTime)}
                </div>
                <div>
                  <strong>Duration:</strong> {formatDuration(selectedSession.duration)}
                </div>
                <div>
                  <strong>Activities:</strong> {selectedSession.activities.length}
                </div>
                <div>
                  <strong>Pages Visited:</strong> {selectedSession.pageVisits}
                </div>
              </div>

              {selectedSession.endTime && (
                <div>
                  <strong>Ended:</strong> {formatDateTime(selectedSession.endTime)}
                </div>
              )}
            </div>

            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>Session Timeline</h3>

            <div style={{ marginBottom: '1.5rem' }}>
              {selectedSession.activities.map((activity, index) => (
                <div key={index} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '0.75rem',
                  borderLeft: '3px solid #007bff',
                  marginLeft: '1rem',
                  marginBottom: '0.5rem',
                  backgroundColor: index % 2 === 0 ? '#f8f9fa' : 'white',
                  borderRadius: '4px'
                }}>
                  <span style={{ fontSize: '1.2rem' }}>
                    {getActivityIcon(activity.activity_type)}
                  </span>
                  <div style={{ flex: 1 }}>
                    <strong>{formatTime(activity.created_at)}</strong>
                    <span style={{ marginLeft: '1rem' }}>
                      {getActivityLabel(activity.activity_type)}
                      {activity.activity_type === 'page_navigation' && activity.details?.endpoint &&
                        ` - ${getPageName(activity.details.endpoint)}`
                      }
                    </span>
                  </div>
                  {activity.details?.response_time_ms && (
                    <span style={{ fontSize: '0.8rem', color: '#666' }}>
                      {activity.details.response_time_ms}ms
                    </span>
                  )}
                </div>
              ))}
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
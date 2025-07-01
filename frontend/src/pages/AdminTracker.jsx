import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../utils/api';

const AdminTracker = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated } = useAuth();
  const [allSessions, setAllSessions] = useState([]); // NEW: Store all sessions for stats
  const [sessions, setSessions] = useState([]); // Filtered sessions for display
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [stats, setStats] = useState(null);

  // Filtering state
  const [filters, setFilters] = useState({
    status: 'active', // NEW: Default to showing only active sessions
    username: '',
    date_from: '',
    date_to: ''
  });

  // Modal state
  const [selectedSession, setSelectedSession] = useState(null);
  const [showActivityModal, setShowActivityModal] = useState(false);

  // Delete confirmation state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [activityToDelete, setActivityToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Session deletion state
  const [showSessionDeleteConfirm, setShowSessionDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [deletingSession, setDeletingSession] = useState(false);
  const [deletionProgress, setDeletionProgress] = useState({ current: 0, total: 0 });

  // Manual completion state
  const [manuallyCompletedSessions, setManuallyCompletedSessions] = useState(new Set());

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

      // Build query parameters (removed activity_type and category)
      const params = new URLSearchParams();

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

      // Store all sessions for stats calculation
      setAllSessions(groupedSessions);

      // Filter sessions by status for display
      const filteredSessions = groupedSessions.filter(session => {
        if (filters.status && filters.status !== '') {
          if (filters.status === 'completed') {
            // Show both completed and expired sessions when "Completed" is selected
            return session.status === 'completed' || session.status === 'expired';
          } else {
            return session.status === filters.status;
          }
        }
        return true;
      });

      setSessions(filteredSessions);

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
      const ACTIVE_THRESHOLD = 10 * 60 * 1000; // 10 minutes (CHANGED FROM 30)

      // Check if manually completed
      if (manuallyCompletedSessions.has(session.id)) {
        session.status = 'completed';
        session.endTime = session.lastActivity;
      } else if (hasLogout) {
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

  // NEW DELETE FUNCTIONS
  const handleDeleteClick = (activity, event) => {
    event.stopPropagation(); // Prevent triggering the session click
    setActivityToDelete(activity);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!activityToDelete || !hasRole(['owner'])) {
      setError('Only owners can delete activities');
      return;
    }

    setDeleting(true);
    try {
      await apiClient.delete(`/activities/${activityToDelete.id}`);
      setSuccessMessage('Activity deleted successfully');
      setShowDeleteConfirm(false);
      setActivityToDelete(null);
      setShowActivityModal(false);

      // Refresh the activities list
      await fetchActivities();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Error deleting activity:', error);
      setError(error.response?.data?.detail || 'Failed to delete activity');
      setTimeout(() => setError(''), 5000);
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setActivityToDelete(null);
  };

  // NEW MANUAL COMPLETION FUNCTION
  const markSessionAsCompleted = (sessionId) => {
    setManuallyCompletedSessions(prev => new Set([...prev, sessionId]));
    setSuccessMessage('Session marked as completed');
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  // NEW SESSION DELETION FUNCTIONS
  const handleSessionDeleteClick = (session, event) => {
    event.stopPropagation();
    setSessionToDelete(session);
    setShowSessionDeleteConfirm(true);
  };

  const confirmSessionDelete = async () => {
    if (!sessionToDelete || !hasRole(['owner'])) {
      setError('Only owners can delete sessions');
      return;
    }

    setDeletingSession(true);
    setDeletionProgress({ current: 0, total: sessionToDelete.activities.length });

    let deletedCount = 0;
    let failedCount = 0;
    const failedActivities = [];

    try {
      // Delete each activity in the session
      for (let i = 0; i < sessionToDelete.activities.length; i++) {
        const activity = sessionToDelete.activities[i];
        setDeletionProgress({ current: i + 1, total: sessionToDelete.activities.length });

        try {
          await apiClient.delete(`/activities/${activity.id}`);
          deletedCount++;
        } catch (error) {
          console.error(`Failed to delete activity ${activity.id}:`, error);
          failedCount++;
          failedActivities.push(activity);
        }
      }

      // Show results
      if (failedCount === 0) {
        setSuccessMessage(`Session deleted successfully! Removed ${deletedCount} activities.`);
      } else {
        setSuccessMessage(`Session partially deleted: ${deletedCount} deleted, ${failedCount} failed.`);
        if (failedCount > 0) {
          console.warn('Failed to delete activities:', failedActivities);
        }
      }

      // Close modals and refresh
      setShowSessionDeleteConfirm(false);
      setSessionToDelete(null);
      setShowActivityModal(false);

      // Refresh the activities list
      await fetchActivities();

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);

    } catch (error) {
      console.error('Error during session deletion:', error);
      setError('Failed to delete session. Please try again.');
      setTimeout(() => setError(''), 5000);
    } finally {
      setDeletingSession(false);
      setDeletionProgress({ current: 0, total: 0 });
    }
  };

  const cancelSessionDelete = () => {
    setShowSessionDeleteConfirm(false);
    setSessionToDelete(null);
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

  if (loading && allSessions.length === 0) {
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
                {allSessions.length}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Total Sessions</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#007bff', fontSize: '2rem', margin: '0' }}>
                {stats.unique_users}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Unique Users</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#28a745', fontSize: '2rem', margin: '0' }}>
                {allSessions.filter(s => s.status === 'active').length}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Currently Active</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#ffc107', fontSize: '2rem', margin: '0' }}>
                {allSessions.filter(s => s.status === 'completed' || s.status === 'expired').length}
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
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
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
                  status: 'active', // Reset to active (default view)
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {/* Delete Session Button - Only show for owners */}
                {hasRole(['owner']) && (
                  <button
                    onClick={(e) => handleSessionDeleteClick(selectedSession, e)}
                    style={{
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '0.5rem 1rem',
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                    title="Delete entire session"
                  >
                    🗑️ Delete Session
                  </button>
                )}
                {/* Mark as Completed Button - Only show for non-completed sessions and for owners/admins */}
                {selectedSession.status !== 'completed' && hasRole(['admin', 'owner']) && (
                  <button
                    onClick={() => markSessionAsCompleted(selectedSession.id)}
                    style={{
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '0.5rem 1rem',
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                    title="Mark this session as completed"
                  >
                    ✅ Mark Completed
                  </button>
                )}
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
                  {/* DELETE BUTTON - Only show for owners */}
                  {hasRole(['owner']) && (
                    <button
                      onClick={(e) => handleDeleteClick(activity, e)}
                      style={{
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '0.25rem 0.5rem',
                        cursor: 'pointer',
                        fontSize: '0.8rem'
                      }}
                      title="Delete this activity"
                    >
                      🗑️
                    </button>
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

      {/* DELETE CONFIRMATION MODAL */}
      {showDeleteConfirm && (
        <div style={modalBackdropStyle}>
          <div style={{
            ...modalContentStyle,
            maxWidth: '400px',
            textAlign: 'center'
          }}>
            <h3 style={{ color: '#dc3545', marginBottom: '1rem' }}>
              🗑️ Confirm Delete
            </h3>
            <p style={{ marginBottom: '1.5rem' }}>
              Are you sure you want to delete this activity?
            </p>
            <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem' }}>
              <strong>Activity:</strong> {activityToDelete && getActivityLabel(activityToDelete.activity_type)}
              <br />
              <strong>Time:</strong> {activityToDelete && formatDateTime(activityToDelete.created_at)}
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button
                onClick={cancelDelete}
                disabled={deleting}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                style={{
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1
                }}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SESSION DELETE CONFIRMATION MODAL */}
      {showSessionDeleteConfirm && (
        <div style={modalBackdropStyle}>
          <div style={{
            ...modalContentStyle,
            maxWidth: '500px',
            textAlign: 'center'
          }}>
            <h3 style={{ color: '#dc3545', marginBottom: '1rem' }}>
              🗑️ Delete Entire Session
            </h3>
            <p style={{ marginBottom: '1.5rem' }}>
              Are you sure you want to delete this entire session?
            </p>
            {sessionToDelete && (
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem', textAlign: 'left' }}>
                <strong>Session Details:</strong>
                <br />• User: {sessionToDelete.username}
                <br />• Duration: {formatDuration(sessionToDelete.duration)}
                <br />• Activities: {sessionToDelete.activities.length} total
                <br />• Started: {formatDateTime(sessionToDelete.startTime)}
                <br />
                <br />
                <span style={{ color: '#dc3545', fontWeight: 'bold' }}>
                  This will permanently delete all {sessionToDelete.activities.length} activities in this session.
                </span>
              </div>
            )}

            {/* Progress indicator during deletion */}
            {deletingSession && (
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ color: '#007bff', marginBottom: '0.5rem' }}>
                  Deleting activities... {deletionProgress.current} of {deletionProgress.total}
                </div>
                <div style={{
                  width: '100%',
                  height: '8px',
                  backgroundColor: '#e9ecef',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(deletionProgress.current / deletionProgress.total) * 100}%`,
                    height: '100%',
                    backgroundColor: '#007bff',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button
                onClick={cancelSessionDelete}
                disabled={deletingSession}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: deletingSession ? 'not-allowed' : 'pointer',
                  opacity: deletingSession ? 0.6 : 1
                }}
              >
                Cancel
              </button>
              <button
                onClick={confirmSessionDelete}
                disabled={deletingSession}
                style={{
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: deletingSession ? 'not-allowed' : 'pointer',
                  opacity: deletingSession ? 0.6 : 1
                }}
              >
                {deletingSession ? 'Deleting...' : `Delete Session (${sessionToDelete?.activities.length || 0} activities)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminTracker;
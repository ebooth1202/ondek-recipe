import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
// import { apiClient } from '../utils/api';
import { apiClient, API_ENDPOINTS } from '../utils/api';

const AdminIssues = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated } = useAuth();
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [stats, setStats] = useState(null);

  // Filtering state
  const [filters, setFilters] = useState({
    type: '',
    severity: '',
    status: '',
    priority: ''
  });

  // Modal state
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [showIssueModal, setShowIssueModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateData, setUpdateData] = useState({
    status: '',
    priority: '',
    resolution_notes: ''
  });

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

    fetchIssues();
    fetchStats();
  }, [isAuthenticated, hasRole, navigate]);

  // Fetch issues when filters change
  useEffect(() => {
    if (hasRole(['admin', 'owner'])) {
      fetchIssues();
    }
  }, [filters]);



  const fetchIssues = async () => {
  try {
    setLoading(true);

    // Keep the working API call exactly as it was
    console.log('Fetching all issues...');
    const response = await apiClient.get(API_ENDPOINTS.ISSUES);
    console.log('Issues response:', response.data);

    // Now filter the results CLIENT-SIDE instead of server-side
    let filteredIssues = response.data;

    // Apply filters if they exist
    if (filters.type) {
      filteredIssues = filteredIssues.filter(issue => issue.type === filters.type);
    }

    if (filters.severity) {
      filteredIssues = filteredIssues.filter(issue => issue.severity === filters.severity);
    }

    if (filters.status) {
      filteredIssues = filteredIssues.filter(issue => issue.status === filters.status);
    }

    if (filters.priority) {
      filteredIssues = filteredIssues.filter(issue => issue.priority === filters.priority);
    }

    // Hide resolved/closed by default (unless specifically filtered)
    if (!filters.status) {
      filteredIssues = filteredIssues.filter(issue =>
        issue.status !== 'resolved' && issue.status !== 'closed'
      );
    }

    setIssues(filteredIssues);

  } catch (error) {
    console.error('Error fetching issues:', error.response || error);
    setError(`Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`);
  } finally {
    setLoading(false);
  }
};

  const fetchStats = async () => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.ISSUE_STATS);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setFilters({
      ...filters,
      [filterName]: value
    });
  };

  const handleIssueClick = (issue) => {
    setSelectedIssue(issue);
    setShowIssueModal(true);
  };

  const handleUpdateIssue = (issue) => {
    setSelectedIssue(issue);
    setUpdateData({
      status: issue.status,
      priority: issue.priority,
      resolution_notes: issue.resolution_notes || ''
    });
    setShowUpdateModal(true);
  };

  const submitUpdate = async () => {
    if (!selectedIssue) return;

    try {
      const response = await apiClient.put(`/issues/${selectedIssue.id}`, updateData);

      // Update the issue in the list
      setIssues(issues.map(issue =>
        issue.id === selectedIssue.id ? response.data : issue
      ));

      setSuccessMessage('Issue updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);

      setShowUpdateModal(false);
      setSelectedIssue(null);
      fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Error updating issue:', error);
      setError(error.response?.data?.detail || 'Failed to update issue');
      setTimeout(() => setError(''), 5000);
    }
  };

  // Helper functions
  const getTypeIcon = (type) => {
    switch (type) {
      case 'bug_report': return '🐛';
      case 'feature_request': return '💡';
      case 'improvement': return '⚡';
      case 'auto_error': return '🚨';
      case 'performance': return '⏱️';
      default: return '📝';
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'bug_report': return 'Bug Report';
      case 'feature_request': return 'Feature Request';
      case 'improvement': return 'Improvement';
      case 'auto_error': return 'Auto Error';
      case 'performance': return 'Performance';
      default: return type;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return '#dc3545';
      case 'in_progress': return '#ffc107';
      case 'resolved': return '#28a745';
      case 'closed': return '#6c757d';
      default: return '#6c757d';
    }
  };

  // Styles
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

  const issuesContainerStyle = {
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

  if (loading && issues.length === 0) {
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
            🎯 Issue Tracker
          </h1>
          <p style={{ fontSize: '1.1rem', color: '#666' }}>
            Monitor and manage user reports, bugs, and system issues
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
                {stats.total_issues}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Total Issues</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#dc3545', fontSize: '2rem', margin: '0' }}>
                {stats.open_critical}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Critical Open</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#fd7e14', fontSize: '2rem', margin: '0' }}>
                {stats.open_high}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>High Priority</p>
            </div>
            <div style={statCardStyle}>
              <h3 style={{ color: '#28a745', fontSize: '2rem', margin: '0' }}>
                {stats.by_status?.resolved || 0}
              </h3>
              <p style={{ color: '#666', margin: '0.5rem 0 0 0' }}>Resolved</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div style={filterContainerStyle}>
          <h3 style={{ color: '#003366', marginBottom: '1rem' }}>Filter Issues</h3>
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
                <option value="">Active Issues</option>
                <option value="open">Open Only</option>
                <option value="in_progress">In Progress Only</option>
                <option value="resolved">Resolved Only</option>
                <option value="closed">Closed Only</option>
                <option value="all">All Issues</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Severity
              </label>
              <select
                value={filters.severity}
                onChange={(e) => handleFilterChange('severity', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              >
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Priority
              </label>
              <select
                value={filters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #ccc'
                }}
              >
                <option value="">All Priorities</option>
                <option value="urgent">Urgent</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Issues List */}
        <div style={issuesContainerStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ color: '#003366', margin: 0 }}>
              Issues ({issues.length})
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

          {issues.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              <h3>No issues found</h3>
              <p>No issues match your current filters.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Type
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Title
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Severity
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Status
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Reporter
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Created
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', color: '#003366', borderBottom: '2px solid #dee2e6' }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {issues.map((issue) => (
                    <tr key={issue.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontSize: '1.2rem', marginRight: '0.5rem' }}>
                          {getTypeIcon(issue.type)}
                        </span>
                        {getTypeLabel(issue.type)}
                      </td>
                      <td style={{ padding: '1rem', maxWidth: '300px' }}>
                        <div
                          style={{
                            cursor: 'pointer',
                            color: '#003366',
                            textDecoration: 'underline'
                          }}
                          onClick={() => handleIssueClick(issue)}
                        >
                          {issue.title}
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span
                          style={{
                            backgroundColor: getSeverityColor(issue.severity),
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '0.8rem',
                            textTransform: 'uppercase'
                          }}
                        >
                          {issue.severity}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span
                          style={{
                            backgroundColor: getStatusColor(issue.status),
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '0.8rem',
                            textTransform: 'uppercase'
                          }}
                        >
                          {issue.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {issue.user_info.username}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {new Date(issue.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <button
                          onClick={() => handleUpdateIssue(issue)}
                          style={{
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            padding: '0.5rem 1rem',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            marginRight: '0.5rem'
                          }}
                        >
                          Update
                        </button>
                        <button
                          onClick={() => handleIssueClick(issue)}
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
                          View
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

      {/* Issue Detail Modal */}
      {showIssueModal && selectedIssue && (
        <div style={modalBackdropStyle} onClick={(e) => e.target === e.currentTarget && setShowIssueModal(false)}>
          <div style={modalContentStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#003366', margin: 0 }}>
                {getTypeIcon(selectedIssue.type)} Issue Details
              </h2>
              <button
                onClick={() => setShowIssueModal(false)}
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
              <h3 style={{ color: '#003366' }}>{selectedIssue.title}</h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <strong>Type:</strong> {getTypeLabel(selectedIssue.type)}
                </div>
                <div>
                  <strong>Severity:</strong>
                  <span
                    style={{
                      backgroundColor: getSeverityColor(selectedIssue.severity),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      marginLeft: '0.5rem'
                    }}
                  >
                    {selectedIssue.severity}
                  </span>
                </div>
                <div>
                  <strong>Status:</strong>
                  <span
                    style={{
                      backgroundColor: getStatusColor(selectedIssue.status),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      marginLeft: '0.5rem'
                    }}
                  >
                    {selectedIssue.status.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <strong>Priority:</strong> {selectedIssue.priority}
                </div>
                <div>
                  <strong>Reporter:</strong> {selectedIssue.user_info.username} ({selectedIssue.user_info.role})
                </div>
                <div>
                  <strong>Created:</strong> {new Date(selectedIssue.created_at).toLocaleString()}
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <strong>Description:</strong>
                <div style={{
                  backgroundColor: '#f8f9fa',
                  padding: '1rem',
                  borderRadius: '8px',
                  marginTop: '0.5rem',
                  border: '1px solid #dee2e6'
                }}>
                  {selectedIssue.description}
                </div>
              </div>

              {selectedIssue.context && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Context:</strong>
                  <ul>
                    {selectedIssue.context.page && <li>Page: {selectedIssue.context.page}</li>}
                    {selectedIssue.context.browser && <li>Browser: {selectedIssue.context.browser}</li>}
                  </ul>
                </div>
              )}

              {selectedIssue.tags && selectedIssue.tags.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Tags:</strong>
                  <div style={{ marginTop: '0.5rem' }}>
                    {selectedIssue.tags.map((tag, index) => (
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

              {selectedIssue.resolution_notes && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Resolution Notes:</strong>
                  <div style={{
                    backgroundColor: '#d4edda',
                    padding: '1rem',
                    borderRadius: '8px',
                    marginTop: '0.5rem',
                    border: '1px solid #c3e6cb'
                  }}>
                    {selectedIssue.resolution_notes}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => {
                  setShowIssueModal(false);
                  handleUpdateIssue(selectedIssue);
                }}
                style={{
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer'
                }}
              >
                Update Issue
              </button>
              <button
                onClick={() => setShowIssueModal(false)}
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

      {/* Update Issue Modal */}
      {showUpdateModal && selectedIssue && (
        <div style={modalBackdropStyle} onClick={(e) => e.target === e.currentTarget && setShowUpdateModal(false)}>
          <div style={modalContentStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ color: '#003366', margin: 0 }}>Update Issue</h2>
              <button
                onClick={() => setShowUpdateModal(false)}
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

            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ color: '#003366' }}>{selectedIssue.title}</h4>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                  Status
                </label>
                <select
                  value={updateData.status}
                  onChange={(e) => setUpdateData({ ...updateData, status: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #ccc'
                  }}
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                  Priority
                </label>
                <select
                  value={updateData.priority}
                  onChange={(e) => setUpdateData({ ...updateData, priority: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #ccc'
                  }}
                >
                  <option value="urgent">Urgent</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: '#003366', fontWeight: '500' }}>
                Resolution Notes
              </label>
              <textarea
                value={updateData.resolution_notes}
                onChange={(e) => setUpdateData({ ...updateData, resolution_notes: e.target.value })}
                style={{
                  width: '100%',
                  minHeight: '100px',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  border: '1px solid #ccc',
                  resize: 'vertical',
                  boxSizing: 'border-box'
                }}
                placeholder="Add notes about the resolution or updates..."
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                onClick={() => setShowUpdateModal(false)}
                style={{
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitUpdate}
                style={{
                  backgroundColor: '#003366',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer'
                }}
              >
                Update Issue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminIssues;
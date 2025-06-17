import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const Users = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, hasRole, updateUserInfo } = useAuth();
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState(null);
  const [showChangeUsernameModal, setShowChangeUsernameModal] = useState(false);
  const [showChangeNameModal, setShowChangeNameModal] = useState(false);
  const [showChangeEmailModal, setShowChangeEmailModal] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [nameData, setNameData] = useState({
    firstName: '',
    lastName: ''
  });
  const [newEmail, setNewEmail] = useState('');
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchUserData();
  }, [isAuthenticated, navigate]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://127.0.0.1:8000/auth/me');
      setUserData(response.data);
      setNewUsername(response.data.username);
      setNewEmail(response.data.email);
      setNameData({
        firstName: response.data.first_name || '',
        lastName: response.data.last_name || ''
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching user data:', error);
      setError('Failed to load your profile data');
      setLoading(false);
    }
  };

  const handleChangeUsername = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await axios.put(`http://127.0.0.1:8000/users/${userData.id}`, {
        username: newUsername
      });
      setShowChangeUsernameModal(false);
      showSuccess('Username updated successfully!');

      // Update user context
      if (updateUserInfo) {
        updateUserInfo({
          ...userData,
          username: newUsername
        });
      }

      fetchUserData();
    } catch (error) {
      console.error('Error updating username:', error);
      setError(error.response?.data?.detail || 'Failed to update username');
    }
  };

  const handleChangeName = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await axios.put(`http://127.0.0.1:8000/users/${userData.id}`, {
        first_name: nameData.firstName,
        last_name: nameData.lastName
      });
      setShowChangeNameModal(false);
      showSuccess('Name updated successfully!');

      // Update user context
      if (updateUserInfo) {
        updateUserInfo({
          ...userData,
          first_name: nameData.firstName,
          last_name: nameData.lastName
        });
      }

      fetchUserData();
    } catch (error) {
      console.error('Error updating name:', error);
      setError(error.response?.data?.detail || 'Failed to update name');
    }
  };

  const handleChangeEmail = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await axios.put(`http://127.0.0.1:8000/users/${userData.id}`, {
        email: newEmail
      });
      setShowChangeEmailModal(false);
      showSuccess('Email updated successfully!');

      // Update user context
      if (updateUserInfo) {
        updateUserInfo({
          ...userData,
          email: newEmail
        });
      }

      fetchUserData();
    } catch (error) {
      console.error('Error updating email:', error);
      setError(error.response?.data?.detail || 'Failed to update email');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    try {
      await axios.put(`http://127.0.0.1:8000/users/${userData.id}`, {
        password: passwordData.newPassword
      });
      setShowChangePasswordModal(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      showSuccess('Password updated successfully!');
    } catch (error) {
      console.error('Error updating password:', error);
      setError(error.response?.data?.detail || 'Failed to update password');
    }
  };

  const showSuccess = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'owner':
        return '#dc3545'; // Red
      case 'admin':
        return '#0066cc'; // Blue
      default:
        return '#28a745'; // Green
    }
  };

  // Styles
  const containerStyle = {
    padding: '2rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)'
  };

  const contentContainerStyle = {
    maxWidth: '1200px',
    margin: '0 auto'
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

  const h1Style = {
    color: '#003366',
    fontSize: '2.5rem',
    marginBottom: '1rem'
  };

  const profileCardStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    marginBottom: '2rem'
  };

  const userInfoStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    marginBottom: '2rem'
  };

  const infoRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    borderBottom: '1px solid #f0f8ff'
  };

  const infoLabelStyle = {
    color: '#666',
    width: '120px',
    fontWeight: 'bold'
  };

  const infoValueStyle = {
    color: '#003366',
    flex: 1,
    fontWeight: '500'
  };

  const buttonContainerStyle = {
    display: 'flex',
    gap: '1rem',
    marginTop: '2rem',
    flexWrap: 'wrap',
    justifyContent: 'center'
  };

  const buttonStyle = (color = '#003366') => ({
    backgroundColor: color,
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '0.75rem 1.5rem',
    cursor: 'pointer',
    fontWeight: '500',
    fontSize: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
  });

  const roleBadgeStyle = (role) => ({
    backgroundColor: getRoleBadgeColor(role),
    color: 'white',
    padding: '4px 8px',
    borderRadius: '6px',
    fontSize: '0.8rem',
    textTransform: 'uppercase',
    fontWeight: 'bold'
  });

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
    maxWidth: '500px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
    position: 'relative'
  };

  const formGroupStyle = {
    marginBottom: '1.5rem'
  };

  const inputLabelStyle = {
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
    fontSize: '1rem'
  };

  const modalButtonsStyle = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '2rem'
  };

  const cancelButtonStyle = {
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '0.75rem 1.5rem',
    cursor: 'pointer'
  };

  const submitButtonStyle = {
    backgroundColor: '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '0.75rem 1.5rem',
    cursor: 'pointer'
  };

  const messageStyle = (isError) => ({
    padding: '1rem',
    borderRadius: '8px',
    backgroundColor: isError ? '#f8d7da' : '#d4edda',
    color: isError ? '#721c24' : '#155724',
    marginBottom: '1.5rem',
    textAlign: 'center'
  });

  if (loading || !userData) {
    return (
      <div style={containerStyle}>
        <div style={contentContainerStyle}>
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
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={contentContainerStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <h1 style={h1Style}>👤 My Profile</h1>
          <p>View and manage your account information</p>
        </div>

        {/* Messages */}
        {error && (
          <div style={messageStyle(true)}>
            {error}
          </div>
        )}

        {successMessage && (
          <div style={messageStyle(false)}>
            {successMessage}
          </div>
        )}

        {/* Profile Information */}
        <div style={profileCardStyle}>
          <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Account Information</h2>

          <div style={userInfoStyle}>
            <div style={infoRowStyle}>
              <div style={infoLabelStyle}>Username:</div>
              <div style={infoValueStyle}>{userData.username}</div>
            </div>

            <div style={infoRowStyle}>
              <div style={infoLabelStyle}>Name:</div>
              <div style={infoValueStyle}>
                {userData.first_name || userData.last_name
                  ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim()
                  : '(Not set)'}
              </div>
            </div>

            <div style={infoRowStyle}>
              <div style={infoLabelStyle}>Email:</div>
              <div style={infoValueStyle}>{userData.email}</div>
            </div>

            <div style={infoRowStyle}>
              <div style={infoLabelStyle}>Role:</div>
              <div>
                <span style={roleBadgeStyle(userData.role)}>
                  {userData.role}
                </span>
              </div>
            </div>

            <div style={infoRowStyle}>
              <div style={infoLabelStyle}>Member Since:</div>
              <div style={infoValueStyle}>
                {new Date(userData.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          <div style={buttonContainerStyle}>
            <button
              style={buttonStyle('#9c27b0')} // Purple color for username
              onClick={() => setShowChangeUsernameModal(true)}
            >
              👤 Change Username
            </button>

            <button
              style={buttonStyle('#ff9800')} // Orange color for name
              onClick={() => setShowChangeNameModal(true)}
            >
              📝 Update Name
            </button>

            <button
              style={buttonStyle('#28a745')} // Green color for email
              onClick={() => setShowChangeEmailModal(true)}
            >
              ✉️ Change Email
            </button>

            <button
              style={buttonStyle('#0066cc')} // Blue color for password
              onClick={() => setShowChangePasswordModal(true)}
            >
              🔑 Change Password
            </button>

            <button
              style={buttonStyle('#dc3545')} // Red color for logout
              onClick={() => {
                if (window.confirm('Are you sure you want to log out?')) {
                  logout();
                  navigate('/login');
                }
              }}
            >
              🚪 Logout
            </button>
          </div>
        </div>

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <button
            style={buttonStyle()}
            onClick={() => navigate('/dashboard')}
          >
            🏠 Back to Dashboard
          </button>

          {(userData.role === 'admin' || userData.role === 'owner') && (
            <button
              style={buttonStyle('#0066cc')}
              onClick={() => navigate('/user-management')}
            >
              👥 Manage Users
            </button>
          )}
        </div>
      </div>

      {/* Change Username Modal */}
      {showChangeUsernameModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Change Username</h2>

            <form onSubmit={handleChangeUsername}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="newUsername">New Username</label>
                <input
                  id="newUsername"
                  type="text"
                  style={inputStyle}
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  required
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowChangeUsernameModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Update Username
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Name Modal */}
      {showChangeNameModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Update Name</h2>

            <form onSubmit={handleChangeName}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="firstName">First Name</label>
                <input
                  id="firstName"
                  type="text"
                  style={inputStyle}
                  value={nameData.firstName}
                  onChange={(e) => setNameData({...nameData, firstName: e.target.value})}
                  placeholder="Enter your first name"
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="lastName">Last Name</label>
                <input
                  id="lastName"
                  type="text"
                  style={inputStyle}
                  value={nameData.lastName}
                  onChange={(e) => setNameData({...nameData, lastName: e.target.value})}
                  placeholder="Enter your last name"
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowChangeNameModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Update Name
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Email Modal */}
      {showChangeEmailModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Change Email</h2>

            <form onSubmit={handleChangeEmail}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="newEmail">New Email Address</label>
                <input
                  id="newEmail"
                  type="email"
                  style={inputStyle}
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowChangeEmailModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Update Email
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showChangePasswordModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Change Password</h2>

            <form onSubmit={handleChangePassword}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="currentPassword">Current Password</label>
                <input
                  id="currentPassword"
                  type="password"
                  style={inputStyle}
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  style={inputStyle}
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="confirmPassword">Confirm New Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  style={inputStyle}
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                  required
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowChangePasswordModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Update Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
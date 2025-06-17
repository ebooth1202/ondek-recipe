import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';

const UserManagement = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user'
  });
  const [actionUser, setActionUser] = useState(null);
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [showChangeRoleModal, setShowChangeRoleModal] = useState(false);
  const [newRole, setNewRole] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Check authentication and fetch users
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    // Only admins and owners can view all users
    if (!hasRole(['admin', 'owner'])) {
      // Redirect regular users to their profile page
      navigate('/users');
      return;
    }

    fetchUsers();
  }, [isAuthenticated, navigate, hasRole]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://127.0.0.1:8000/users');
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to load users. Please try again.');
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/auth/register', newUser);
      setShowAddUserModal(false);
      setNewUser({ username: '', email: '', password: '', role: 'user' });
      showSuccess('User added successfully!');
      fetchUsers();
    } catch (error) {
      console.error('Error adding user:', error);
      setError(error.response?.data?.detail || 'Failed to add user');
    }
  };

  const handleDeleteUser = async () => {
    if (!actionUser) return;

    try {
      await axios.delete(`http://127.0.0.1:8000/users/${actionUser.id}`);
      setShowConfirmDeleteModal(false);
      setActionUser(null);
      showSuccess('User deleted successfully!');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      setError(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!actionUser) return;

    try {
      await axios.put(`http://127.0.0.1:8000/users/${actionUser.id}`, {
        password: newPassword
      });
      setShowResetPasswordModal(false);
      setNewPassword('');
      setActionUser(null);
      showSuccess('Password reset successfully!');
    } catch (error) {
      console.error('Error resetting password:', error);
      setError(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const handleChangeRole = async () => {
    if (!actionUser) return;

    try {
      await axios.put(`http://127.0.0.1:8000/users/${actionUser.id}/role`, {
        role: newRole
      });
      setShowChangeRoleModal(false);
      setNewRole('');
      setActionUser(null);
      showSuccess('User role updated successfully!');
      fetchUsers();
    } catch (error) {
      console.error('Error changing role:', error);
      setError(error.response?.data?.detail || 'Failed to change user role');
    }
  };

  const showSuccess = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  // Helper function for role badge color
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

  // Common styles
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

  const buttonContainerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '2rem'
  };

  const buttonStyle = {
    backgroundColor: '#003366',
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
  };

  const tableContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    overflowX: 'auto'
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse'
  };

  const thStyle = {
    color: '#003366',
    textAlign: 'left',
    padding: '1rem',
    borderBottom: '2px solid #f0f8ff',
    fontWeight: '600'
  };

  const tdStyle = {
    padding: '1rem',
    borderBottom: '1px solid #f0f8ff',
    color: '#333'
  };

  const actionButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    color: '#003366',
    cursor: 'pointer',
    padding: '0.5rem',
    borderRadius: '4px',
    margin: '0 0.25rem'
  };

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

  const selectStyle = {
    width: '100%',
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid #ccc',
    fontSize: '1rem',
    backgroundColor: 'white'
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

  const deleteButtonStyle = {
    backgroundColor: '#dc3545',
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

  if (loading) {
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
          <h1 style={h1Style}>👥 User Management</h1>
          <p>Manage user accounts, roles, and permissions</p>
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

        {/* Action Buttons */}
        <div style={buttonContainerStyle}>
          <button
            style={buttonStyle}
            onClick={() => setShowAddUserModal(true)}
          >
            <span>➕</span> Add New User
          </button>
          <button
            style={buttonStyle}
            onClick={() => navigate('/dashboard')}
          >
            <span>🏠</span> Back to Dashboard
          </button>
        </div>

        {/* Users Table */}
        <div style={tableContainerStyle}>
          <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>System Users</h2>

          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Username</th>
                <th style={thStyle}>Email</th>
                <th style={thStyle}>Role</th>
                <th style={thStyle}>Created At</th>
                <th style={thStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td style={tdStyle}>{u.username}</td>
                  <td style={tdStyle}>{u.email}</td>
                  <td style={tdStyle}>
                    <span style={roleBadgeStyle(u.role)}>
                      {u.role}
                    </span>
                  </td>
                  <td style={tdStyle}>
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td style={tdStyle}>
                    <div style={{ display: 'flex' }}>
                      {/* Reset Password */}
                      <button
                        style={{
                          ...actionButtonStyle,
                          color: '#0066cc'
                        }}
                        title="Reset Password"
                        onClick={() => {
                          setActionUser(u);
                          setShowResetPasswordModal(true);
                        }}
                      >
                        🔑
                      </button>

                      {/* Change Role - Only available if not owner or self */}
                      {(user.id !== u.id && u.role !== 'owner') && (
                        <button
                          style={{
                            ...actionButtonStyle,
                            color: '#28a745'
                          }}
                          title="Change Role"
                          onClick={() => {
                            setActionUser(u);
                            setNewRole(u.role);
                            setShowChangeRoleModal(true);
                          }}
                        >
                          👑
                        </button>
                      )}

                      {/* Delete - Only available if not owner or self */}
                      {(user.id !== u.id && u.role !== 'owner') && (
                        <button
                          style={{
                            ...actionButtonStyle,
                            color: '#dc3545'
                          }}
                          title="Delete User"
                          onClick={() => {
                            setActionUser(u);
                            setShowConfirmDeleteModal(true);
                          }}
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddUserModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Add New User</h2>

            <form onSubmit={handleAddUser}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="username">Username</label>
                <input
                  id="username"
                  type="text"
                  style={inputStyle}
                  value={newUser.username}
                  onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  style={inputStyle}
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  style={inputStyle}
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="role">Role</label>
                <select
                  id="role"
                  style={selectStyle}
                  value={newUser.role}
                  onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                >
                  <option value="user">User</option>
                  {hasRole('owner') && (
                    <>
                      <option value="admin">Admin</option>
                      <option value="owner">Owner</option>
                    </>
                  )}
                  {hasRole('admin') && !hasRole('owner') && (
                    <option value="admin">Admin</option>
                  )}
                </select>
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowAddUserModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Add User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirm Delete Modal */}
      {showConfirmDeleteModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#dc3545', marginBottom: '1.5rem' }}>Confirm Deletion</h2>
            <p>Are you sure you want to delete the user <strong>{actionUser?.username}</strong>?</p>
            <p>This action cannot be undone.</p>

            <div style={modalButtonsStyle}>
              <button
                style={cancelButtonStyle}
                onClick={() => setShowConfirmDeleteModal(false)}
              >
                Cancel
              </button>
              <button
                style={deleteButtonStyle}
                onClick={handleDeleteUser}
              >
                Delete User
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Reset Password</h2>
            <p>Set a new password for <strong>{actionUser?.username}</strong>:</p>

            <form onSubmit={handleResetPassword}>
              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  style={inputStyle}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={() => setShowResetPasswordModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" style={submitButtonStyle}>
                  Reset Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Role Modal */}
      {showChangeRoleModal && (
        <div style={modalBackdropStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>Change User Role</h2>
            <p>Update role for <strong>{actionUser?.username}</strong>:</p>

            <div style={formGroupStyle}>
              <label style={inputLabelStyle} htmlFor="newRole">Role</label>
              <select
                id="newRole"
                style={selectStyle}
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
              >
                <option value="user">User</option>
                {hasRole('owner') && (
                  <>
                    <option value="admin">Admin</option>
                    <option value="owner">Owner</option>
                  </>
                )}
                {hasRole('admin') && !hasRole('owner') && (
                  <option value="admin">Admin</option>
                )}
              </select>
            </div>

            <div style={modalButtonsStyle}>
              <button
                style={cancelButtonStyle}
                onClick={() => setShowChangeRoleModal(false)}
              >
                Cancel
              </button>
              <button
                style={submitButtonStyle}
                onClick={handleChangeRole}
              >
                Update Role
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
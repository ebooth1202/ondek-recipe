import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const Users = () => {
  const navigate = useNavigate();
  const { user, hasRole, isAuthenticated, setUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // User editing state
  const [editMode, setEditMode] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: ''
  });

  // Modal states
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);
  const [actionUser, setActionUser] = useState(null);
  const [showChangeRoleModal, setShowChangeRoleModal] = useState(false);
  const [newRole, setNewRole] = useState('');

  // Check authentication and fetch users
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    // Only admins and owners can view all users
    if (!hasRole(['admin', 'owner'])) {
      // For regular users, only show their own profile
      setUsers([user]);
      setLoading(false);
      return;
    }

    fetchUsers();
  }, [isAuthenticated, navigate, hasRole, user]);

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

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const startEditingUser = (userToEdit) => {
    setEditingUser(userToEdit);
    setFormData({
      username: userToEdit.username,
      email: userToEdit.email,
      first_name: userToEdit.first_name || '',
      last_name: userToEdit.last_name || '',
      password: ''
    });
    setEditMode(true);
  };

  const cancelEditing = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      password: ''
    });
    setEditMode(false);
  };

  const updateUser = async (e) => {
    e.preventDefault();

    if (!editingUser) return;

    try {
      const updateData = {};

      // Only include fields that have changed
      if (formData.username !== editingUser.username) {
        updateData.username = formData.username;
      }

      if (formData.email !== editingUser.email) {
        updateData.email = formData.email;
      }

      if (formData.first_name !== editingUser.first_name) {
        updateData.first_name = formData.first_name;
      }

      if (formData.last_name !== editingUser.last_name) {
        updateData.last_name = formData.last_name;
      }

      if (formData.password && formData.password.trim() !== '') {
        updateData.password = formData.password;
      }

      // If nothing has changed, don't make the request
      if (Object.keys(updateData).length === 0) {
        setSuccessMessage('No changes to save');
        setTimeout(() => setSuccessMessage(''), 3000);
        return;
      }

      console.log('Updating user with data:', updateData);

      const response = await axios.put(`http://127.0.0.1:8000/users/${editingUser.id}`, updateData);

      // Update users list
      setUsers(users.map(u =>
        u.id === editingUser.id ? response.data : u
      ));

      // If updating current user, update auth context
      if (user.id === editingUser.id) {
        setUser(response.data);
      }

      setSuccessMessage('User updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);

      // Exit edit mode
      cancelEditing();

    } catch (error) {
      console.error('Error updating user:', error);
      setError(error.response?.data?.detail || 'Failed to update user');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/auth/register', {
        username: formData.username,
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        password: formData.password,
        role: 'user' // Default role for new users
      });
      setShowAddUserModal(false);
      setFormData({ username: '', email: '', first_name: '', last_name: '', password: '' });
      setSuccessMessage('User added successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
      fetchUsers();
    } catch (error) {
      console.error('Error adding user:', error);
      setError(error.response?.data?.detail || 'Failed to add user');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleDeleteUser = async () => {
    if (!actionUser) return;

    try {
      await axios.delete(`http://127.0.0.1:8000/users/${actionUser.id}`);
      setShowConfirmDeleteModal(false);
      setActionUser(null);
      setSuccessMessage('User deleted successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      setError(error.response?.data?.detail || 'Failed to delete user');
      setTimeout(() => setError(''), 5000);
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
      setSuccessMessage('User role updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
      fetchUsers();
    } catch (error) {
      console.error('Error changing role:', error);
      setError(error.response?.data?.detail || 'Failed to change user role');
      setTimeout(() => setError(''), 5000);
    }
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

  // Helper to format user display name
  const getDisplayName = (user) => {
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    } else if (user.first_name) {
      return user.first_name;
    } else if (user.last_name) {
      return user.last_name;
    } else {
      return 'Not set';
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

  const editFormStyle = {
    backgroundColor: '#f9f9f9',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1.5rem',
    marginBottom: '2rem'
  };

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

        {/* Edit User Form - Conditionally rendered */}
        {editMode && editingUser && (
          <div style={editFormStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1rem' }}>
              {editingUser.id === user.id ? 'Edit Your Profile' : `Edit User: ${editingUser.username}`}
            </h2>

            <form onSubmit={updateUser}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div style={formGroupStyle}>
                  <label style={inputLabelStyle} htmlFor="first_name">First Name</label>
                  <input
                    id="first_name"
                    name="first_name"
                    type="text"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    style={inputStyle}
                  />
                </div>

                <div style={formGroupStyle}>
                  <label style={inputLabelStyle} htmlFor="last_name">Last Name</label>
                  <input
                    id="last_name"
                    name="last_name"
                    type="text"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    style={inputStyle}
                  />
                </div>
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="username">Username</label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleInputChange}
                  style={inputStyle}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="email">Email</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  style={inputStyle}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="password">
                  {editingUser.id === user.id ? 'New Password (leave empty to keep current)' : 'Reset Password (leave empty to keep current)'}
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  style={inputStyle}
                />
              </div>

              <div style={modalButtonsStyle}>
                <button
                  type="button"
                  style={cancelButtonStyle}
                  onClick={cancelEditing}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={submitButtonStyle}
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Action Buttons */}
        <div style={buttonContainerStyle}>
          {hasRole(['admin', 'owner']) && (
            <button
              style={buttonStyle}
              onClick={() => {
                setFormData({ username: '', email: '', first_name: '', last_name: '', password: '' });
                setShowAddUserModal(true);
              }}
            >
              <span>➕</span> Add New User
            </button>
          )}
          <button
            style={buttonStyle}
            onClick={() => navigate('/dashboard')}
          >
            <span>🏠</span> Back to Dashboard
          </button>
        </div>

        {/* Users Table */}
        <div style={tableContainerStyle}>
          <h2 style={{ color: '#003366', marginBottom: '1.5rem' }}>
            {hasRole(['admin', 'owner']) ? 'System Users' : 'Your Account'}
          </h2>

          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Username</th>
                <th style={thStyle}>Name</th>
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
                  <td style={tdStyle}>{getDisplayName(u)}</td>
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
                      {/* Edit User */}
                      <button
                        style={{
                          ...actionButtonStyle,
                          color: '#28a745'
                        }}
                        title="Edit User"
                        onClick={() => startEditingUser(u)}
                      >
                        ✏️
                      </button>

                      {/* Change Role - Only available for admins/owners */}
                      {hasRole(['admin', 'owner']) && (user.id !== u.id && u.role !== 'owner') && (
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

                      {/* Delete - Only available for admins/owners */}
                      {hasRole(['admin', 'owner']) && (user.id !== u.id && u.role !== 'owner') && (
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={formGroupStyle}>
                  <label style={inputLabelStyle} htmlFor="add_first_name">First Name</label>
                  <input
                    id="add_first_name"
                    name="first_name"
                    type="text"
                    style={inputStyle}
                    value={formData.first_name}
                    onChange={handleInputChange}
                  />
                </div>

                <div style={formGroupStyle}>
                  <label style={inputLabelStyle} htmlFor="add_last_name">Last Name</label>
                  <input
                    id="add_last_name"
                    name="last_name"
                    type="text"
                    style={inputStyle}
                    value={formData.last_name}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="add_username">Username</label>
                <input
                  id="add_username"
                  name="username"
                  type="text"
                  style={inputStyle}
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="add_email">Email</label>
                <input
                  id="add_email"
                  name="email"
                  type="email"
                  style={inputStyle}
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={inputLabelStyle} htmlFor="add_password">Password</label>
                <input
                  id="add_password"
                  name="password"
                  type="password"
                  style={inputStyle}
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                />
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

export default Users;
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(formData.username, formData.password);

    if (result.success) {
      navigate('/recipes');
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="page-container">
      <div className="form-container">
        <h1 className="page-title">Login</h1>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username" className="form-label">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="form-control"
              placeholder="Enter your username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="form-control"
              placeholder="Enter your password"
              required
            />
          </div>

          <div className="form-group">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%' }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </div>
        </form>

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#0066cc', textDecoration: 'none' }}>
              Register here
            </Link>
          </p>

          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            background: '#f0f8ff',
            borderRadius: '10px',
            border: '1px solid #003366'
          }}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>Demo Account</h3>
            <p><strong>Username:</strong> owner</p>
            <p><strong>Password:</strong> admin123</p>
            <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '1rem' }}>
              Use this account to test the application features
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
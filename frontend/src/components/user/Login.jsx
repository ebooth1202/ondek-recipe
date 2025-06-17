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
      navigate('/dashboard');
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const handleDemoLogin = () => {
    setFormData({
      username: 'owner',
      password: 'admin123'
    });
  };

  return (
    <div style={{
      padding: '2rem',
      backgroundColor: '#f0f8ff',
      minHeight: 'calc(100vh - 80px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        maxWidth: '500px',
        width: '100%',
        background: 'white',
        border: '2px solid #003366',
        borderRadius: '15px',
        padding: '2rem',
        boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
      }}>
        <h1 style={{
          textAlign: 'center',
          color: '#003366',
          fontSize: '2rem',
          marginBottom: '2rem'
        }}>
          🔑 Login
        </h1>

        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #f5c6cb'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="username"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#003366',
                fontWeight: '500'
              }}
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #003366',
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Enter your username"
              required
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="password"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#003366',
                fontWeight: '500'
              }}
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '12px',
                border: '2px solid #003366',
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Enter your password"
              required
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px 24px',
                border: 'none',
                borderRadius: '10px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: loading ? 'not-allowed' : 'pointer',
                backgroundColor: loading ? '#ccc' : '#003366',
                color: 'white',
                transition: 'all 0.3s ease'
              }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </div>
        </form>

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p>
            Don't have an account?{' '}
            <Link
              to="/register"
              style={{
                color: '#0066cc',
                textDecoration: 'none',
                fontWeight: '500'
              }}
            >
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
            <h3 style={{
              color: '#003366',
              marginBottom: '1rem',
              fontSize: '1.1rem'
            }}>
              🧪 Demo Account
            </h3>
            <p style={{ margin: '0.5rem 0' }}>
              <strong>Username:</strong> owner
            </p>
            <p style={{ margin: '0.5rem 0' }}>
              <strong>Password:</strong> admin123
            </p>
            <button
              type="button"
              onClick={handleDemoLogin}
              style={{
                marginTop: '1rem',
                padding: '8px 16px',
                border: '2px solid #003366',
                borderRadius: '8px',
                backgroundColor: 'white',
                color: '#003366',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Fill Demo Credentials
            </button>
            <p style={{
              fontSize: '0.9rem',
              color: '#666',
              marginTop: '1rem',
              margin: '1rem 0 0 0'
            }}>
              Use this account to test all application features
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
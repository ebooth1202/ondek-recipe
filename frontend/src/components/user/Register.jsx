import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    // Clear specific error when user types
    if (errors[e.target.name]) {
      setErrors({
        ...errors,
        [e.target.name]: '',
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formErrors = validateForm();
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    const result = await register(formData.username, formData.email, formData.password);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setErrors({ submit: result.error });
    }

    setLoading(false);
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
          👤 Create Account
        </h1>

        {errors.submit && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #f5c6cb'
          }}>
            {errors.submit}
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
                border: `2px solid ${errors.username ? '#dc3545' : '#003366'}`,
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Choose a username"
              required
            />
            {errors.username && (
              <div style={{
                color: '#dc3545',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}>
                {errors.username}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="email"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#003366',
                fontWeight: '500'
              }}
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '12px',
                border: `2px solid ${errors.email ? '#dc3545' : '#003366'}`,
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Enter your email"
              required
            />
            {errors.email && (
              <div style={{
                color: '#dc3545',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}>
                {errors.email}
              </div>
            )}
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
                border: `2px solid ${errors.password ? '#dc3545' : '#003366'}`,
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Create a password"
              required
            />
            {errors.password && (
              <div style={{
                color: '#dc3545',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}>
                {errors.password}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="confirmPassword"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#003366',
                fontWeight: '500'
              }}
            >
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '12px',
                border: `2px solid ${errors.confirmPassword ? '#dc3545' : '#003366'}`,
                borderRadius: '10px',
                fontSize: '16px',
                backgroundColor: 'white'
              }}
              placeholder="Confirm your password"
              required
            />
            {errors.confirmPassword && (
              <div style={{
                color: '#dc3545',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}>
                {errors.confirmPassword}
              </div>
            )}
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
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </div>
        </form>

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p>
            Already have an account?{' '}
            <Link
              to="/login"
              style={{
                color: '#0066cc',
                textDecoration: 'none',
                fontWeight: '500'
              }}
            >
              Login here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
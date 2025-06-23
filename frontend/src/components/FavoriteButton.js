// FavoriteButton.js - Updated with styled theme to match recipe page
import React, { useState } from 'react';
import { Heart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const FavoriteButton = ({ recipeId, isFavorited: initialFavorited = false, onToggle }) => {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);
  const { apiBaseUrl } = useAuth();

  const handleToggle = async () => {
    setIsLoading(true);
    try {
      const method = isFavorited ? 'DELETE' : 'POST';
      const token = localStorage.getItem('token');

      const response = await fetch(`${apiBaseUrl}/recipes/${recipeId}/favorite`, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setIsFavorited(!isFavorited);
        if (onToggle) onToggle(!isFavorited);
      } else {
        const error = await response.json();
        console.error('Error toggling favorite:', error);
        alert(error.detail || 'Error updating favorites');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const buttonStyle = {
    background: isFavorited
      ? 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)'
      : 'linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%)',
    color: isFavorited ? 'white' : '#003366',
    border: `2px solid ${isFavorited ? '#dc3545' : '#003366'}`,
    borderRadius: '15px',
    padding: '12px 20px',
    cursor: isLoading ? 'not-allowed' : 'pointer',
    fontSize: '16px',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    boxShadow: isFavorited
      ? '0 4px 12px rgba(220, 53, 69, 0.3)'
      : '0 4px 12px rgba(0, 51, 102, 0.1)',
    transition: 'all 0.3s ease',
    transform: 'scale(1)',
    opacity: isLoading ? 0.7 : 1,
    minWidth: '160px',
    justifyContent: 'center'
  };

  const handleMouseEnter = (e) => {
    if (isLoading) return;

    if (isFavorited) {
      e.target.style.background = 'linear-gradient(135deg, #c82333 0%, #a71e2a 100%)';
      e.target.style.transform = 'scale(1.05)';
      e.target.style.boxShadow = '0 6px 16px rgba(220, 53, 69, 0.4)';
    } else {
      e.target.style.background = 'linear-gradient(135deg, #003366 0%, #002244 100%)';
      e.target.style.color = 'white';
      e.target.style.transform = 'scale(1.05)';
      e.target.style.boxShadow = '0 6px 16px rgba(0, 51, 102, 0.3)';
    }
  };

  const handleMouseLeave = (e) => {
    if (isLoading) return;

    if (isFavorited) {
      e.target.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
      e.target.style.transform = 'scale(1)';
      e.target.style.boxShadow = '0 4px 12px rgba(220, 53, 69, 0.3)';
    } else {
      e.target.style.background = 'linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%)';
      e.target.style.color = '#003366';
      e.target.style.transform = 'scale(1)';
      e.target.style.boxShadow = '0 4px 12px rgba(0, 51, 102, 0.1)';
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading}
      style={buttonStyle}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      {isLoading ? (
        <>
          <span style={{ fontSize: '18px' }}>⏳</span>
          <span style={{ fontSize: '14px', fontWeight: '600' }}>Saving...</span>
        </>
      ) : (
        <>
          <Heart
            style={{
              width: '20px',
              height: '20px',
              fill: isFavorited ? 'white' : 'none',
              stroke: isFavorited ? 'white' : '#003366',
              strokeWidth: '2px',
              transition: 'all 0.3s ease',
              transform: isFavorited ? 'scale(1.1)' : 'scale(1)',
              filter: isFavorited ? 'drop-shadow(0 0 4px rgba(255, 255, 255, 0.5))' : 'none'
            }}
          />
          <span style={{ fontSize: '14px', fontWeight: '600' }}>
            {isFavorited ? 'Favorited' : 'Add to Favorites'}
          </span>
        </>
      )}
    </button>
  );
};

export default FavoriteButton;
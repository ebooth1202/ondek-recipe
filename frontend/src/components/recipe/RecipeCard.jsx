import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Dynamic API base URL - detects environment automatically
const getApiBaseUrl = () => {
  // If running locally (localhost or 127.0.0.1), use local backend
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }
  // If in production, use your production backend URL
  // Replace this with your actual production backend URL
  return 'https://ondek-recipe-testing-2777bc2152f6.herokuapp.com';
};

const API_BASE_URL = getApiBaseUrl();

// Format genre display name
const formatGenreName = (genre) => {
  if (!genre) return '';

  return genre.charAt(0).toUpperCase() + genre.slice(1);
};

// Format dietary restriction display name
const formatDietaryRestrictionName = (restriction) => {
  if (!restriction) return '';

  switch(restriction) {
    case 'gluten_free': return 'Gluten Free';
    case 'dairy_free': return 'Dairy Free';
    case 'egg_free': return 'Egg Free';
    default:
      return restriction.charAt(0).toUpperCase() + restriction.slice(1);
  }
};

const RecipeCard = ({ recipe, onFavoriteToggle }) => {
  const navigate = useNavigate();
  const [isFavorited, setIsFavorited] = useState(recipe.is_favorited || false);
  const [isToggling, setIsToggling] = useState(false);

  // Check favorite status when component mounts
  useEffect(() => {
    const checkFavoriteStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/recipes/${recipe.id}/favorite-status`);
        setIsFavorited(response.data.is_favorited);
      } catch (error) {
        console.error('Error checking favorite status:', error);
      }
    };

    if (recipe.id) {
      checkFavoriteStatus();
    }
  }, [recipe.id]);

  const handleClick = () => {
    navigate(`/recipes/${recipe.id}`);
  };

  const handleFavoriteClick = async (e) => {
    e.stopPropagation(); // Prevent navigating to recipe detail

    if (isToggling) return; // Prevent multiple clicks

    setIsToggling(true);
    try {
      if (isFavorited) {
        // Remove from favorites
        await axios.delete(`${API_BASE_URL}/recipes/${recipe.id}/favorite`);
      } else {
        // Add to favorites
        await axios.post(`${API_BASE_URL}/recipes/${recipe.id}/favorite`);
      }

      setIsFavorited(!isFavorited);
      // Call the callback if provided
      if (onFavoriteToggle) {
        onFavoriteToggle(recipe.id, !isFavorited);
      }
    } catch (error) {
      console.error('Error toggling favorite status:', error);
    } finally {
      setIsToggling(false);
    }
  };

  const getGenreEmoji = (genre) => {
    const emojis = {
      breakfast: '🥞',
      lunch: '🥪',
      dinner: '🍽️',
      snack: '🍿',
      dessert: '🍰',
      appetizer: '🥗'
    };
    return emojis[genre] || '🍳';
  };

  const getGenreColor = (genre) => {
    const colors = {
      breakfast: '#ffc107',
      lunch: '#28a745',
      dinner: '#dc3545',
      snack: '#17a2b8',
      dessert: '#e83e8c',
      appetizer: '#6f42c1'
    };
    return colors[genre] || '#003366';
  };

  // Styles - Made card smaller
  const cardStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.25rem', // Reduced from 1.5rem
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    minHeight: '180px', // Reduced from 250px
    display: 'flex',
    flexDirection: 'column',
    position: 'relative' // For absolute positioning of favorite button and dietary tags
  };

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '1rem'
  };

  const titleStyle = {
    color: '#003366',
    fontSize: '1.3rem',
    margin: 0,
    flex: 1,
    lineHeight: '1.3',
    minHeight: '3.4rem', // Fixed height to accommodate 2 lines consistently
    display: 'flex',
    alignItems: 'flex-start' // Align text to top of the fixed height area
  };

  const badgeContainerStyle = {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end'
  };

  const genreBadgeStyle = {
    backgroundColor: getGenreColor(recipe?.genre),
    color: 'white',
    padding: '4px 8px',
    borderRadius: '20px',
    fontSize: '0.8rem',
    fontWeight: '500',
    marginBottom: '4px' // Add space for dietary restriction tags below
  };

  const dietaryTagsContainerStyle = {
    position: 'absolute',
    top: '32px', // Position below the genre badge (genre badge height + margin)
    right: '0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '2px', // Small gap between multiple dietary restriction tags
    zIndex: 1
  };

  const dietaryBadgeStyle = {
    backgroundColor: '#28a745', // Green color for dietary restrictions
    color: 'white',
    padding: '2px 6px',
    borderRadius: '12px',
    fontSize: '0.7rem',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)' // Subtle shadow to make it stand out
  };

  const metaStyle = {
    display: 'flex',
    justifyContent: 'center',
    gap: '2rem',
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '1rem' // Reduced from 1.5rem
  };

  return (
    <div
      onClick={handleClick}
      style={cardStyle}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-5px)';
        e.currentTarget.style.boxShadow = '0 8px 20px rgba(0, 51, 102, 0.2)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 51, 102, 0.1)';
      }}
    >
      {/* Favorite Button - Absolutely positioned at top center */}
      <button
        onClick={handleFavoriteClick}
        style={{
          position: 'absolute',
          top: '-15px',  // Position slightly above the card
          left: '50%',
          transform: 'translateX(-50%)', // Center horizontally
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: isFavorited ? '#ffc107' : 'white',
          color: isFavorited ? 'white' : '#666',
          border: '2px solid ' + (isFavorited ? '#ffc107' : '#e0e0e0'),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          zIndex: 2,
          boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.2s ease',
          fontSize: '18px'
        }}
        disabled={isToggling}
      >
        {isToggling ? (
          <span>⏳</span>
        ) : (
          <span>{isFavorited ? '★' : '☆'}</span>
        )}
      </button>

      {/* Header */}
      <div style={headerStyle}>
        <h3 style={titleStyle}>{recipe.recipe_name}</h3>
        <div style={badgeContainerStyle}>
          {/* Genre Badge */}
          <div style={genreBadgeStyle}>
            {getGenreEmoji(recipe.genre)} {formatGenreName(recipe.genre)}
          </div>

          {/* Dietary Restrictions - Absolutely positioned below genre badge */}
          {recipe.dietary_restrictions && recipe.dietary_restrictions.length > 0 && (
            <div style={dietaryTagsContainerStyle}>
              {recipe.dietary_restrictions.map((restriction, index) => (
                <div
                  key={restriction}
                  style={dietaryBadgeStyle}
                >
                  {formatDietaryRestrictionName(restriction)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Meta Information */}
      <div style={metaStyle}>
        <span>👥 Serves {recipe.serving_size}</span>
        <span>👨‍🍳 By {recipe.created_by}</span>
      </div>

      {/* Description Section - Truncated to 4 lines with Total Time Box */}
      <div style={{
        flex: 1,
        marginBottom: '0.5rem', // Reduced from 1rem
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem' // Reduced from 0.75rem
      }}>
        {/* Truncated Description */}
        <div style={{
          fontSize: '0.85rem', // Slightly smaller font
          color: '#555',
          lineHeight: '1.3', // Adjusted line height
          textAlign: 'left', // Changed from center to left for better text flow
          padding: '0.4rem 0.5rem', // Reduced top/bottom padding
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #e9ecef',
          height: '70px', // Increased height slightly
          display: 'flex',
          alignItems: 'flex-start', // Changed from center to flex-start
          justifyContent: 'flex-start', // Changed alignment
          fontStyle: recipe.description ? 'normal' : 'italic',
          overflow: 'hidden',
          position: 'relative'
        }}>
          <div style={{
            display: '-webkit-box',
            WebkitLineClamp: 4,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            width: '100%',
            paddingTop: '2px' // Small padding to prevent top cutoff
          }}>
            {recipe.description || 'No description available'}
          </div>
        </div>

        {/* Total Time Box - Made smaller and half width */}
        <div style={{
          backgroundColor: '#e6f0ff',
          border: '1px solid #003366', // Thinner border
          borderRadius: '6px', // Smaller border radius
          padding: '0.25rem 0.5rem', // Reduced padding
          textAlign: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.3rem', // Reduced gap
          minHeight: '35px', // Increased to 35px as requested
          width: '50%', // Half the width
          margin: '0 auto' // Center the box
        }}>
          <span style={{
            fontSize: '0.9rem' // Smaller emoji
          }}>⏱️</span>
          <div>
            <div style={{
              fontSize: '0.65rem', // Smaller label
              color: '#666',
              fontWeight: '500',
              lineHeight: '1'
            }}>
              Total Time
            </div>
            <div style={{
              fontSize: '0.75rem', // Smaller time text
              color: '#003366',
              fontWeight: '700',
              lineHeight: '1'
            }}>
              {((recipe.prep_time || 0) + (recipe.cook_time || 0)) || 'Not set'}
              {((recipe.prep_time || 0) + (recipe.cook_time || 0)) ? ' mins' : ''}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: '1rem',
        borderTop: '1px solid #f0f8ff',
        marginTop: 'auto'
      }}>
        <span style={{
          fontSize: '0.8rem',
          color: '#999'
        }}>
          Created: {new Date(recipe.created_at).toLocaleDateString()}
        </span>
        <div style={{
          background: '#f0f8ff',
          color: '#003366',
          padding: '4px 8px',
          borderRadius: '8px',
          fontSize: '0.8rem',
          fontWeight: '500'
        }}>
          Click to view →
        </div>
      </div>
    </div>
  );
};

export default RecipeCard;
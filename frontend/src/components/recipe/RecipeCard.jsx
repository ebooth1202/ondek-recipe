import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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
        const response = await axios.get(`http://127.0.0.1:8000/recipes/${recipe.id}/favorite-status`);
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
        await axios.delete(`http://127.0.0.1:8000/recipes/${recipe.id}/favorite`);
      } else {
        // Add to favorites
        await axios.post(`http://127.0.0.1:8000/recipes/${recipe.id}/favorite`);
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
    lineHeight: '1.3'
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

      {/* Description Section - Replaces ingredients and instructions */}
      <div style={{
        flex: 1,
        marginBottom: '1rem',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          fontSize: '0.95rem',
          color: '#555',
          lineHeight: '1.5',
          textAlign: 'center',
          padding: '0.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #e9ecef',
          minHeight: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontStyle: recipe.description ? 'normal' : 'italic'
        }}>
          {recipe.description || 'No description available'}
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
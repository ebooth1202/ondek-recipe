import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL, API_ENDPOINTS, apiClient } from '../../utils/api';

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
        const response = await apiClient.get(API_ENDPOINTS.RECIPE_FAVORITE_STATUS(recipe.id));
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
        await apiClient.delete(API_ENDPOINTS.RECIPE_FAVORITE(recipe.id));
      } else {
        // Add to favorites
        await apiClient.post(API_ENDPOINTS.RECIPE_FAVORITE(recipe.id));
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

  // Rest of your component styles and JSX remain exactly the same...
  const cardStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.25rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    minHeight: '180px',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative'
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
    minHeight: '3.4rem',
    display: 'flex',
    alignItems: 'flex-start'
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
    marginBottom: '4px'
  };

  const dietaryTagsContainerStyle = {
    position: 'absolute',
    top: '32px',
    right: '0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '2px',
    zIndex: 1
  };

  const dietaryBadgeStyle = {
    backgroundColor: '#28a745',
    color: 'white',
    padding: '2px 6px',
    borderRadius: '12px',
    fontSize: '0.7rem',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)'
  };

  const metaStyle = {
    display: 'flex',
    justifyContent: 'center',
    gap: '2rem',
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '1rem'
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
          top: '-15px',
          left: '50%',
          transform: 'translateX(-50%)',
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
        marginBottom: '0.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}>
        {/* Truncated Description */}
        <div style={{
          fontSize: '0.85rem',
          color: '#555',
          lineHeight: '1.3',
          textAlign: 'left',
          padding: '0.4rem 0.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #e9ecef',
          height: '70px',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'flex-start',
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
            paddingTop: '2px'
          }}>
            {recipe.description || 'No description available'}
          </div>
        </div>

        {/* Total Time Box - Made smaller and half width */}
        <div style={{
          backgroundColor: '#e6f0ff',
          border: '1px solid #003366',
          borderRadius: '6px',
          padding: '0.25rem 0.5rem',
          textAlign: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.3rem',
          minHeight: '35px',
          width: '50%',
          margin: '0 auto'
        }}>
          <span style={{
            fontSize: '0.9rem'
          }}>⏱️</span>
          <div>
            <div style={{
              fontSize: '0.65rem',
              color: '#666',
              fontWeight: '500',
              lineHeight: '1'
            }}>
              Total Time
            </div>
            <div style={{
              fontSize: '0.75rem',
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
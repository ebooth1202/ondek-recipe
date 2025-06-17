import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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

  // Styles
  const cardStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.5rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    minHeight: '250px',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative' // For absolute positioning of favorite button
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

  const genreBadgeStyle = {
    backgroundColor: getGenreColor(recipe.genre),
    color: 'white',
    padding: '4px 8px',
    borderRadius: '15px',
    fontSize: '0.8rem',
    fontWeight: '500',
    textTransform: 'uppercase',
    whiteSpace: 'nowrap',
    marginLeft: '1rem'
  };

  const metaStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '1rem',
    fontSize: '0.9rem',
    color: '#666'
  };

  const sectionStyle = {
    marginBottom: '1rem',
    flex: 1
  };

  const sectionTitleStyle = {
    color: '#003366',
    fontSize: '1rem',
    marginBottom: '0.5rem'
  };

  const ingredientsListStyle = {
    maxHeight: '80px',
    overflowY: 'auto',
    fontSize: '0.9rem',
    color: '#666'
  };

  const ingredientItemStyle = {
    padding: '2px 0',
    borderBottom: '1px solid #f0f8ff'
  };

  const instructionsStyle = {
    fontSize: '0.9rem',
    color: '#666',
    lineHeight: '1.4'
  };

  const footerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '1rem',
    borderTop: '1px solid #f0f8ff',
    marginTop: 'auto'
  };

  const dateStyle = {
    fontSize: '0.8rem',
    color: '#999'
  };

  const viewButtonStyle = {
    background: '#f0f8ff',
    color: '#003366',
    padding: '4px 8px',
    borderRadius: '8px',
    fontSize: '0.8rem',
    fontWeight: '500'
  };

  // Favorite button style - positioned absolutely at the top center
  const favoriteButtonStyle = {
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
        style={favoriteButtonStyle}
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
        <div style={genreBadgeStyle}>
          {getGenreEmoji(recipe.genre)} {recipe.genre}
        </div>
      </div>

      {/* Meta Information */}
      <div style={metaStyle}>
        <span>👥 Serves {recipe.serving_size}</span>
        <span>👨‍🍳 By {recipe.created_by}</span>
      </div>

      {/* Ingredients Preview */}
      <div style={sectionStyle}>
        <h4 style={sectionTitleStyle}>
          🛒 Ingredients ({recipe.ingredients.length})
        </h4>
        <div style={ingredientsListStyle}>
          {recipe.ingredients.slice(0, 5).map((ingredient, index) => (
            <div
              key={index}
              style={{
                ...ingredientItemStyle,
                borderBottom: index < Math.min(4, recipe.ingredients.length - 1)
                  ? '1px solid #f0f8ff'
                  : 'none'
              }}
            >
              {ingredient.quantity} {ingredient.unit} {ingredient.name}
            </div>
          ))}
          {recipe.ingredients.length > 5 && (
            <div style={{
              padding: '2px 0',
              fontStyle: 'italic',
              color: '#003366'
            }}>
              + {recipe.ingredients.length - 5} more...
            </div>
          )}
        </div>
      </div>

      {/* Instructions Preview */}
      <div style={sectionStyle}>
        <h4 style={sectionTitleStyle}>
          📝 Instructions ({recipe.instructions.length} steps)
        </h4>
        <div style={instructionsStyle}>
          {recipe.instructions[0] && (
            <div>
              <strong>1.</strong> {recipe.instructions[0].length > 80
                ? `${recipe.instructions[0].substring(0, 80)}...`
                : recipe.instructions[0]
              }
            </div>
          )}
          {recipe.instructions.length > 1 && (
            <div style={{
              marginTop: '4px',
              fontStyle: 'italic',
              color: '#003366'
            }}>
              + {recipe.instructions.length - 1} more step{recipe.instructions.length - 1 !== 1 ? 's' : ''}...
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={footerStyle}>
        <span style={dateStyle}>
          Created: {new Date(recipe.created_at).toLocaleDateString()}
        </span>
        <div style={viewButtonStyle}>
          Click to view →
        </div>
      </div>
    </div>
  );
};

export default RecipeCard;

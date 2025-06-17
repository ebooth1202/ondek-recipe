import React from 'react';
import { useNavigate } from 'react-router-dom';

const RecipeCard = ({ recipe }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/recipes/${recipe.id}`);
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
    flexDirection: 'column'
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
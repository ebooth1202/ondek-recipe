// Updated RecipeDetail.jsx file with dietary restrictions display
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RatingsAndReviews from '../components/RatingsAndReviews';
import FavoriteButton from '../components/FavoriteButton';
import RecipeForm from '../components/recipe/RecipeForm';
import axios from 'axios';
import { Fraction } from 'fraction.js';

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

const RecipeDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user, hasRole } = useAuth();

  // State management
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showIngredients, setShowIngredients] = useState(true);
  const [showInstructions, setShowInstructions] = useState(true);
  const [servingMultiplier, setServingMultiplier] = useState(1);
  const [checkedIngredients, setCheckedIngredients] = useState(new Set());
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [favoriteStatus, setFavoriteStatus] = useState(false);
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    if (recipe) {
      console.log('Recipe ID:', recipe.id);
      console.log('Recipe Name:', recipe.recipe_name);
      console.log('Prep Time:', recipe.prep_time);
      console.log('Cook Time:', recipe.cook_time);
      console.log('Dietary Restrictions:', recipe.dietary_restrictions);
      console.log('Full Recipe Object:', JSON.stringify(recipe, null, 2));
    }
  }, [recipe]);

  // Fetch recipe and favorite status on component mount
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    const fetchRecipeData = async () => {
      try {
        setLoading(true);
        console.log(`Fetching recipe with ID: ${id}`);

        // Fetch recipe and favorite status in parallel
        const [recipeResponse, favoriteResponse] = await Promise.all([
          axios.get(`http://127.0.0.1:8000/recipes/${id}`),
          axios.get(`http://127.0.0.1:8000/recipes/${id}/favorite-status`)
        ]);

        console.log('Recipe received:', recipeResponse.data);
        console.log('Favorite status:', favoriteResponse.data);

        setRecipe(recipeResponse.data);
        setFavoriteStatus(favoriteResponse.data.is_favorited);
      } catch (error) {
        console.error('Error fetching recipe data:', error);
        setError('Recipe not found or failed to load');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipeData();
  }, [id, isAuthenticated, navigate]);

  // Fraction utilities
  const formatQuantity = (value) => {
    if (value === undefined || value === null || value === '') return '';

    try {
      // Handle integer values
      if (Number.isInteger(Number(value))) {
        return String(value);
      }

      // Convert to fraction
      const frac = new Fraction(value);

      // If it's a proper fraction (less than 1)
      if (frac.compare(1) < 0) {
        return `${frac.n}/${frac.d}`;
      }

      // If it's an improper fraction (greater than or equal to 1)
      const wholePart = Math.floor(frac.valueOf());
      const fractionalPart = frac.subtract(wholePart);

      if (fractionalPart.valueOf() === 0) {
        return String(wholePart);
      }

      return `${wholePart} ${fractionalPart.n}/${fractionalPart.d}`;
    } catch (e) {
      console.error("Error formatting fraction:", e);
      return String(value);
    }
  };

  // Helper functions
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

  const canEditOrDelete = () => {
    if (!recipe || !user) return false;
    return recipe.created_by === user.username || hasRole(['admin', 'owner']);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete "${recipe.recipe_name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(true);
      await axios.delete(`http://127.0.0.1:8000/recipes/${id}`);
      navigate('/recipes');
    } catch (error) {
      console.error('Error deleting recipe:', error);
      alert('Failed to delete recipe. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const toggleIngredient = (index) => {
    const newChecked = new Set(checkedIngredients);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedIngredients(newChecked);
  };

  const toggleStep = (index) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(index)) {
      newCompleted.delete(index);
    } else {
      newCompleted.add(index);
    }
    setCompletedSteps(newCompleted);
  };

  const adjustServings = (multiplier) => {
    setServingMultiplier(multiplier);
  };

  const calculateQuantity = (originalQuantity) => {
  if (originalQuantity === undefined || originalQuantity === null || originalQuantity === '')
    return '';

  try {
    // Scale the quantity by the serving multiplier
    const scaledValue = originalQuantity * servingMultiplier;

    // Handle integer values
    if (Number.isInteger(scaledValue)) {
      return String(scaledValue);
    }

    // Convert to fraction
    const frac = new Fraction(scaledValue);

    // If it's a proper fraction (less than 1)
    if (frac.compare(1) < 0) {
      return `${frac.n}/${frac.d}`;
    }

    // If it's an improper fraction (greater than or equal to 1)
    const wholePart = Math.floor(frac.valueOf());
    const fractionalPart = frac.subtract(wholePart);

    if (fractionalPart.valueOf() === 0) {
      return String(wholePart);
    }

    return `${wholePart} ${fractionalPart.n}/${fractionalPart.d}`;
  } catch (e) {
    console.error("Error formatting scaled quantity:", e);
    return String(originalQuantity * servingMultiplier);
  }
};

  const handleFavoriteToggle = (isFavorited) => {
    setFavoriteStatus(isFavorited);
  };

  // Edit functions
  const handleEnableEdit = () => {
    setEditMode(true);
  };

  const handleEditSuccess = (updatedRecipe) => {
    // Update the recipe state with the updated data
    setRecipe(updatedRecipe);
    // Exit edit mode
    setEditMode(false);
  };

  // Render guards
  if (!isAuthenticated()) {
    return null;
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: 'calc(100vh - 80px)',
        backgroundColor: '#f0f8ff'
      }}>
        <div style={{
          padding: '3rem',
          backgroundColor: 'white',
          borderRadius: '15px',
          border: '2px solid #003366',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
        }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid #f0f8ff',
            borderTop: '4px solid #003366',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem'
          }}></div>
          <h2 style={{ color: '#003366', marginBottom: '1rem' }}>Loading Recipe...</h2>
          <p style={{ color: '#666' }}>Fetching delicious details 🍳</p>
        </div>
      </div>
    );
  }

  if (error) {
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
          background: 'white',
          border: '2px solid #dc3545',
          borderRadius: '15px',
          padding: '3rem',
          textAlign: 'center',
          maxWidth: '500px',
          boxShadow: '0 4px 12px rgba(220, 53, 69, 0.1)'
        }}>
          <h2 style={{ color: '#dc3545', marginBottom: '1rem' }}>😕 Recipe Not Found</h2>
          <p style={{ color: '#666', marginBottom: '2rem' }}>{error}</p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              onClick={() => navigate('/recipes')}
              style={{
                padding: '12px 24px',
                backgroundColor: '#003366',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              ← Back to Recipes
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '12px 24px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              🔄 Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // If in edit mode, render the RecipeForm component
  if (editMode) {
    return (
      <div style={{ padding: '2rem', backgroundColor: '#f0f8ff', minHeight: 'calc(100vh - 80px)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <button
            onClick={() => setEditMode(false)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f0f8ff',
              color: '#003366',
              border: '2px solid #003366',
              borderRadius: '8px',
              cursor: 'pointer',
              marginBottom: '2rem',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            ← Cancel & Return to Recipe
          </button>

          <RecipeForm
            editMode={true}
            existingRecipe={recipe}
            onSubmitSuccess={handleEditSuccess}
          />
        </div>
      </div>
    );
  }

  // Styles
  const containerStyle = {
    padding: '2rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)'
  };

  const backButtonStyle = {
    padding: '8px 16px',
    backgroundColor: '#f0f8ff',
    color: '#003366',
    border: '2px solid #003366',
    borderRadius: '8px',
    cursor: 'pointer',
    marginBottom: '2rem',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.3s ease'
  };

  const headerContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    marginBottom: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    textAlign: 'center'
  };

  const titleStyle = {
    color: '#003366',
    fontSize: '2.5rem',
    marginBottom: '1rem',
    lineHeight: '1.2'
  };

  const badgeContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
    marginBottom: '1.5rem'
  };

  const genreBadgeStyle = {
    backgroundColor: getGenreColor(recipe?.genre),
    color: 'white',
    padding: '8px 16px',
    borderRadius: '20px',
    fontSize: '1rem',
    fontWeight: '500'
  };

  const dietaryBadgeStyle = {
    backgroundColor: '#28a745', // Green for dietary restrictions
    color: 'white',
    padding: '6px 12px',
    borderRadius: '15px',
    fontSize: '0.9rem',
    fontWeight: '500',
    margin: '0 4px'
  };

  const servingBadgeStyle = {
    backgroundColor: '#003366',
    color: 'white',
    padding: '8px 16px',
    borderRadius: '20px',
    fontSize: '1rem'
  };

  const metaStyle = {
    display: 'flex',
    justifyContent: 'center',
    gap: '2rem',
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '1.5rem'
  };

  const contentGridStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '2rem',
    marginBottom: '2rem'
  };

  const sectionStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
  };

  const sectionHeaderStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
    paddingBottom: '0.5rem',
    borderBottom: '2px solid #f0f8ff'
  };

  const sectionTitleStyle = {
    color: '#003366',
    fontSize: '1.5rem',
    margin: 0
  };

  const toggleButtonStyle = {
    background: 'none',
    border: 'none',
    color: '#003366',
    cursor: 'pointer',
    fontSize: '1.2rem',
    padding: '4px'
  };

  return (
    <div style={containerStyle}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Back Button */}
        <button
          onClick={() => navigate('/recipes')}
          style={backButtonStyle}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = '#003366';
            e.target.style.color = 'white';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = '#f0f8ff';
            e.target.style.color = '#003366';
          }}
        >
          ← Back to Recipes
        </button>

        {/* Recipe Header */}
        <div style={headerContainerStyle}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '1rem'
          }}>
            <h1 style={titleStyle}>{recipe.recipe_name}</h1>
            <FavoriteButton
              recipeId={recipe.id}
              isFavorited={favoriteStatus}
              onToggle={handleFavoriteToggle}
            />
          </div>

          <div style={badgeContainerStyle}>
            <div style={genreBadgeStyle}>
              {getGenreEmoji(recipe.genre)} {formatGenreName(recipe.genre)}
            </div>

            {/* Dietary Restrictions Badges */}
            {recipe.dietary_restrictions && recipe.dietary_restrictions.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>
                {recipe.dietary_restrictions.map(restriction => (
                  <div key={restriction} style={dietaryBadgeStyle}>
                    {formatDietaryRestrictionName(restriction)}
                  </div>
                ))}
              </div>
            )}

            <div style={servingBadgeStyle}>
              👥 Serves {Math.round(recipe.serving_size * servingMultiplier)}
            </div>
          </div>

          <div style={metaStyle}>
            <span>👨‍🍳 Created by {recipe.created_by}</span>
            <span>📅 {new Date(recipe.created_at).toLocaleDateString()}</span>
            <span>🕒 {new Date(recipe.created_at).toLocaleTimeString()}</span>
          </div>

          {/* Time Information */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1.5rem',
            margin: '1rem 0',
            flexWrap: 'wrap'
          }}>
            <div style={{
              background: '#f0f8ff',
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '0.9rem', color: '#666' }}>Prep Time</span>
              <span style={{ fontWeight: '500', color: '#003366' }}>
                {recipe.prep_time !== undefined && recipe.prep_time !== null ? recipe.prep_time : 0} mins
              </span>
            </div>

            <div style={{
              background: '#f0f8ff',
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '0.9rem', color: '#666' }}>Cook Time</span>
              <span style={{ fontWeight: '500', color: '#003366' }}>
                {recipe.cook_time !== undefined && recipe.cook_time !== null ? recipe.cook_time : 0} mins
              </span>
            </div>

            <div style={{
              background: '#e6f0ff', // Slightly darker background
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              border: '1px solid #cce0ff'
            }}>
              <span style={{ fontSize: '0.9rem', color: '#666' }}>Total Time</span>
              <span style={{ fontWeight: '600', color: '#002855' }}>
                {(recipe.prep_time || 0) + (recipe.cook_time || 0)} mins
              </span>
            </div>
          </div>

          {/* Serving Size Adjuster */}
          <div style={{
            background: '#f0f8ff',
            padding: '1rem',
            borderRadius: '10px',
            margin: '1rem 0',
            border: '1px solid #003366'
          }}>
            <h4 style={{ color: '#003366', marginBottom: '0.5rem' }}>🍽️ Adjust Serving Size</h4>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', alignItems: 'center' }}>
              {[0.5, 1, 1.5, 2, 3, 4].map(multiplier => (
                <button
                  key={multiplier}
                  onClick={() => adjustServings(multiplier)}
                  style={{
                    padding: '6px 12px',
                    border: '2px solid #003366',
                    borderRadius: '8px',
                    backgroundColor: servingMultiplier === multiplier ? '#003366' : 'white',
                    color: servingMultiplier === multiplier ? 'white' : '#003366',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  {multiplier}x
                </button>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: '#666', margin: '0.5rem 0 0 0' }}>
              Original recipe serves {recipe.serving_size} • Currently showing {Math.round(recipe.serving_size * servingMultiplier)} servings
            </p>
          </div>

          {/* Action Buttons */}
          {canEditOrDelete() && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '1rem',
              marginTop: '1.5rem'
            }}>
              <button
                onClick={handleEnableEdit}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                ✏️ Edit Recipe
              </button>

              <button
                onClick={handleDelete}
                disabled={deleting}
                style={{
                  padding: '10px 20px',
                  backgroundColor: deleting ? '#ccc' : '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                {deleting ? 'Deleting...' : '🗑️ Delete Recipe'}
              </button>
            </div>
          )}
        </div>

        {/* Recipe Content */}
        <div style={contentGridStyle}>
          {/* Ingredients */}
          <div style={sectionStyle}>
            <div style={sectionHeaderStyle}>
              <h2 style={sectionTitleStyle}>
                🛒 Ingredients ({recipe.ingredients.length})
              </h2>
              <button
                style={toggleButtonStyle}
                onClick={() => setShowIngredients(!showIngredients)}
              >
                {showIngredients ? '▼' : '▶'}
              </button>
            </div>

            {showIngredients && (
              <div>
                <div style={{
                  marginBottom: '1rem',
                  padding: '0.5rem',
                  background: '#f0f8ff',
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  color: '#666'
                }}>
                  💡 Click ingredients to check them off as you gather them!
                </div>

                {recipe.ingredients.map((ingredient, index) => (
                  <div
                    key={index}
                    onClick={() => toggleIngredient(index)}
                    style={{
                      padding: '0.75rem',
                      borderBottom: index < recipe.ingredients.length - 1 ? '1px solid #f0f8ff' : 'none',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      backgroundColor: checkedIngredients.has(index) ? '#f0f8ff' : 'transparent',
                      borderRadius: '6px',
                      margin: '2px 0',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      <span style={{
                        fontSize: '1.2rem',
                        color: checkedIngredients.has(index) ? '#28a745' : '#ccc'
                      }}>
                        {checkedIngredients.has(index) ? '✅' : '⭕'}
                      </span>
                      <span style={{
                        fontWeight: '500',
                        color: '#003366',
                        textDecoration: checkedIngredients.has(index) ? 'line-through' : 'none'
                      }}>
                        {ingredient.name}
                      </span>
                    </div>
                    <span style={{
                      color: '#666',
                      fontSize: '0.9rem',
                      fontWeight: '500'
                    }}>
                      {calculateQuantity(ingredient.quantity)} {ingredient.unit}
                    </span>
                  </div>
                ))}

                <div style={{
                  marginTop: '1rem',
                  padding: '0.5rem',
                  background: '#e8f5e8',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                  color: '#155724',
                  textAlign: 'center'
                }}>
                  {checkedIngredients.size} of {recipe.ingredients.length} ingredients gathered
                </div>
              </div>
            )}
          </div>

          {/* Instructions */}
          <div style={sectionStyle}>
            <div style={sectionHeaderStyle}>
              <h2 style={sectionTitleStyle}>
                📝 Instructions ({recipe.instructions.length} steps)
              </h2>
              <button
                style={toggleButtonStyle}
                onClick={() => setShowInstructions(!showInstructions)}
              >
                {showInstructions ? '▼' : '▶'}
              </button>
            </div>

            {showInstructions && (
              <div>
                <div style={{
                  marginBottom: '1rem',
                  padding: '0.5rem',
                  background: '#f0f8ff',
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  color: '#666'
                }}>
                  💡 Click steps to mark them as completed!
                </div>

                {recipe.instructions.map((instruction, index) => (
                  <div
                    key={index}
                    onClick={() => toggleStep(index)}
                    style={{
                      marginBottom: '1.5rem',
                      padding: '1rem',
                      background: completedSteps.has(index) ? '#e8f5e8' : '#f0f8ff',
                      borderRadius: '10px',
                      borderLeft: `4px solid ${completedSteps.has(index) ? '#28a745' : '#003366'}`,
                      cursor: 'pointer',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '1rem'
                    }}>
                      <span style={{
                        backgroundColor: completedSteps.has(index) ? '#28a745' : '#003366',
                        color: 'white',
                        borderRadius: '50%',
                        width: '28px',
                        height: '28px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '14px',
                        fontWeight: 'bold',
                        flexShrink: 0
                      }}>
                        {completedSteps.has(index) ? '✓' : index + 1}
                      </span>
                      <p style={{
                        margin: 0,
                        lineHeight: '1.5',
                        color: '#333',
                        textDecoration: completedSteps.has(index) ? 'line-through' : 'none'
                      }}>
                        {instruction}
                      </p>
                    </div>
                  </div>
                ))}

                <div style={{
                  marginTop: '1rem',
                  padding: '0.5rem',
                  background: '#e8f5e8',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                  color: '#155724',
                  textAlign: 'center'
                }}>
                  {completedSteps.size} of {recipe.instructions.length} steps completed
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Notes Section - Display if notes exist */}
        {recipe.notes && recipe.notes.length > 0 && recipe.notes[0] && (
          <div style={{
            background: 'white',
            border: '2px solid #6c757d',
            borderRadius: '15px',
            padding: '2rem',
            marginBottom: '2rem',
            boxShadow: '0 4px 12px rgba(108, 117, 125, 0.1)'
          }}>
            <h2 style={{
              color: '#6c757d',
              fontSize: '1.5rem',
              marginBottom: '1.5rem',
              borderBottom: '2px solid #f0f8ff',
              paddingBottom: '0.5rem'
            }}>
              📋 Recipe Notes
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {recipe.notes.map((note, index) => (
                <div
                  key={index}
                  style={{
                    padding: '1rem',
                    background: '#f8f9fa',
                    borderRadius: '10px',
                    borderLeft: '4px solid #6c757d'
                  }}
                >
                  <p style={{ margin: 0, lineHeight: '1.5' }}>{note}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ratings and Reviews Section */}
        <RatingsAndReviews
          recipeId={recipe.id}
          currentUserId={user?.id}
        />

        {/* Additional Recipe Actions */}
        <div style={{
          background: 'white',
          border: '2px solid #003366',
          borderRadius: '15px',
          padding: '2rem',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
          marginTop: '2rem'
        }}>
          <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
            🍳 Recipe Actions
          </h3>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            {completedSteps.size === recipe.instructions.length && checkedIngredients.size === recipe.ingredients.length
              ? "🎉 All ingredients gathered and steps completed! Enjoy your delicious creation!"
              : "Use the tools above to track your cooking progress!"
            }
          </p>

          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={() => {
                const url = window.location.href;
                navigator.clipboard.writeText(url);
                alert('Recipe link copied to clipboard! 📋');
              }}
              style={{
                padding: '12px 24px',
                backgroundColor: '#17a2b8',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '16px'
              }}
            >
              📤 Share Recipe
            </button>

            <button
              onClick={() => window.print()}
              style={{
                padding: '12px 24px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '16px'
              }}
            >
              🖨️ Print Recipe
            </button>
          </div>
        </div>
      </div>

      {/* Add CSS animation for loading spinner */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default RecipeDetail;
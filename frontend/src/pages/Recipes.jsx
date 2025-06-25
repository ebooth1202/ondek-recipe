import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RecipeCard from '../components/recipe/RecipeCard';
import { API_BASE_URL, API_ENDPOINTS, apiClient } from '../utils/api';

const Recipes = () => {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  // State management
  const [recipes, setRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState(new Set());

  // New dietary restriction filters
  const [activeFilters, setActiveFilters] = useState({
    glutenFree: false,
    dairyFree: false,
    eggFree: false
  });

  // Available genres (excluding dietary restrictions)
  const availableGenres = [
    { value: '', label: 'All Categories' },
    { value: 'breakfast', label: 'Breakfast' },
    { value: 'lunch', label: 'Lunch' },
    { value: 'dinner', label: 'Dinner' },
    { value: 'snack', label: 'Snack' },
    { value: 'dessert', label: 'Dessert' },
    { value: 'appetizer', label: 'Appetizer' }
  ];

  // Dietary restriction filter definitions
  const dietaryFilters = [
    { key: 'glutenFree', label: 'Gluten Free', value: 'gluten_free' },
    { key: 'dairyFree', label: 'Dairy Free', value: 'dairy_free' },
    { key: 'eggFree', label: 'Egg Free', value: 'egg_free' }
  ];

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Fetch recipes and favorites
  useEffect(() => {
    const fetchData = async () => {
      if (!isAuthenticated()) return;

      try {
        setLoading(true);

        // Fetch recipes and favorites in parallel
        const [recipesResponse, favoritesResponse] = await Promise.all([
          apiClient.get(API_ENDPOINTS.RECIPES),
          apiClient.get(API_ENDPOINTS.USER_FAVORITES)
        ]);

        const allRecipes = recipesResponse.data;
        const favoriteRecipes = favoritesResponse.data;

        // Create set of favorite recipe IDs for quick lookup
        const favoriteIds = new Set(favoriteRecipes.map(recipe => recipe.id));

        // Add is_favorited flag to recipes
        const recipesWithFavorites = allRecipes.map(recipe => ({
          ...recipe,
          is_favorited: favoriteIds.has(recipe.id)
        }));

        setRecipes(recipesWithFavorites);
        setFavoriteRecipeIds(favoriteIds);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to load recipes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated]);

  // Filter and search recipes
  useEffect(() => {
    let filtered = [...recipes];

    // Apply search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(recipe =>
        recipe.recipe_name.toLowerCase().includes(searchLower) ||
        recipe.description?.toLowerCase().includes(searchLower) ||
        recipe.ingredients.some(ing =>
          ing.name.toLowerCase().includes(searchLower)
        )
      );
    }

    // Apply genre filter
    if (selectedGenre) {
      filtered = filtered.filter(recipe => recipe.genre === selectedGenre);
    }

    // Apply dietary restriction filters
    Object.entries(activeFilters).forEach(([filterKey, isActive]) => {
      if (isActive) {
        const filterValue = dietaryFilters.find(f => f.key === filterKey)?.value;
        if (filterValue) {
          filtered = filtered.filter(recipe =>
            recipe.dietary_restrictions &&
            recipe.dietary_restrictions.includes(filterValue)
          );
        }
      }
    });

    // Apply favorites filter
    if (showFavoritesOnly) {
      filtered = filtered.filter(recipe => favoriteRecipeIds.has(recipe.id));
    }

    // Sort recipes alphabetically
    filtered.sort((a, b) => a.recipe_name.localeCompare(b.recipe_name));

    setFilteredRecipes(filtered);
  }, [recipes, searchTerm, selectedGenre, activeFilters, showFavoritesOnly, favoriteRecipeIds]);

  // Handle favorite toggle
  const handleFavoriteToggle = (recipeId, isFavorited) => {
    const newFavoriteIds = new Set(favoriteRecipeIds);

    if (isFavorited) {
      newFavoriteIds.add(recipeId);
    } else {
      newFavoriteIds.delete(recipeId);
    }

    setFavoriteRecipeIds(newFavoriteIds);

    // Update the recipe in the recipes array
    setRecipes(prevRecipes =>
      prevRecipes.map(recipe =>
        recipe.id === recipeId
          ? { ...recipe, is_favorited: isFavorited }
          : recipe
      )
    );
  };

  // Handle dietary filter toggle
  const handleDietaryFilterToggle = (filterKey) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterKey]: !prev[filterKey]
    }));
  };

  // Clear all filters
  const clearAllFilters = () => {
    setSearchTerm('');
    setSelectedGenre('');
    setActiveFilters({
      glutenFree: false,
      dairyFree: false,
      eggFree: false
    });
    setShowFavoritesOnly(false);
  };

  // Group recipes by first letter (only when no filters are applied)
  const shouldShowLetterGroups = !searchTerm.trim() &&
                                !showFavoritesOnly &&
                                !selectedGenre &&
                                !Object.values(activeFilters).some(Boolean);

  const groupedRecipes = shouldShowLetterGroups ?
    filteredRecipes.reduce((groups, recipe) => {
      const firstLetter = recipe.recipe_name.charAt(0).toUpperCase();
      if (!groups[firstLetter]) {
        groups[firstLetter] = [];
      }
      groups[firstLetter].push(recipe);
      return groups;
    }, {}) : {};

  // Styles
  const containerStyle = {
    padding: '2rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)'
  };

  const headerStyle = {
    textAlign: 'center',
    color: '#003366',
    fontSize: '2.5rem',
    marginBottom: '2rem'
  };

  const controlsContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.5rem',
    marginBottom: '2rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
  };

  const searchInputStyle = {
    padding: '12px 16px',
    border: '2px solid #003366',
    borderRadius: '10px',
    fontSize: '16px',
    backgroundColor: 'white',
    flex: '2'
  };

  const searchRowStyle = {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    marginBottom: '1rem'
  };

  const filtersRowStyle = {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginBottom: '1rem'
  };

  const genreSelectStyle = {
    padding: '8px 12px',
    border: '2px solid #003366',
    borderRadius: '8px',
    fontSize: '14px',
    backgroundColor: 'white',
    flex: '1'
  };

  const buttonStyle = {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.3s ease'
  };

  const dietaryFilterButtonStyle = (isActive) => ({
    ...buttonStyle,
    backgroundColor: isActive ? '#0066cc' : '#f0f8ff',
    color: isActive ? 'white' : '#0066cc',
    border: `2px solid #0066cc`
  });

  const favoritesButtonStyle = {
    ...buttonStyle,
    backgroundColor: showFavoritesOnly ? '#0066cc' : '#f0f8ff',
    color: showFavoritesOnly ? 'white' : '#0066cc',
    border: '2px solid #0066cc'
  };

  const refreshButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#28a745',
    color: 'white',
    border: '2px solid #28a745'
  };

  const letterHeaderStyle = {
    backgroundColor: '#003366',
    color: 'white',
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    fontSize: '1.2rem',
    fontWeight: 'bold',
    textAlign: 'center',
    margin: '2rem 0 1rem 0'
  };

  const recipesGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '2rem',
    marginTop: '2rem'
  };

  // Render guard
  if (!isAuthenticated()) {
    return null;
  }

  if (loading) {
    return (
      <div style={containerStyle}>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '50vh'
        }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid #f0f8ff',
            borderTop: '4px solid #003366',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={containerStyle}>
        <div style={{
          background: 'white',
          border: '2px solid #dc3545',
          borderRadius: '15px',
          padding: '2rem',
          textAlign: 'center',
          maxWidth: '500px',
          margin: '0 auto'
        }}>
          <h2 style={{ color: '#dc3545', marginBottom: '1rem' }}>😕 Error Loading Recipes</h2>
          <p style={{ color: '#666', marginBottom: '1rem' }}>{error}</p>
          <button
            onClick={() => window.location.reload()}
            style={refreshButtonStyle}
          >
            🔄 Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={headerStyle}>🍳 Recipe Collection</h1>

        {/* Search and Filter Controls */}
        <div style={controlsContainerStyle}>
          {/* Search and Genre Row */}
          <div style={searchRowStyle}>
            <input
              type="text"
              placeholder="🔍 Search recipes, ingredients, or descriptions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={searchInputStyle}
            />
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              style={genreSelectStyle}
            >
              {availableGenres.map(genre => (
                <option key={genre.value} value={genre.value}>
                  {genre.label}
                </option>
              ))}
            </select>
          </div>

          {/* Filter Buttons Row */}
          <div style={filtersRowStyle}>
            {/* Dietary Restriction Filter Buttons */}
            {dietaryFilters.map(filter => (
              <button
                key={filter.key}
                onClick={() => handleDietaryFilterToggle(filter.key)}
                style={dietaryFilterButtonStyle(activeFilters[filter.key])}
                onMouseEnter={(e) => {
                  if (!activeFilters[filter.key]) {
                    e.target.style.backgroundColor = '#0066cc';
                    e.target.style.color = 'white';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!activeFilters[filter.key]) {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.color = '#0066cc';
                  }
                }}
              >
                {filter.label}
              </button>
            ))}

            <button
              onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
              style={favoritesButtonStyle}
              onMouseEnter={(e) => {
                if (!showFavoritesOnly) {
                  e.target.style.backgroundColor = '#0066cc';
                  e.target.style.color = 'white';
                }
              }}
              onMouseLeave={(e) => {
                if (!showFavoritesOnly) {
                  e.target.style.backgroundColor = '#f0f8ff';
                  e.target.style.color = '#0066cc';
                }
              }}
            >
              ⭐ {showFavoritesOnly ? 'All Recipes' : 'Favorites'}
            </button>

            <button
              onClick={clearAllFilters}
              style={refreshButtonStyle}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#218838';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#28a745';
              }}
            >
              🔄 Clear Filters
            </button>
          </div>

          {/* Active Filters Summary */}
          {(searchTerm || selectedGenre || Object.values(activeFilters).some(Boolean) || showFavoritesOnly) && (
            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: '#e6f0ff',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#003366'
            }}>
              <strong>Active filters:</strong>{' '}
              {searchTerm && <span>Search: "{searchTerm}" • </span>}
              {selectedGenre && <span>Category: {availableGenres.find(g => g.value === selectedGenre)?.label} • </span>}
              {Object.entries(activeFilters).map(([key, active]) =>
                active && <span key={key}>{dietaryFilters.find(f => f.key === key)?.label} • </span>
              )}
              {showFavoritesOnly && <span>Favorites Only • </span>}
              <strong>Showing {filteredRecipes.length} of {recipes.length} recipes</strong>
            </div>
          )}
        </div>

        {/* Results */}
        {filteredRecipes.length === 0 ? (
          <div style={{
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            padding: '3rem',
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
          }}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
              {recipes.length === 0 ? '📝 No Recipes Yet' : '🔍 No Recipes Found'}
            </h3>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
              {recipes.length === 0
                ? 'Start building your recipe collection by adding your first recipe!'
                : 'Try adjusting your search terms or filters to find more recipes.'
              }
            </p>
            <button
              onClick={() => navigate('/add-recipe')}
              style={{
                ...buttonStyle,
                backgroundColor: '#003366',
                color: 'white',
                fontSize: '16px',
                padding: '12px 24px'
              }}
            >
              ➕ Add Your First Recipe
            </button>
          </div>
        ) : shouldShowLetterGroups ? (
          // Grouped by letter (default view)
          Object.keys(groupedRecipes).sort().map(letter => (
            <div key={letter}>
              <div style={letterHeaderStyle}>{letter}</div>
              <div style={recipesGridStyle}>
                {groupedRecipes[letter].map(recipe => (
                  <RecipeCard
                    key={recipe.id}
                    recipe={recipe}
                    onFavoriteToggle={handleFavoriteToggle}
                  />
                ))}
              </div>
            </div>
          ))
        ) : (
          // Alphabetical list (search results or favorites)
          <div style={recipesGridStyle}>
            {filteredRecipes.map(recipe => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onFavoriteToggle={handleFavoriteToggle}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Recipes;
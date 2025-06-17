import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RecipeCard from '../components/recipe/RecipeCard';
import axios from 'axios';

const Recipes = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // State management
  const [recipes, setRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [availableGenres, setAvailableGenres] = useState([]);

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Fetch recipes and genres from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log('Fetching recipes from API...');

        const [recipesRes, genresRes] = await Promise.all([
          axios.get('http://127.0.0.1:8000/recipes'),
          axios.get('http://127.0.0.1:8000/genres')
        ]);

        console.log('Recipes received:', recipesRes.data);
        console.log('Genres received:', genresRes.data);

        setRecipes(recipesRes.data);
        setFilteredRecipes(recipesRes.data);
        setAvailableGenres(genresRes.data.genres);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to load recipes. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated()) {
      fetchData();
    }
  }, [isAuthenticated]);

  // Filter recipes based on search and genre
  useEffect(() => {
    let filtered = recipes;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(recipe =>
        recipe.recipe_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        recipe.ingredients.some(ing =>
          ing.name.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Filter by genre
    if (selectedGenre) {
      filtered = filtered.filter(recipe => recipe.genre === selectedGenre);
    }

    setFilteredRecipes(filtered);
  }, [recipes, searchTerm, selectedGenre]);

  // Group recipes alphabetically
  const groupedRecipes = filteredRecipes.reduce((acc, recipe) => {
    const firstLetter = recipe.recipe_name.charAt(0).toUpperCase();
    if (!acc[firstLetter]) {
      acc[firstLetter] = [];
    }
    acc[firstLetter].push(recipe);
    return acc;
  }, {});

  const alphabeticalGroups = Object.keys(groupedRecipes).sort();

  // Handle recipe refresh (when coming back from add recipe)
  const refreshRecipes = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/recipes');
      setRecipes(response.data);
      setFilteredRecipes(response.data);
    } catch (error) {
      console.error('Error refreshing recipes:', error);
    }
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
          padding: '2rem',
          backgroundColor: 'white',
          borderRadius: '15px',
          border: '2px solid #003366',
          textAlign: 'center',
          boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
        }}>
          <h2 style={{ color: '#003366', marginBottom: '1rem' }}>
            🍳 Loading Recipes...
          </h2>
          <p style={{ color: '#666' }}>
            Fetching your delicious recipes from the kitchen!
          </p>
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

  const headerStyle = {
    textAlign: 'center',
    marginBottom: '2rem'
  };

  const titleStyle = {
    color: '#003366',
    fontSize: '2.5rem',
    marginBottom: '1rem'
  };

  const subtitleStyle = {
    fontSize: '1.2rem',
    color: '#666'
  };

  const searchContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.5rem',
    marginBottom: '2rem',
    boxShadow: '0 2px 8px rgba(0, 51, 102, 0.1)'
  };

  const searchGridStyle = {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr auto',
    gap: '1rem',
    alignItems: 'center'
  };

  const inputStyle = {
    width: '100%',
    padding: '12px',
    border: '2px solid #003366',
    borderRadius: '10px',
    fontSize: '16px',
    backgroundColor: 'white'
  };

  const buttonStyle = {
    padding: '12px 20px',
    backgroundColor: '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '16px',
    fontWeight: '500',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'all 0.3s ease'
  };

  const recipeGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '1.5rem'
  };

  const alphabetHeaderStyle = {
    background: '#003366',
    color: 'white',
    padding: '1rem',
    borderRadius: '10px',
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    textAlign: 'center'
  };

  const emptyStateStyle = {
    textAlign: 'center',
    padding: '3rem',
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
  };

  return (
    <div style={containerStyle}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={headerStyle}>
          <h1 style={titleStyle}>🍳 Recipe Collection</h1>
          <p style={subtitleStyle}>
            {filteredRecipes.length} recipe{filteredRecipes.length !== 1 ? 's' : ''} found
            {recipes.length > 0 && (
              <span> • Total: {recipes.length}</span>
            )}
          </p>
        </div>

        {/* Search and Filter */}
        <div style={searchContainerStyle}>
          <div style={searchGridStyle}>
            <div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={inputStyle}
                placeholder="🔍 Search recipes or ingredients..."
              />
            </div>

            <div>
              <select
                value={selectedGenre}
                onChange={(e) => setSelectedGenre(e.target.value)}
                style={inputStyle}
              >
                <option value="">All Categories</option>
                {availableGenres.map(genre => (
                  <option key={genre} value={genre}>
                    {genre.charAt(0).toUpperCase() + genre.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => navigate('/add-recipe')}
              style={buttonStyle}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#0066cc';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#003366';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              ➕ Add Recipe
            </button>
          </div>

          {/* Quick Actions */}
          <div style={{
            display: 'flex',
            gap: '1rem',
            marginTop: '1rem',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={refreshRecipes}
              style={{
                padding: '8px 16px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              🔄 Refresh
            </button>

            {(searchTerm || selectedGenre) && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSelectedGenre('');
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                ✕ Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '2rem',
            border: '1px solid #f5c6cb',
            textAlign: 'center'
          }}>
            {error}
            <button
              onClick={refreshRecipes}
              style={{
                marginLeft: '1rem',
                padding: '4px 8px',
                backgroundColor: '#721c24',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {filteredRecipes.length === 0 && !loading && !error && (
          <div style={emptyStateStyle}>
            <h2 style={{ color: '#003366', marginBottom: '1rem' }}>
              {searchTerm || selectedGenre ? '🔍 No recipes found' : '📝 No recipes yet'}
            </h2>
            <p style={{ color: '#666', marginBottom: '2rem' }}>
              {searchTerm || selectedGenre
                ? 'Try adjusting your search or filter criteria'
                : 'Start building your recipe collection by adding your first recipe!'
              }
            </p>

            <div style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={() => navigate('/add-recipe')}
                style={buttonStyle}
              >
                ➕ Add Your First Recipe
              </button>

              {(searchTerm || selectedGenre) && (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedGenre('');
                  }}
                  style={{
                    ...buttonStyle,
                    backgroundColor: '#6c757d'
                  }}
                >
                  📋 Show All Recipes
                </button>
              )}
            </div>
          </div>
        )}

        {/* Recipe Groups */}
        {alphabeticalGroups.map(letter => (
          <div key={letter} style={{ marginBottom: '3rem' }}>
            <div style={alphabetHeaderStyle}>{letter}</div>

            <div style={recipeGridStyle}>
              {groupedRecipes[letter].map(recipe => (
                <RecipeCard key={recipe.id} recipe={recipe} />
              ))}
            </div>
          </div>
        ))}

        {/* Recipe Count Summary */}
        {filteredRecipes.length > 0 && (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            background: 'white',
            border: '2px solid #003366',
            borderRadius: '15px',
            marginTop: '2rem',
            boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
          }}>
            <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
              🎉 Recipe Collection Summary
            </h3>
            <p style={{ color: '#666' }}>
              You have <strong>{recipes.length}</strong> recipe{recipes.length !== 1 ? 's' : ''} in your collection!
              {searchTerm || selectedGenre ? (
                <span> Showing <strong>{filteredRecipes.length}</strong> filtered result{filteredRecipes.length !== 1 ? 's' : ''}.</span>
              ) : null}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Recipes;

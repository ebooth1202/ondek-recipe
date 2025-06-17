// File: frontend/src/components/FavoriteButton.js
import React, { useState } from 'react';
import { Heart } from 'lucide-react';

const FavoriteButton = ({ recipeId, isFavorited: initialFavorited = false, onToggle }) => {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);

  const handleToggle = async () => {
    setIsLoading(true);
    try {
      const method = isFavorited ? 'DELETE' : 'POST';
      const token = localStorage.getItem('token');

      const response = await fetch(`http://localhost:8000/recipes/${recipeId}/favorite`, {
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

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading}
      className={`p-2 rounded-full transition-all ${
        isFavorited 
          ? 'text-red-500 bg-red-50 hover:bg-red-100' 
          : 'text-gray-400 bg-gray-50 hover:bg-gray-100 hover:text-red-400'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      title={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        className={`w-5 h-5 ${isFavorited ? 'fill-current' : ''}`}
      />
    </button>
  );
};

export default FavoriteButton;
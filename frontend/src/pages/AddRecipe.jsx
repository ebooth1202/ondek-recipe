import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RecipeForm from '../components/recipe/RecipeForm';
import axios from 'axios';

const AddRecipe = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [loading, setLoading] = useState(false);

  // Check if we're duplicating a recipe
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const duplicating = searchParams.get('duplicate') === 'true';
    setIsDuplicating(duplicating);

    if (duplicating) {
      // Log to help debugging
      const duplicateRecipe = sessionStorage.getItem('duplicateRecipe');
      console.log('Add Recipe page found duplicate param. Recipe data in storage:',
        duplicateRecipe ? 'Present' : 'Not found');
    }
  }, [location.search]);

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Handle successful form submission
  const handleSubmitSuccess = (data) => {
    // You can add any post-submission logic here if needed
    console.log('Recipe created successfully:', data);
  };

  return (
    <div style={{
      padding: '2rem',
      backgroundColor: '#f0f8ff',
      minHeight: 'calc(100vh - 80px)'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {loading ? (
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
        ) : (
          <RecipeForm
            editMode={false}
            onSubmitSuccess={handleSubmitSuccess}
          />
        )}
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

export default AddRecipe;
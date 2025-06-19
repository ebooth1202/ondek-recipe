import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import StarRating from './StarRating';
import ReviewItem from './ReviewItem';
import RatingForm from './RatingForm';

const RatingsAndReviews = ({ recipeId, currentUserId }) => {
  const { apiBaseUrl } = useAuth();
  const [ratings, setRatings] = useState([]);
  const [summary, setSummary] = useState({
    average_rating: 0,
    total_ratings: 0,
    rating_breakdown: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userRating, setUserRating] = useState(null);
  const [showRatingForm, setShowRatingForm] = useState(false);
  const [editingRating, setEditingRating] = useState(null);

  // Fetch ratings and summary on component mount
  useEffect(() => {
    if (recipeId) {
      fetchRatings();
      fetchSummary();
    }
  }, [recipeId]);

  const fetchRatings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://127.0.0.1:8000/recipes/${recipeId}/ratings`);
      setRatings(response.data);

      // Check if current user has already rated
      const currentUserRating = response.data.find(rating => rating.user_id === currentUserId);
      if (currentUserRating) {
        setUserRating(currentUserRating);
      }
    } catch (err) {
      console.error('Error fetching ratings:', err);
      setError('Failed to load ratings');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`http://127.0.0.1:8000/recipes/${recipeId}/ratings/summary`);
      setSummary(response.data);
    } catch (err) {
      console.error('Error fetching rating summary:', err);
    }
  };

  const handleRatingSubmit = (newRating) => {
    // Update the ratings list
    if (editingRating) {
      // Replace the edited rating
      setRatings(ratings.map(r =>
        r.id === newRating.id ? newRating : r
      ));
      setUserRating(newRating);
    } else {
      // Add the new rating
      setRatings([newRating, ...ratings]);
      setUserRating(newRating);
    }

    // Refresh summary
    fetchSummary();

    // Close the form
    setShowRatingForm(false);
    setEditingRating(null);
  };

  const handleEditRating = (rating) => {
    setEditingRating(rating);
    setShowRatingForm(true);
  };

  const handleDeleteRating = async (rating) => {
    if (!window.confirm("Are you sure you want to delete this review?")) {
      return;
    }

    try {
      await axios.delete(`http://127.0.0.1:8000/recipes/${recipeId}/ratings/${rating.id}`);

      // Update local state
      setRatings(ratings.filter(r => r.id !== rating.id));
      if (userRating && userRating.id === rating.id) {
        setUserRating(null);
      }

      // Refresh summary
      fetchSummary();
    } catch (error) {
      console.error('Error deleting rating:', error);
      alert('Failed to delete rating. Please try again.');
    }
  };

  // Render the rating breakdown bars
  const RatingBreakdown = () => (
    <div style={{ width: '100%', maxWidth: '300px' }}>
      {[5, 4, 3, 2, 1].map((num) => (
        <div key={num} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '4px'
        }}>
          <span style={{
            width: '16px',
            fontSize: '14px',
            color: '#666',
            textAlign: 'right'
          }}>
            {num}
          </span>
          <div style={{
            flex: 1,
            height: '8px',
            backgroundColor: '#e0e0e0',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div
              style={{
                height: '100%',
                backgroundColor: '#ffc107',
                borderRadius: '4px',
                width: `${summary.total_ratings ? (summary.rating_breakdown[num] / summary.total_ratings) * 100 : 0}%`,
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <span style={{
            width: '24px',
            fontSize: '12px',
            color: '#999',
            textAlign: 'right'
          }}>
            {summary.rating_breakdown[num] || 0}
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <div style={{
      backgroundColor: 'white',
      border: '2px solid #003366',
      borderRadius: '15px',
      padding: '2rem',
      marginBottom: '2rem',
      boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)'
    }}>
      <h2 style={{
        color: '#003366',
        fontSize: '2rem',
        marginBottom: '2rem',
        textAlign: 'center'
      }}>
        ⭐ Ratings & Reviews
      </h2>

      {/* Rating Summary */}
      <div style={{
        backgroundColor: '#f0f8ff',
        padding: '2rem',
        borderRadius: '15px',
        marginBottom: '2rem',
        border: '1px solid #003366'
      }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '2rem'
        }}>
          {/* Average Rating Display */}
          <div style={{
            textAlign: 'center',
            minWidth: '200px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'center',
              marginBottom: '8px'
            }}>
              <span style={{
                fontSize: '3rem',
                fontWeight: 'bold',
                color: '#003366'
              }}>
                {summary.average_rating ? summary.average_rating.toFixed(1) : "0.0"}
              </span>
              <span style={{
                fontSize: '1.2rem',
                color: '#666',
                marginLeft: '4px'
              }}>
                / 5
              </span>
            </div>
            <div style={{ marginBottom: '8px' }}>
              <StarRating rating={summary.average_rating} size="lg" />
            </div>
            <p style={{
              fontSize: '14px',
              color: '#666',
              margin: 0
            }}>
              Based on {summary.total_ratings} {summary.total_ratings === 1 ? 'rating' : 'ratings'}
            </p>
          </div>

          {/* Rating Breakdown */}
          <div style={{ flex: 1, maxWidth: '400px' }}>
            <RatingBreakdown />
          </div>
        </div>
      </div>

      {/* Add/Edit Rating Form */}
      {showRatingForm ? (
        <div style={{ marginBottom: '2rem' }}>
          <RatingForm
            recipeId={recipeId}
            existingRating={editingRating}
            onSubmit={handleRatingSubmit}
            onCancel={() => {
              setShowRatingForm(false);
              setEditingRating(null);
            }}
          />
        </div>
      ) : (
        <div style={{
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          <button
            onClick={() => setShowRatingForm(true)}
            style={{
              backgroundColor: '#003366',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#0066cc';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#003366';
            }}
          >
            {userRating ? '✏️ Edit Your Rating' : '⭐ Add Your Rating'}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {/* Reviews List */}
      <div style={{ marginTop: '2rem' }}>
        <h3 style={{
          color: '#003366',
          fontSize: '1.5rem',
          marginBottom: '1.5rem',
          borderBottom: '2px solid #f0f8ff',
          paddingBottom: '0.5rem'
        }}>
          💬 User Reviews ({ratings.length})
        </h3>

        {loading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            padding: '3rem'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid #f0f8ff',
              borderTop: '4px solid #003366',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
          </div>
        ) : ratings.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '3rem',
            backgroundColor: '#f0f8ff',
            borderRadius: '15px',
            border: '1px solid #003366'
          }}>
            <p style={{
              color: '#666',
              fontSize: '1.1rem',
              margin: 0
            }}>
              No reviews yet. Be the first to review this recipe! 🌟
            </p>
          </div>
        ) : (
          <div style={{
            maxHeight: '500px',
            overflowY: 'auto',
            padding: '0 8px'
          }}>
            {ratings.map((rating) => (
              <ReviewItem
                key={rating.id}
                review={rating}
                currentUserId={currentUserId}
                onEdit={handleEditRating}
                onDelete={handleDeleteRating}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add CSS animation for loading spinner */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default RatingsAndReviews;
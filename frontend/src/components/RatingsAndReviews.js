import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RatingsAndReviews = ({ recipeId, currentUserId }) => {
  const [ratings, setRatings] = useState([]);
  const [summary, setSummary] = useState({ average_rating: 0, total_ratings: 0, rating_breakdown: {} });
  const [userRating, setUserRating] = useState(0);
  const [userReview, setUserReview] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [userHasRated, setUserHasRated] = useState(false);
  const [userRatingId, setUserRatingId] = useState(null);

  // Fetch ratings and summary on component mount
  useEffect(() => {
    if (recipeId) {
      fetchRatings();
      fetchSummary();
    }
  }, [recipeId]);

  const fetchRatings = async () => {
    try {
      const response = await axios.get(`http://127.0.0.1:8000/recipes/${recipeId}/ratings`);
      setRatings(response.data);

      // Check if current user has already rated
      const userRating = response.data.find(rating => rating.user_id === currentUserId);
      if (userRating) {
        setUserHasRated(true);
        setUserRating(userRating.rating);
        setUserReview(userRating.review || '');
        setUserRatingId(userRating.id);
      }
    } catch (err) {
      console.error('Error fetching ratings:', err);
      setError('Failed to load ratings');
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

  const submitRating = async () => {
    if (userRating === 0) {
      setError('Please select a star rating');
      return;
    }

    setIsSubmitting(true);
    setError('');
    setSuccess('');

    try {
      let response;

      if (userHasRated) {
        // Update existing rating
        response = await axios.put(`http://127.0.0.1:8000/recipes/${recipeId}/ratings/${userRatingId}`, {
          rating: userRating,
          review: userReview
        });
      } else {
        // Create new rating
        response = await axios.post(`http://127.0.0.1:8000/recipes/${recipeId}/ratings`, {
          recipe_id: recipeId,
          rating: userRating,
          review: userReview
        });
      }

      setSuccess(userHasRated ? 'Your rating was updated successfully!' : 'Your rating was submitted successfully!');
      fetchRatings();
      fetchSummary();
    } catch (err) {
      console.error('Error submitting rating:', err);
      setError(err.response?.data?.detail || 'Failed to submit rating');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Styled Star Rating component
  const StarRating = ({ value, onChange, readOnly = false }) => {
    return (
      <div style={{ display: 'flex' }}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => !readOnly && onChange(star)}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '2rem',
              color: star <= value ? '#ffc107' : '#e4e5e9',
              cursor: readOnly ? 'default' : 'pointer',
              padding: '0 5px'
            }}
          >
            ★
          </button>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '1rem' }}>
      {/* Rating Summary */}
      <div style={{
        background: '#f0f8ff',
        padding: '1.5rem',
        borderRadius: '10px',
        marginBottom: '2rem',
        boxShadow: '0 2px 5px rgba(0, 51, 102, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <h3 style={{
              color: '#003366',
              fontSize: '2rem',
              marginBottom: '0.5rem'
            }}>
              {summary.average_rating ? summary.average_rating.toFixed(1) : "0.0"}
              <span style={{ fontSize: '1rem', color: '#666', marginLeft: '0.5rem' }}>/ 5</span>
            </h3>
            <StarRating value={Math.round(summary.average_rating)} readOnly={true} />
            <p style={{
              color: '#666',
              marginTop: '0.5rem',
              fontSize: '0.9rem'
            }}>
              Based on {summary.total_ratings} {summary.total_ratings === 1 ? 'rating' : 'ratings'}
            </p>
          </div>

          <div style={{ width: '200px' }}>
            {[5, 4, 3, 2, 1].map((num) => (
              <div key={num} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.3rem'
              }}>
                <span style={{ width: '10px', color: '#666' }}>{num}</span>
                <div style={{
                  flex: 1,
                  height: '8px',
                  background: '#e4e5e9',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${summary.total_ratings ? (summary.rating_breakdown[num] / summary.total_ratings) * 100 : 0}%`,
                    background: '#ffc107',
                    borderRadius: '4px'
                  }} />
                </div>
                <span style={{ width: '30px', textAlign: 'right', color: '#666', fontSize: '0.8rem' }}>
                  {summary.rating_breakdown[num] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Rating Section */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '10px',
        marginBottom: '2rem',
        border: '1px solid #e4e5e9'
      }}>
        <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
          {userHasRated ? 'Update Your Rating' : 'Add Your Rating'}
        </h3>

        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '0.75rem',
            borderRadius: '5px',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{
            background: '#d4edda',
            color: '#155724',
            padding: '0.75rem',
            borderRadius: '5px',
            marginBottom: '1rem'
          }}>
            {success}
          </div>
        )}

        <div style={{ marginBottom: '1rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: '500',
            color: '#003366'
          }}>
            Your Rating
          </label>
          <StarRating value={userRating} onChange={setUserRating} />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontWeight: '500',
            color: '#003366'
          }}>
            Your Review (Optional)
          </label>
          <textarea
            value={userReview}
            onChange={(e) => setUserReview(e.target.value)}
            placeholder="Share your experience with this recipe..."
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '5px',
              border: '1px solid #ccc',
              minHeight: '100px',
              resize: 'vertical'
            }}
          />
        </div>

        <button
          onClick={submitRating}
          disabled={isSubmitting || userRating === 0}
          style={{
            padding: '0.75rem 1.5rem',
            background: isSubmitting || userRating === 0 ? '#ccc' : '#003366',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isSubmitting || userRating === 0 ? 'not-allowed' : 'pointer',
            fontWeight: '500'
          }}
        >
          {isSubmitting ? 'Submitting...' : userHasRated ? 'Update Rating' : 'Submit Rating'}
        </button>
      </div>

      {/* Reviews List */}
      <div>
        <h3 style={{ color: '#003366', marginBottom: '1.5rem' }}>
          User Reviews ({ratings.length})
        </h3>

        {ratings.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            background: '#f0f8ff',
            borderRadius: '10px',
            color: '#666'
          }}>
            <p>No reviews yet. Be the first to review this recipe!</p>
          </div>
        ) : (
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {ratings.map((rating) => (
              <div key={rating.id} style={{
                padding: '1.5rem',
                borderBottom: '1px solid #e4e5e9',
                marginBottom: '1rem'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem'
                }}>
                  <h4 style={{ color: '#003366', margin: 0 }}>{rating.username}</h4>
                  <span style={{ color: '#666', fontSize: '0.9rem' }}>
                    {new Date(rating.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div style={{ marginBottom: '0.5rem' }}>
                  <StarRating value={rating.rating} readOnly={true} />
                </div>

                {rating.review && (
                  <p style={{ margin: '0.5rem 0 0 0', lineHeight: '1.5' }}>
                    {rating.review}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RatingsAndReviews;
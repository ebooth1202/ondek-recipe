import React, { useState } from 'react';
import StarRating from './StarRating';
import { useAuth } from '../context/AuthContext';

const RatingForm = ({ recipeId, existingRating = null, onSubmit, onCancel }) => {
  const [rating, setRating] = useState(existingRating?.rating || 0);
  const [review, setReview] = useState(existingRating?.review || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { apiBaseUrl } = useAuth();

  const handleSubmit = async () => {
    if (rating === 0) {
      alert('Please select a rating');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const method = existingRating ? 'PUT' : 'POST';
      const url = existingRating
        ? `http://127.0.0.1:8000/recipes/${recipeId}/ratings/${existingRating.id}`
        : `http://127.0.0.1:8000/recipes/${recipeId}/ratings`;

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recipe_id: recipeId,
          rating,
          review: review.trim() || null
        })
      });

      if (response.ok) {
        const result = await response.json();
        onSubmit(result);

        // Reset form if it's a new rating
        if (!existingRating) {
          setRating(0);
          setReview('');
        }
      } else {
        const error = await response.json();
        alert(error.detail || 'Error submitting rating');
      }
    } catch (error) {
      console.error('Error submitting rating:', error);
      alert('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
      border: '3px solid #003366',
      borderRadius: '20px',
      padding: '2.5rem',
      boxShadow: '0 8px 25px rgba(0, 51, 102, 0.15)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative background elements */}
      <div style={{
        position: 'absolute',
        top: '-20px',
        right: '-20px',
        width: '100px',
        height: '100px',
        background: 'linear-gradient(45deg, #ffc107, #ffeb3b)',
        borderRadius: '50%',
        opacity: '0.1',
        zIndex: 0
      }}></div>

      <div style={{
        position: 'absolute',
        bottom: '-30px',
        left: '-30px',
        width: '80px',
        height: '80px',
        background: 'linear-gradient(45deg, #003366, #0066cc)',
        borderRadius: '50%',
        opacity: '0.1',
        zIndex: 0
      }}></div>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <h4 style={{
          color: '#003366',
          fontSize: '1.8rem',
          marginBottom: '2rem',
          textAlign: 'center',
          fontWeight: '700',
          textShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          {existingRating ? '✏️ Edit Your Rating' : '🌟 Rate This Recipe'}
        </h4>

        {/* Rating Section */}
        <div style={{
          marginBottom: '2rem',
          textAlign: 'center'
        }}>
          <label style={{
            display: 'block',
            color: '#003366',
            fontSize: '1.2rem',
            fontWeight: '600',
            marginBottom: '1rem'
          }}>
            How would you rate this recipe?
          </label>

          <div style={{
            background: 'white',
            borderRadius: '15px',
            padding: '1.5rem',
            border: '2px solid #e9ecef',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.06)',
            display: 'inline-block'
          }}>
            <StarRating
              rating={rating}
              interactive={true}
              onRatingChange={setRating}
              size="lg"
            />
          </div>

          {rating > 0 && (
            <div style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              background: 'linear-gradient(45deg, #28a745, #20c997)',
              color: 'white',
              borderRadius: '20px',
              display: 'inline-block',
              fontSize: '14px',
              fontWeight: '600',
              boxShadow: '0 2px 8px rgba(40, 167, 69, 0.3)'
            }}>
              {rating === 1 && '😞 Poor'}
              {rating === 2 && '😐 Fair'}
              {rating === 3 && '🙂 Good'}
              {rating === 4 && '😊 Very Good'}
              {rating === 5 && '🤩 Excellent'}
            </div>
          )}
        </div>

        {/* Review Section */}
        <div style={{ marginBottom: '2rem' }}>
          <label style={{
            display: 'block',
            color: '#003366',
            fontSize: '1.1rem',
            fontWeight: '600',
            marginBottom: '0.5rem'
          }}>
            Share your experience (Optional)
          </label>
          <p style={{
            fontSize: '14px',
            color: '#666',
            marginBottom: '1rem',
            fontStyle: 'italic'
          }}>
            Help others by sharing what you liked about this recipe!
          </p>

          <textarea
            value={review}
            onChange={(e) => setReview(e.target.value)}
            placeholder="Tell us about your cooking experience, any modifications you made, or tips for other cooks..."
            style={{
              width: '100%',
              padding: '1rem',
              border: '2px solid #e9ecef',
              borderRadius: '12px',
              fontSize: '15px',
              fontFamily: 'inherit',
              resize: 'vertical',
              minHeight: '120px',
              backgroundColor: 'white',
              transition: 'all 0.3s ease',
              lineHeight: '1.5',
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.06)'
            }}
            rows={4}
            maxLength={1000}
            onFocus={(e) => {
              e.target.style.borderColor = '#ffc107';
              e.target.style.boxShadow = '0 0 0 3px rgba(255, 193, 7, 0.2)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e9ecef';
              e.target.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.06)';
            }}
          />
          <div style={{
            fontSize: '12px',
            color: review.length > 900 ? '#dc3545' : '#666',
            marginTop: '0.5rem',
            textAlign: 'right',
            fontWeight: '500'
          }}>
            {review.length}/1000 characters
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0}
            style={{
              padding: '1rem 2rem',
              background: isSubmitting || rating === 0
                ? 'linear-gradient(45deg, #ccc, #999)'
                : 'linear-gradient(45deg, #003366, #0066cc)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: isSubmitting || rating === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              minWidth: '160px',
              boxShadow: isSubmitting || rating === 0
                ? 'none'
                : '0 4px 15px rgba(0, 51, 102, 0.3)',
              transform: 'translateY(0)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}
            onMouseEnter={(e) => {
              if (!isSubmitting && rating > 0) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(0, 51, 102, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isSubmitting && rating > 0) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(0, 51, 102, 0.3)';
              }
            }}
          >
            {isSubmitting ? (
              <>
                <span style={{ marginRight: '8px' }}>⏳</span>
                Submitting...
              </>
            ) : (
              <>
                <span style={{ marginRight: '8px' }}>
                  {existingRating ? '💾' : '🚀'}
                </span>
                {existingRating ? 'Update Rating' : 'Submit Rating'}
              </>
            )}
          </button>

          <button
            onClick={onCancel}
            style={{
              padding: '1rem 2rem',
              background: 'linear-gradient(45deg, #6c757d, #495057)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              minWidth: '120px',
              boxShadow: '0 4px 15px rgba(108, 117, 125, 0.3)',
              transform: 'translateY(0)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(108, 117, 125, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 15px rgba(108, 117, 125, 0.3)';
            }}
          >
            <span style={{ marginRight: '8px' }}>❌</span>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default RatingForm;
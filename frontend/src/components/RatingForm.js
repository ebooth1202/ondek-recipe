// RatingForm.js - Updated with API base URL
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
        ? `${apiBaseUrl}/recipes/${recipeId}/ratings/${existingRating.id}`
        : `${apiBaseUrl}/recipes/${recipeId}/ratings`;

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
    <div className="bg-gray-50 p-4 rounded-lg">
      <h4 className="font-medium mb-3">
        {existingRating ? 'Edit Your Rating' : 'Rate This Recipe'}
      </h4>

      <div>
        <div className="mb-4">
          <div className="block text-sm font-medium mb-2">Your Rating</div>
          <StarRating
            rating={rating}
            interactive={true}
            onRatingChange={setRating}
            size="lg"
          />
        </div>

        <div className="mb-4">
          <div className="block text-sm font-medium mb-2">
            Review (Optional)
          </div>
          <textarea
            value={review}
            onChange={(e) => setReview(e.target.value)}
            placeholder="Share your thoughts about this recipe..."
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
            maxLength={1000}
          />
          <div className="text-xs text-gray-500 mt-1">
            {review.length}/1000 characters
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : (existingRating ? 'Update Rating' : 'Submit Rating')}
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default RatingForm;
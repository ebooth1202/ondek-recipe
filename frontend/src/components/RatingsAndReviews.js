
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
  }, [recipeId, apiBaseUrl]);

  const fetchRatings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiBaseUrl}/recipes/${recipeId}/ratings`);
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
      const response = await axios.get(`${apiBaseUrl}/recipes/${recipeId}/ratings/summary`);
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
      await axios.delete(`${apiBaseUrl}/recipes/${recipeId}/ratings/${rating.id}`);

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
    <div className="w-full max-w-sm">
      {[5, 4, 3, 2, 1].map((num) => (
        <div key={num} className="flex items-center gap-2 mb-1">
          <span className="w-4 text-sm text-gray-600">{num}</span>
          <div className="flex-1 h-2 bg-gray-200 rounded overflow-hidden">
            <div
              className="h-full bg-yellow-400 rounded"
              style={{
                width: `${summary.total_ratings ? (summary.rating_breakdown[num] / summary.total_ratings) * 100 : 0}%`
              }}
            />
          </div>
          <span className="w-8 text-xs text-gray-500 text-right">
            {summary.rating_breakdown[num] || 0}
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="bg-white border-2 border-blue-900 rounded-lg p-6 mb-6 shadow-md">
      <h2 className="text-2xl font-bold text-blue-900 mb-6">
        Ratings & Reviews
      </h2>

      {/* Rating Summary */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <div className="flex flex-wrap justify-between items-center gap-6">
          <div className="text-center">
            <div className="flex items-end">
              <span className="text-4xl font-bold text-blue-900">
                {summary.average_rating ? summary.average_rating.toFixed(1) : "0.0"}
              </span>
              <span className="text-sm text-gray-500 ml-1 mb-1">/ 5</span>
            </div>
            <StarRating rating={summary.average_rating} size="lg" />
            <p className="text-sm text-gray-600 mt-1">
              Based on {summary.total_ratings} {summary.total_ratings === 1 ? 'rating' : 'ratings'}
            </p>
          </div>

          <RatingBreakdown />
        </div>
      </div>

      {/* Add/Edit Rating Form */}
      {showRatingForm ? (
        <RatingForm
          recipeId={recipeId}
          existingRating={editingRating}
          onSubmit={handleRatingSubmit}
          onCancel={() => {
            setShowRatingForm(false);
            setEditingRating(null);
          }}
        />
      ) : (
        <div className="flex justify-center mb-6">
          <button
            onClick={() => setShowRatingForm(true)}
            className="bg-blue-900 text-white px-4 py-2 rounded-lg hover:bg-blue-800 transition-colors"
          >
            {userRating ? 'Edit Your Rating' : 'Add Your Rating'}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 text-red-800 p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Reviews List */}
      <div className="mt-8">
        <h3 className="text-xl font-semibold text-blue-900 mb-4">
          User Reviews ({ratings.length})
        </h3>

        {loading ? (
          <div className="flex justify-center p-8">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-900"></div>
          </div>
        ) : ratings.length === 0 ? (
          <div className="text-center p-8 bg-blue-50 rounded-lg text-gray-600">
            <p>No reviews yet. Be the first to review this recipe!</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[500px] overflow-y-auto px-2">
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
    </div>
  );
};

export default RatingsAndReviews;
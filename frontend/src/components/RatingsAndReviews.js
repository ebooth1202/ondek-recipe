// File: frontend/src/components/RatingsAndReviews.js
import React, { useState, useEffect } from 'react';
import { MessageCircle } from 'lucide-react';
import StarRating from './StarRating';
import RatingForm from './RatingForm';
import ReviewItem from './ReviewItem';

const RatingsAndReviews = ({ recipeId, currentUserId }) => {
  const [reviews, setReviews] = useState([]);
  const [ratingsSummary, setRatingsSummary] = useState(null);
  const [showRatingForm, setShowRatingForm] = useState(false);
  const [editingRating, setEditingRating] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch ratings summary
  const fetchRatingsSummary = async () => {
    try {
      const response = await fetch(`http://localhost:8000/recipes/${recipeId}/ratings/summary`);
      if (response.ok) {
        const summary = await response.json();
        setRatingsSummary(summary);
      }
    } catch (error) {
      console.error('Error fetching ratings summary:', error);
    }
  };

  // Fetch reviews
  const fetchReviews = async () => {
    try {
      const response = await fetch(`http://localhost:8000/recipes/${recipeId}/ratings`);
      if (response.ok) {
        const reviewsData = await response.json();
        setReviews(reviewsData);
      }
    } catch (error) {
      console.error('Error fetching reviews:', error);
      setError('Failed to load reviews');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRatingsSummary();
    fetchReviews();
  }, [recipeId]);

  const handleRatingSubmit = (newRating) => {
    // Refresh data after submitting rating
    fetchRatingsSummary();
    fetchReviews();
    setShowRatingForm(false);
    setEditingRating(null);
  };

  const handleEditRating = (rating) => {
    setEditingRating(rating);
    setShowRatingForm(true);
  };

  const handleDeleteRating = async (rating) => {
    if (!window.confirm('Are you sure you want to delete your review?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/recipes/${recipeId}/ratings/${rating.id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          }
        }
      );

      if (response.ok) {
        fetchRatingsSummary();
        fetchReviews();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error deleting review');
      }
    } catch (error) {
      console.error('Error deleting rating:', error);
      alert('Network error. Please try again.');
    }
  };

  const userHasRated = reviews.some(review => review.user_id === currentUserId);
  const userRating = reviews.find(review => review.user_id === currentUserId);

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5" />
          Ratings & Reviews
        </h3>

        {ratingsSummary && ratingsSummary.total_ratings > 0 ? (
          <div className="mb-4">
            <div className="flex items-center gap-4 mb-2">
              <StarRating rating={ratingsSummary.average_rating} size="lg" />
              <span className="text-2xl font-bold">{ratingsSummary.average_rating}</span>
              <span className="text-gray-600">
                ({ratingsSummary.total_ratings} review{ratingsSummary.total_ratings !== 1 ? 's' : ''})
              </span>
            </div>

            {/* Rating breakdown */}
            <div className="space-y-1">
              {[5, 4, 3, 2, 1].map(stars => (
                <div key={stars} className="flex items-center gap-2 text-sm">
                  <span className="w-4">{stars}</span>
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-400 h-2 rounded-full"
                      style={{
                        width: `${ratingsSummary.total_ratings > 0 
                          ? (ratingsSummary.rating_breakdown[stars] / ratingsSummary.total_ratings) * 100 
                          : 0}%`
                      }}
                    ></div>
                  </div>
                  <span className="w-8 text-right">{ratingsSummary.rating_breakdown[stars] || 0}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mb-4 text-gray-600">
            No ratings yet. Be the first to rate this recipe!
          </div>
        )}

        {/* Add/Edit Rating Button */}
        {!showRatingForm && (
          <button
            onClick={() => setShowRatingForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {userHasRated ? 'Edit Your Review' : 'Write a Review'}
          </button>
        )}

        {/* Rating Form */}
        {showRatingForm && (
          <div className="mt-4">
            <RatingForm
              recipeId={recipeId}
              existingRating={editingRating || userRating}
              onSubmit={handleRatingSubmit}
              onCancel={() => {
                setShowRatingForm(false);
                setEditingRating(null);
              }}
            />
          </div>
        )}
      </div>

      {/* Reviews List */}
      {reviews.length > 0 && (
        <div>
          <h4 className="font-medium mb-4">Reviews</h4>
          <div className="space-y-4">
            {reviews.map((review) => (
              <ReviewItem
                key={review.id}
                review={review}
                currentUserId={currentUserId}
                onEdit={handleEditRating}
                onDelete={handleDeleteRating}
              />
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-600 text-center py-4">
          {error}
        </div>
      )}
    </div>
  );
};

export default RatingsAndReviews;
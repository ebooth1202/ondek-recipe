// File: frontend/src/components/ReviewItem.js
import React, { useState } from 'react';
import { Edit2, Trash2 } from 'lucide-react';
import StarRating from './StarRating';

const ReviewItem = ({ review, currentUserId, onEdit, onDelete }) => {
  const [showFullReview, setShowFullReview] = useState(false);
  const isOwner = review.user_id === currentUserId;

  const reviewText = review.review || '';
  const shouldTruncate = reviewText.length > 200;
  const displayText = shouldTruncate && !showFullReview
    ? reviewText.substring(0, 200) + '...'
    : reviewText;

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      return 'Unknown date';
    }
  };

  return (
    <div className="border-b border-gray-200 pb-4 mb-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {review.username ? review.username.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <div className="font-medium text-gray-900">{review.username || 'Anonymous'}</div>
            <div className="flex items-center gap-2">
              <StarRating rating={review.rating} size="sm" />
              <span className="text-xs text-gray-500">
                {formatDate(review.created_at)}
              </span>
            </div>
          </div>
        </div>

        {isOwner && (
          <div className="flex gap-1">
            <button
              onClick={() => onEdit(review)}
              className="p-1 text-gray-400 hover:text-blue-600 rounded"
              title="Edit review"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDelete(review)}
              className="p-1 text-gray-400 hover:text-red-600 rounded"
              title="Delete review"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {reviewText && (
        <div className="ml-11">
          <p className="text-gray-700 whitespace-pre-wrap">{displayText}</p>
          {shouldTruncate && (
            <button
              onClick={() => setShowFullReview(!showFullReview)}
              className="text-blue-600 hover:text-blue-700 text-sm mt-1"
            >
              {showFullReview ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ReviewItem;
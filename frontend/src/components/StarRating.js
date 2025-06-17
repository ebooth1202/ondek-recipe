// File: frontend/src/components/StarRating.js
import React, { useState } from 'react';
import { Star } from 'lucide-react';

const StarRating = ({ rating = 0, size = 'md', interactive = false, onRatingChange }) => {
  const [hoverRating, setHoverRating] = useState(0);
  const [currentRating, setCurrentRating] = useState(rating);

  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const handleClick = (starValue) => {
    if (!interactive) return;
    setCurrentRating(starValue);
    if (onRatingChange) {
      onRatingChange(starValue);
    }
  };

  const displayRating = interactive ? (hoverRating || currentRating) : rating;

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((starValue) => (
        <button
          key={starValue}
          type="button"
          disabled={!interactive}
          className={`${interactive ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-transform`}
          onClick={() => handleClick(starValue)}
          onMouseEnter={() => interactive && setHoverRating(starValue)}
          onMouseLeave={() => interactive && setHoverRating(0)}
        >
          <Star
            className={`${sizes[size]} ${
              starValue <= displayRating 
                ? 'text-yellow-400 fill-current' 
                : 'text-gray-300'
            }`}
          />
        </button>
      ))}
      {rating && !interactive && (
        <span className="ml-2 text-sm text-gray-600">
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  );
};

export default StarRating;
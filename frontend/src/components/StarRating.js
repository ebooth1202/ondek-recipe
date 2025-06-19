import React, { useState } from 'react';
import { Star } from 'lucide-react';

const StarRating = ({ rating = 0, size = 'md', interactive = false, onRatingChange }) => {
  const [hoverRating, setHoverRating] = useState(0);
  const [currentRating, setCurrentRating] = useState(rating);

  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const sizeStyles = {
    sm: { width: '16px', height: '16px' },
    md: { width: '24px', height: '24px' },
    lg: { width: '32px', height: '32px' }
  };

  const handleClick = (starValue) => {
    if (!interactive) return;
    setCurrentRating(starValue);
    if (onRatingChange) {
      onRatingChange(starValue);
    }
  };

  const handleMouseEnter = (starValue) => {
    if (interactive) {
      setHoverRating(starValue);
    }
  };

  const handleMouseLeave = () => {
    if (interactive) {
      setHoverRating(0);
    }
  };

  const displayRating = interactive ? (hoverRating || currentRating) : rating;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: interactive ? '4px' : '2px'
    }}>
      {[1, 2, 3, 4, 5].map((starValue) => {
        const isActive = starValue <= displayRating;
        const isHovering = interactive && hoverRating >= starValue;

        return (
          <button
            key={starValue}
            type="button"
            disabled={!interactive}
            style={{
              background: 'none',
              border: 'none',
              padding: interactive ? '4px' : '0',
              cursor: interactive ? 'pointer' : 'default',
              transition: 'all 0.2s ease',
              transform: isHovering ? 'scale(1.1)' : 'scale(1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '4px'
            }}
            onClick={() => handleClick(starValue)}
            onMouseEnter={() => handleMouseEnter(starValue)}
            onMouseLeave={handleMouseLeave}
            onFocus={() => interactive && handleMouseEnter(starValue)}
            onBlur={handleMouseLeave}
          >
            <Star
              style={{
                ...sizeStyles[size],
                color: isActive ? '#ffc107' : '#e0e0e0',
                fill: isActive ? '#ffc107' : 'transparent',
                stroke: isActive ? '#ffc107' : '#e0e0e0',
                strokeWidth: '2px',
                filter: isActive ? 'drop-shadow(0 1px 2px rgba(255, 193, 7, 0.3))' : 'none',
                transition: 'all 0.2s ease'
              }}
            />
          </button>
        );
      })}

      {/* Only show rating number for non-interactive (display) mode */}
      {!interactive && rating > 0 && (
        <span style={{
          marginLeft: '8px',
          fontSize: size === 'sm' ? '12px' : size === 'md' ? '14px' : '16px',
          color: '#666',
          fontWeight: '500'
        }}>
          {rating.toFixed(1)}
        </span>
      )}

      {/* Show rating text for interactive mode */}
      {interactive && (
        <span style={{
          marginLeft: '12px',
          fontSize: '16px',
          color: '#003366',
          fontWeight: '600',
          minWidth: '80px'
        }}>
          {displayRating > 0 ? (
            <>
              {displayRating} star{displayRating !== 1 ? 's' : ''}
              {displayRating === 1 && ' ⭐'}
              {displayRating === 2 && ' ⭐⭐'}
              {displayRating === 3 && ' ⭐⭐⭐'}
              {displayRating === 4 && ' ⭐⭐⭐⭐'}
              {displayRating === 5 && ' ⭐⭐⭐⭐⭐'}
            </>
          ) : (
            'Click to rate'
          )}
        </span>
      )}
    </div>
  );
};

export default StarRating;
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RatingCreate(BaseModel):
    recipe_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review: Optional[str] = Field(None, max_length=1000, description="Optional review text")

class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    review: Optional[str] = Field(None, max_length=1000, description="Optional review text")

class RatingResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    username: str
    rating: int
    review: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RecipeRatingsSummary(BaseModel):
    recipe_id: str
    average_rating: float
    total_ratings: int
    rating_breakdown: dict  # {1: count, 2: count, 3: count, 4: count, 5: count}

# backend/app/models/favorite.py
from pydantic import BaseModel
from datetime import datetime

class FavoriteCreate(BaseModel):
    recipe_id: str

class FavoriteResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    created_at: datetime

class UserFavoritesResponse(BaseModel):
    user_id: str
    favorites: list  # List of recipe IDs or full recipe objects
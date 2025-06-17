# backend/app/__init__.py
"""
Ondek Recipe App Backend
A comprehensive recipe management API with user roles and AI integration.
"""

__version__ = "1.0.0"
__author__ = "Ondek Recipe Team"

# backend/app/models/__init__.py
"""
Pydantic models for the Ondek Recipe API
"""

from .user import User, UserCreate, UserUpdate, UserResponse, UserRole
from .recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeResponse, Genre, MeasuringUnit, Ingredient

__all__ = [
    "User", "UserCreate", "UserUpdate", "UserResponse", "UserRole",
    "Recipe", "RecipeCreate", "RecipeUpdate", "RecipeResponse",
    "Genre", "MeasuringUnit", "Ingredient"
]

# backend/app/routes/__init__.py
"""
API routes for the Ondek Recipe application
"""

# backend/app/middleware/__init__.py
"""
Middleware for authentication and authorization
"""

# backend/app/utils/__init__.py
"""
Utility functions for the Ondek Recipe application
"""

from .password import hash_password, verify_password, validate_password_strength
from .ai_helper import AIHelper, ai_helper

__all__ = [
    "hash_password", "verify_password", "validate_password_strength",
    "AIHelper", "ai_helper"
]
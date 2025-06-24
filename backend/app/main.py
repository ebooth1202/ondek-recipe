# backend/app/main.py - Fixed version with better error handling and photo support

from fastapi import FastAPI, HTTPException, Depends, status, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt
from jose import jwt  # ✅ This is correct
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
import re
from statistics import mean
import logging
import uuid
import asyncio
import tempfile
import csv
import io
import json
import shutil
from pathlib import Path
from .config import settings  # Make sure you import your settings
from .database import db, Database
from .utils.ai_helper import ai_helper


# Load environment variables first
# load_dotenv()
from pathlib import Path

# env_path = Path(__file__).parent.parent.parent / '.env'
# load_dotenv(dotenv_path=env_path)

possible_env_paths = [
    Path(__file__).parent.parent.parent / '.env',  # Original calculation
    Path.cwd() / '.env',  # Current working directory
    Path(__file__).parent.parent / '.env',  # Backend directory
    Path.cwd().parent / '.env' if 'backend' in str(Path.cwd()) else Path.cwd() / '.env'
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        print(f"Loading .env from: {env_path}")
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        break

if not env_loaded:
    print("Warning: No .env file found in any expected location")
    print("Tried paths:")
    for path in possible_env_paths:
        print(f"  - {path} (exists: {path.exists()})")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import database - with error handling
try:
    from .database import db, Database

    logger.info("Database module imported successfully")
    db_available = True
except Exception as e:
    logger.error(f"Failed to import database: {e}")
    db = None
    db_available = False

# Try to import AI helper - with error handling (skip file processing dependencies)
try:
    from .utils.ai_helper import ai_helper

    logger.info("AI helper imported successfully")
    ai_available = True
except Exception as e:
    logger.error(f"Failed to import AI helper: {e}")
    ai_helper = None
    ai_available = False

# Initialize FastAPI app
app = FastAPI(
    title="Ondek Recipe API",
    description="A comprehensive recipe management API with AI integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development origins
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # Production origins
        settings.frontend_url,  # https://yourdomain.com
        settings.base_url,      # https://api.yourdomain.com
        # Backup Heroku URL
        f"https://{os.getenv('HEROKU_APP_NAME', 'your-app-name')}.herokuapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
    max_age=600,
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
security = HTTPBearer()

@app.get("/test")
async def test_route():
    return {"message": "Test route works", "build_exists": os.path.exists("/app/frontend/build")}

# Pydantic Models (keeping existing models...)
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None


class RoleUpdate(BaseModel):
    role: UserRole


class Genre(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    APPETIZER = "appetizer"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    EGG_FREE = "egg_free"


class MeasuringUnit(str, Enum):
    CUP = "cup"
    CUPS = "cups"
    TABLESPOON = "tablespoon"
    TABLESPOONS = "tablespoons"
    TEASPOON = "teaspoon"
    TEASPOONS = "teaspoons"
    OUNCE = "ounce"
    OUNCES = "ounces"
    POUND = "pound"
    POUNDS = "pounds"
    GRAM = "gram"
    GRAMS = "grams"
    KILOGRAM = "kilogram"
    KILOGRAMS = "kilograms"
    LITER = "liter"
    LITERS = "liters"
    MILLILITER = "milliliter"
    MILLILITERS = "milliliters"
    PIECE = "piece"
    PIECES = "pieces"
    WHOLE = "whole"
    STICK = "stick"
    STICKS = "sticks"
    PINCH = "pinch"
    DASH = "dash"


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: MeasuringUnit


# Add all your other existing models here...
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    created_at: datetime


class Recipe(BaseModel):
    recipe_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    ingredients: List[Ingredient] = Field(..., min_items=1)
    instructions: List[str] = Field(..., min_items=1)
    serving_size: int = Field(..., gt=0, le=100)
    genre: Genre
    prep_time: Optional[int] = Field(0, ge=0, le=1440)
    cook_time: Optional[int] = Field(0, ge=0, le=1440)
    notes: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    photo_url: Optional[str] = None


class RecipeResponse(BaseModel):
    id: str
    recipe_name: str
    description: Optional[str] = None
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    prep_time: Optional[int] = 0
    cook_time: Optional[int] = 0
    notes: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    created_by: str
    created_at: datetime
    photo_url: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Photo handling functions
async def save_uploaded_photo(photo: UploadFile, recipe_id: str) -> Optional[str]:
    """Save uploaded photo and return the photo URL"""
    try:
        # Create photos directory if it doesn't exist
        photos_dir = Path("static/photos")
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(photo.filename)[1].lower()
        if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            raise ValueError("Invalid file type")

        filename = f"recipe_{recipe_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = photos_dir / filename

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        # Return the full URL using settings
        return f"{settings.base_url}/photos/{filename}"

    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        return None


def fix_photo_url(photo_url: Optional[str]) -> Optional[str]:
    """Convert old static URLs to new photo endpoint URLs"""
    if not photo_url:
        return None

    # Use base URL from settings
    base_url = settings.base_url

    # If it's already a full URL, return as-is
    if photo_url.startswith('http'):
        return photo_url

    # If it's an old static path, convert it
    if photo_url.startswith('/static/photos/'):
        filename = photo_url.replace('/static/photos/', '')
        return f"{base_url}/photos/{filename}"

    # If it's just a filename, add the full URL
    if not photo_url.startswith('/'):
        return f"{base_url}/photos/{filename}"

    return photo_url


# Photo serving route - MUST BE BEFORE OTHER ROUTES
@app.get("/photos/{filename}")
async def get_photo(filename: str):
    """Serve photos with proper CORS headers"""
    photo_path = Path("static/photos") / filename
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    return FileResponse(
        photo_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Ondek Recipe API...")
    logger.info(f"Environment: {'Production' if settings.is_production() else 'Development'}")
    logger.info(f"Base URL: {settings.base_url}")

    if not db_available:
        logger.warning("Database connection not available")
    else:
        logger.info("Database connection verified")

    if not ai_available:
        logger.warning("AI helper not available")
    elif ai_helper and ai_helper.is_configured():
        logger.info("AI helper configured and ready")
    else:
        logger.warning("AI helper available but not configured (missing OpenAI API key)")

# 5. UPDATE the main section at the bottom
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info" if settings.is_production() else "debug"
    )


# Health check route
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": "connected" if db_available else "unavailable",
        "ai": "configured" if (ai_available and ai_helper and ai_helper.is_configured()) else "not configured"
    }


# Basic routes
# @app.get("/")
# async def root():
#     return {"message": "Welcome to the Ondek Recipe API! 🍳"}


# Authentication routes
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.role in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Cannot create admin users through registration")

    hashed_password = hash_password(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role.value,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    # Add first_name and last_name if provided
    if user.first_name:
        user_doc["first_name"] = user.first_name
    if user.last_name:
        user_doc["last_name"] = user.last_name

    result = db.users.insert_one(user_doc)

    return UserResponse(
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        created_at=user_doc["created_at"]
    )


@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    logger.info(f"Login attempt for username: {user.username}")

    db_user = db.users.find_one({"username": user.username})
    if not db_user:
        logger.info(f"User not found: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(user.password, db_user["password"]):
        logger.info(f"Password verification failed for: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": db_user["username"]}, expires_delta=access_token_expires
    )

    user_response = UserResponse(
        id=str(db_user["_id"]),
        username=db_user["username"],
        email=db_user["email"],
        first_name=db_user.get("first_name"),
        last_name=db_user.get("last_name"),
        role=UserRole(db_user["role"]),
        created_at=db_user["created_at"]
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        role=UserRole(current_user["role"]),
        created_at=current_user["created_at"]
    )


# User management routes
@app.get("/users", response_model=List[UserResponse])
async def get_users(
        skip: int = Query(0, ge=0, description="Number of users to skip"),
        limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get all users - Admin/Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    cursor = db.users.find({}).skip(skip).limit(limit).sort("created_at", -1)
    users = []

    for user_doc in cursor:
        users.append(UserResponse(
            id=str(user_doc["_id"]),
            username=user_doc["username"],
            email=user_doc["email"],
            first_name=user_doc.get("first_name"),
            last_name=user_doc.get("last_name"),
            role=UserRole(user_doc["role"]),
            created_at=user_doc["created_at"]
        ))

    return users


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
        user_id: str,
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get a specific user by ID - Admin/Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        email=user_doc["email"],
        first_name=user_doc.get("first_name"),
        last_name=user_doc.get("last_name"),
        role=UserRole(user_doc["role"]),
        created_at=user_doc["created_at"]
    )


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: str,
        user_update: UserUpdate,
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Update a user - Admin/Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    existing_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update document
    update_doc = {"updated_at": datetime.now()}

    if user_update.first_name is not None:
        update_doc["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_doc["last_name"] = user_update.last_name
    if user_update.email is not None:
        if not validate_email(user_update.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        # Check if email is already taken by another user
        email_check = db.users.find_one({"email": user_update.email, "_id": {"$ne": ObjectId(user_id)}})
        if email_check:
            raise HTTPException(status_code=400, detail="Email already registered")
        update_doc["email"] = user_update.email

    # Update the user
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_doc}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes were made")

    # Return the updated user
    updated_user = db.users.find_one({"_id": ObjectId(user_id)})
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        first_name=updated_user.get("first_name"),
        last_name=updated_user.get("last_name"),
        role=UserRole(updated_user["role"]),
        created_at=updated_user["created_at"]
    )


@app.delete("/users/{user_id}")
async def delete_user(
        user_id: str,
        current_user: dict = Depends(require_role([UserRole.OWNER]))  # Only owners can delete users
):
    """Delete a user - Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Don't allow deleting yourself
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Don't allow deleting other owners
    if user_doc["role"] == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete owner accounts")

    # Delete the user
    db.users.delete_one({"_id": ObjectId(user_id)})

    return {"message": "User deleted successfully"}


@app.put("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
        user_id: str,
        role_update: RoleUpdate,
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Change a user's role - Admin/Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    existing_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Don't allow changing your own role
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    # Don't allow changing owner roles unless you're an owner
    if existing_user["role"] == "owner" and current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner role")

    # Don't allow non-owners to assign owner role
    if role_update.role == UserRole.OWNER and current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can assign owner role")

    # Update the user's role
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role_update.role.value, "updated_at": datetime.now()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="No changes were made")

    # Return the updated user
    updated_user = db.users.find_one({"_id": ObjectId(user_id)})
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        first_name=updated_user.get("first_name"),
        last_name=updated_user.get("last_name"),
        role=UserRole(updated_user["role"]),
        created_at=updated_user["created_at"]
    )


# Recipe routes - Updated with photo support
@app.post("/recipes", response_model=RecipeResponse)
async def create_recipe(
        recipe_data: str = Form(...),
        photo: Optional[UploadFile] = File(None),
        current_user: dict = Depends(get_current_user)
):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Parse the JSON recipe data from form
        recipe_dict = json.loads(recipe_data)
        recipe = Recipe(**recipe_dict)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid recipe data format. Please check your recipe information.")
    except ValidationError as e:
        logger.error(f"Recipe validation error: {e}")
        # Extract specific field errors for better user feedback
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        raise HTTPException(status_code=422, detail=f"Recipe validation failed: {'; '.join(error_details)}")
    except Exception as e:
        logger.error(f"Recipe parsing error: {e}")
        raise HTTPException(status_code=400,
                            detail=f"Invalid recipe data: Please review your recipe information and try again.")

    # Validate required fields more specifically
    if not recipe.recipe_name or not recipe.recipe_name.strip():
        raise HTTPException(status_code=400, detail="Recipe name is required")

    if not recipe.ingredients or len(recipe.ingredients) == 0:
        raise HTTPException(status_code=400, detail="At least one ingredient is required")

    if not recipe.instructions or len(recipe.instructions) == 0:
        raise HTTPException(status_code=400, detail="At least one instruction is required")

    # Validate ingredient data
    for i, ingredient in enumerate(recipe.ingredients):
        if not ingredient.name or not ingredient.name.strip():
            raise HTTPException(status_code=400, detail=f"Ingredient {i + 1} name is required")
        if ingredient.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Ingredient {i + 1} quantity must be greater than 0")

    # Validate instructions
    for i, instruction in enumerate(recipe.instructions):
        if not instruction or not instruction.strip():
            raise HTTPException(status_code=400, detail=f"Instruction {i + 1} cannot be empty")

    try:
        recipe_doc = {
            "recipe_name": recipe.recipe_name.strip(),
            "description": recipe.description.strip() if recipe.description else None,
            "ingredients": [ing.dict() for ing in recipe.ingredients],
            "instructions": [inst.strip() for inst in recipe.instructions if inst.strip()],
            "serving_size": recipe.serving_size,
            "genre": recipe.genre.value,
            "prep_time": recipe.prep_time or 0,
            "cook_time": recipe.cook_time or 0,
            "notes": [note.strip() for note in (recipe.notes or []) if note.strip()],
            "dietary_restrictions": recipe.dietary_restrictions or [],
            "created_by": current_user["username"],
            "created_at": datetime.now(),
            "photo_url": None  # Will be updated if photo is provided
        }

        # Insert recipe first to get the ID
        result = db.recipes.insert_one(recipe_doc)
        recipe_id = str(result.inserted_id)

        # Handle photo upload if provided
        photo_url = None
        if photo and photo.filename and photo.filename.strip():
            try:
                photo_url = await save_uploaded_photo(photo, recipe_id)
                if photo_url:
                    # Update the recipe with the photo URL
                    db.recipes.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {"photo_url": photo_url}}
                    )
                    recipe_doc["photo_url"] = photo_url
                    logger.info(f"Photo uploaded successfully for recipe {recipe_id}: {photo_url}")
                else:
                    logger.warning(f"Photo upload failed for recipe {recipe_id}")
            except Exception as photo_error:
                logger.error(f"Photo upload error for recipe {recipe_id}: {photo_error}")
                # Don't fail the recipe creation if photo upload fails
                pass

        # Prepare response
        ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]
        return RecipeResponse(
            id=recipe_id,
            recipe_name=recipe_doc["recipe_name"],
            description=recipe_doc.get("description"),
            ingredients=ingredients,
            instructions=recipe_doc["instructions"],
            serving_size=recipe_doc["serving_size"],
            genre=Genre(recipe_doc["genre"]),
            prep_time=recipe_doc.get("prep_time", 0),
            cook_time=recipe_doc.get("cook_time", 0),
            notes=recipe_doc.get("notes", []),
            dietary_restrictions=recipe_doc.get("dietary_restrictions", []),
            created_by=recipe_doc["created_by"],
            created_at=recipe_doc["created_at"],
            photo_url=photo_url
        )

    except Exception as e:
        logger.error(f"Error saving recipe to database: {e}")
        # Clean up if recipe was partially created
        try:
            if 'result' in locals() and result.inserted_id:
                db.recipes.delete_one({"_id": result.inserted_id})
        except:
            pass
        raise HTTPException(status_code=500, detail="Failed to save recipe. Please try again.")


@app.get("/recipes", response_model=List[RecipeResponse])
async def get_recipes(
        search: Optional[str] = Query(None, description="Search recipes by name or ingredients"),
        genre: Optional[Genre] = Query(None, description="Filter by genre"),
        skip: int = Query(0, ge=0, description="Number of recipes to skip"),
        limit: int = Query(100, ge=1, le=100, description="Number of recipes to return")
):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    query = {}

    if search:
        query["$or"] = [
            {"recipe_name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"ingredients.name": {"$regex": search, "$options": "i"}}
        ]

    if genre:
        query["genre"] = genre.value

    cursor = db.recipes.find(query).skip(skip).limit(limit).sort("recipe_name", 1)
    recipes = []

    for recipe_doc in cursor:
        ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]

        # Fix photo URL for backward compatibility
        photo_url = fix_photo_url(recipe_doc.get("photo_url"))

        recipes.append(RecipeResponse(
            id=str(recipe_doc["_id"]),
            recipe_name=recipe_doc["recipe_name"],
            description=recipe_doc.get("description"),
            ingredients=ingredients,
            instructions=recipe_doc["instructions"],
            serving_size=recipe_doc["serving_size"],
            genre=Genre(recipe_doc["genre"]),
            prep_time=recipe_doc.get("prep_time", 0),
            cook_time=recipe_doc.get("cook_time", 0),
            notes=recipe_doc.get("notes", []),
            dietary_restrictions=recipe_doc.get("dietary_restrictions", []),
            created_by=recipe_doc["created_by"],
            created_at=recipe_doc["created_at"],
            photo_url=photo_url
        ))

    return recipes


class EnhancedRecipeResponse(BaseModel):
    id: str
    recipe_name: str
    description: Optional[str] = None
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
    prep_time: Optional[int] = 0
    cook_time: Optional[int] = 0
    notes: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    created_by: str
    created_at: datetime
    average_rating: Optional[float] = None
    total_ratings: int = 0
    user_has_favorited: bool = False
    user_rating: Optional[int] = None
    photo_url: Optional[str] = None


@app.get("/recipes/{recipe_id}", response_model=EnhancedRecipeResponse)
async def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe_doc:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Get rating info
    ratings = list(db.ratings.find({"recipe_id": recipe_id}))
    average_rating = None
    total_ratings = len(ratings)
    user_rating = None

    if ratings:
        rating_values = [r["rating"] for r in ratings]
        average_rating = round(mean(rating_values), 1)

        # Find user's rating
        user_rating_doc = next((r for r in ratings if r["user_id"] == str(current_user["_id"])), None)
        if user_rating_doc:
            user_rating = user_rating_doc["rating"]

    # Check if user has favorited
    favorite = db.favorites.find_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })
    user_has_favorited = favorite is not None

    ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]

    # Fix photo URL for backward compatibility
    photo_url = fix_photo_url(recipe_doc.get("photo_url"))

    return EnhancedRecipeResponse(
        id=str(recipe_doc["_id"]),
        recipe_name=recipe_doc["recipe_name"],
        description=recipe_doc.get("description"),
        ingredients=ingredients,
        instructions=recipe_doc["instructions"],
        serving_size=recipe_doc["serving_size"],
        genre=Genre(recipe_doc["genre"]),
        prep_time=recipe_doc.get("prep_time", 0),
        cook_time=recipe_doc.get("cook_time", 0),
        notes=recipe_doc.get("notes", []),
        dietary_restrictions=recipe_doc.get("dietary_restrictions", []),
        created_by=recipe_doc["created_by"],
        created_at=recipe_doc["created_at"],
        average_rating=average_rating,
        total_ratings=total_ratings,
        user_has_favorited=user_has_favorited,
        user_rating=user_rating,
        photo_url=photo_url
    )


# RATING MODELS AND ROUTES
class RatingCreate(BaseModel):
    recipe_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
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
    rating_breakdown: dict


class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5 stars")
    review: Optional[str] = Field(None, max_length=1000, description="Optional review text")


@app.post("/recipes/{recipe_id}/ratings", response_model=RatingResponse)
async def create_rating(
        recipe_id: str,
        rating_data: RatingCreate,
        current_user: dict = Depends(get_current_user)
):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing_rating = db.ratings.find_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this recipe")

    rating_doc = {
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"]),
        "username": current_user["username"],
        "rating": rating_data.rating,
        "review": rating_data.review,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = db.ratings.insert_one(rating_doc)

    return RatingResponse(
        id=str(result.inserted_id),
        recipe_id=recipe_id,
        user_id=str(current_user["_id"]),
        username=current_user["username"],
        rating=rating_data.rating,
        review=rating_data.review,
        created_at=rating_doc["created_at"],
        updated_at=rating_doc["updated_at"]
    )


@app.get("/recipes/{recipe_id}/ratings", response_model=List[RatingResponse])
async def get_recipe_ratings(
        recipe_id: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100)
):
    """Get all ratings for a specific recipe"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ratings = []
    cursor = db.ratings.find({"recipe_id": recipe_id}).skip(skip).limit(limit).sort("created_at", -1)

    for rating_doc in cursor:
        ratings.append(RatingResponse(
            id=str(rating_doc["_id"]),
            recipe_id=rating_doc["recipe_id"],
            user_id=rating_doc["user_id"],
            username=rating_doc["username"],
            rating=rating_doc["rating"],
            review=rating_doc.get("review"),
            created_at=rating_doc["created_at"],
            updated_at=rating_doc["updated_at"]
        ))

    return ratings


@app.get("/recipes/{recipe_id}/ratings/summary", response_model=RecipeRatingsSummary)
async def get_recipe_ratings_summary(recipe_id: str):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ratings = list(db.ratings.find({"recipe_id": recipe_id}))

    if not ratings:
        return RecipeRatingsSummary(
            recipe_id=recipe_id,
            average_rating=0.0,
            total_ratings=0,
            rating_breakdown={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        )

    rating_values = [r["rating"] for r in ratings]
    average_rating = mean(rating_values)

    breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in rating_values:
        breakdown[rating] += 1

    return RecipeRatingsSummary(
        recipe_id=recipe_id,
        average_rating=round(average_rating, 1),
        total_ratings=len(ratings),
        rating_breakdown=breakdown
    )


@app.put("/recipes/{recipe_id}/ratings/{rating_id}", response_model=RatingResponse)
async def update_rating(
        recipe_id: str,
        rating_id: str,
        rating_update: RatingUpdate,
        current_user: dict = Depends(get_current_user)
):
    """Update a rating"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        rating_doc = db.ratings.find_one({"_id": ObjectId(rating_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid rating ID")

    if not rating_doc:
        raise HTTPException(status_code=404, detail="Rating not found")

    if rating_doc["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to edit this rating")

    update_doc = {"updated_at": datetime.now()}
    if rating_update.rating is not None:
        update_doc["rating"] = rating_update.rating
    if rating_update.review is not None:
        update_doc["review"] = rating_update.review

    db.ratings.update_one({"_id": ObjectId(rating_id)}, {"$set": update_doc})

    updated_rating = db.ratings.find_one({"_id": ObjectId(rating_id)})
    return RatingResponse(
        id=str(updated_rating["_id"]),
        recipe_id=updated_rating["recipe_id"],
        user_id=updated_rating["user_id"],
        username=updated_rating["username"],
        rating=updated_rating["rating"],
        review=updated_rating.get("review"),
        created_at=updated_rating["created_at"],
        updated_at=updated_rating["updated_at"]
    )


@app.delete("/recipes/{recipe_id}/ratings/{rating_id}")
async def delete_rating(
        recipe_id: str,
        rating_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Delete a rating"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        rating_doc = db.ratings.find_one({"_id": ObjectId(rating_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid rating ID")

    if not rating_doc:
        raise HTTPException(status_code=404, detail="Rating not found")

    if (rating_doc["user_id"] != str(current_user["_id"]) and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this rating")

    db.ratings.delete_one({"_id": ObjectId(rating_id)})
    return {"message": "Rating deleted successfully"}


# FAVORITES ROUTES
class FavoriteResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    created_at: datetime


@app.post("/recipes/{recipe_id}/favorite", response_model=FavoriteResponse)
async def add_to_favorites(recipe_id: str, current_user: dict = Depends(get_current_user)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing_favorite = db.favorites.find_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    if existing_favorite:
        raise HTTPException(status_code=400, detail="Recipe already in favorites")

    favorite_doc = {
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"]),
        "created_at": datetime.now()
    }

    result = db.favorites.insert_one(favorite_doc)

    return FavoriteResponse(
        id=str(result.inserted_id),
        recipe_id=recipe_id,
        user_id=str(current_user["_id"]),
        created_at=favorite_doc["created_at"]
    )


@app.delete("/recipes/{recipe_id}/favorite")
async def remove_from_favorites(recipe_id: str, current_user: dict = Depends(get_current_user)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    result = db.favorites.delete_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not in favorites")

    return {"message": "Recipe removed from favorites"}


@app.get("/users/me/favorites", response_model=List[RecipeResponse])
async def get_user_favorites(current_user: dict = Depends(get_current_user)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    favorites = list(db.favorites.find({"user_id": str(current_user["_id"])}))
    favorite_recipe_ids = [fav["recipe_id"] for fav in favorites]

    if not favorite_recipe_ids:
        return []

    recipes = []
    for recipe_id in favorite_recipe_ids:
        try:
            recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
            if recipe_doc:
                ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]

                # Fix photo URL for backward compatibility
                photo_url = fix_photo_url(recipe_doc.get("photo_url"))

                recipes.append(RecipeResponse(
                    id=str(recipe_doc["_id"]),
                    recipe_name=recipe_doc["recipe_name"],
                    description=recipe_doc.get("description"),
                    ingredients=ingredients,
                    instructions=recipe_doc["instructions"],
                    serving_size=recipe_doc["serving_size"],
                    genre=Genre(recipe_doc["genre"]),
                    prep_time=recipe_doc.get("prep_time", 0),
                    cook_time=recipe_doc.get("cook_time", 0),
                    notes=recipe_doc.get("notes", []),
                    dietary_restrictions=recipe_doc.get("dietary_restrictions", []),
                    created_by=recipe_doc["created_by"],
                    created_at=recipe_doc["created_at"],
                    photo_url=photo_url
                ))
        except InvalidId:
            continue

    return recipes


@app.get("/recipes/{recipe_id}/favorite-status")
async def check_favorite_status(recipe_id: str, current_user: dict = Depends(get_current_user)):
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    favorite = db.favorites.find_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    return {"is_favorited": favorite is not None}


# Recipe Update Model and Route
class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    serving_size: Optional[int] = None
    genre: Optional[Genre] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    notes: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    photo_url: Optional[str] = None


@app.put("/recipes/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
        recipe_id: str,
        recipe_data: str = Form(...),
        photo: Optional[UploadFile] = File(None),
        current_user: dict = Depends(get_current_user)
):
    """Update an existing recipe"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    # Find the existing recipe
    existing_recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if user owns the recipe or is admin/owner
    if (existing_recipe["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to edit this recipe")

    try:
        # Parse the JSON recipe data from form
        recipe_dict = json.loads(recipe_data)
        recipe_update = RecipeUpdate(**recipe_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid recipe data format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid recipe data: {str(e)}")

    # Build update document
    update_doc = {"updated_at": datetime.now()}

    if recipe_update.recipe_name is not None:
        update_doc["recipe_name"] = recipe_update.recipe_name
    if recipe_update.description is not None:
        update_doc["description"] = recipe_update.description
    if recipe_update.ingredients is not None:
        update_doc["ingredients"] = [ing.dict() for ing in recipe_update.ingredients]
    if recipe_update.instructions is not None:
        update_doc["instructions"] = recipe_update.instructions
    if recipe_update.serving_size is not None:
        update_doc["serving_size"] = recipe_update.serving_size
    if recipe_update.genre is not None:
        update_doc["genre"] = recipe_update.genre.value
    if recipe_update.prep_time is not None:
        update_doc["prep_time"] = recipe_update.prep_time
    if recipe_update.cook_time is not None:
        update_doc["cook_time"] = recipe_update.cook_time
    if recipe_update.notes is not None:
        update_doc["notes"] = recipe_update.notes
    if recipe_update.dietary_restrictions is not None:
        update_doc["dietary_restrictions"] = recipe_update.dietary_restrictions

    # Handle photo upload if provided
    if photo and photo.filename:
        photo_url = await save_uploaded_photo(photo, recipe_id)
        if photo_url:
            update_doc["photo_url"] = photo_url

    # Update the recipe
    result = db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": update_doc}
    )

    if result.modified_count == 0 and not photo:
        raise HTTPException(status_code=400, detail="No changes were made")

    # Return the updated recipe
    updated_recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    ingredients = [Ingredient(**ing) for ing in updated_recipe["ingredients"]]

    return RecipeResponse(
        id=str(updated_recipe["_id"]),
        recipe_name=updated_recipe["recipe_name"],
        description=updated_recipe.get("description"),
        ingredients=ingredients,
        instructions=updated_recipe["instructions"],
        serving_size=updated_recipe["serving_size"],
        genre=Genre(updated_recipe["genre"]),
        prep_time=updated_recipe.get("prep_time", 0),
        cook_time=updated_recipe.get("cook_time", 0),
        notes=updated_recipe.get("notes", []),
        dietary_restrictions=updated_recipe.get("dietary_restrictions", []),
        created_by=updated_recipe["created_by"],
        created_at=updated_recipe["created_at"],
        photo_url=updated_recipe.get("photo_url")
    )


@app.delete("/recipes/{recipe_id}")
async def delete_recipe(
        recipe_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Delete a recipe"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check permissions
    if (recipe["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    # Delete associated data
    db.ratings.delete_many({"recipe_id": recipe_id})
    db.favorites.delete_many({"recipe_id": recipe_id})

    # Delete the recipe
    db.recipes.delete_one({"_id": ObjectId(recipe_id)})

    return {"message": "Recipe deleted successfully"}


# AI ROUTES AND MODELS
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []
    action_type: Optional[str] = None
    action_metadata: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime


class RecipeSearchRequest(BaseModel):
    ingredients: List[str]


class FileUploadResponse(BaseModel):
    success: bool
    message: str
    temp_id: Optional[str] = None
    file_type: Optional[str] = None
    parsed_content: Optional[str] = None
    recipe_data: Optional[dict] = None
    error: Optional[str] = None


@app.get("/ai/status")
async def ai_status():
    """Check AI service status"""
    return {
        "ai_configured": ai_available and ai_helper.is_configured() if ai_available else False,
        "model": ai_helper.model if ai_available and ai_helper.is_configured() else None,
        "database_connected": db_available
    }


@app.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Enhanced AI chat endpoint for recipe-related conversations with recipe creation support"""
    try:
        if not ai_available:
            return ChatResponse(
                response="AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key.",
                timestamp=datetime.now()
            )

        # Process the chat message with enhanced recipe creation support
        response_text = await ai_helper.chat_about_recipes(
            user_message=chat_data.message,
            conversation_history=chat_data.conversation_history,
            action_type=chat_data.action_type,
            action_metadata=chat_data.action_metadata
        )

        return ChatResponse(
            response=response_text,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return ChatResponse(
            response="I'm sorry, I encountered an error while processing your request. Please try again.",
            timestamp=datetime.now()
        )


@app.post("/ai/recipe-suggestions")
async def get_recipe_suggestions(
        search_request: RecipeSearchRequest,
        current_user: dict = Depends(get_current_user)
):
    """Get recipe suggestions based on available ingredients"""
    try:
        if not ai_available:
            return {"response": "AI features are currently unavailable."}

        suggestions = ai_helper.get_recipe_suggestions_by_ingredients(
            search_request.ingredients
        )

        return {"response": suggestions}

    except Exception as e:
        logger.error(f"Error getting recipe suggestions: {e}")
        return {"response": "Sorry, I couldn't retrieve recipe suggestions at the moment."}


@app.get("/ai/recipe-search")
async def search_recipes_ai(
        query: str = Query(..., description="Natural language search query"),
        current_user: dict = Depends(get_current_user)
):
    """Search recipes using natural language processing"""
    try:
        if not ai_available:
            return {"recipes": [], "message": "AI features are currently unavailable."}

        # Extract search criteria from the query
        search_criteria = ai_helper.extract_search_intent(query)

        # Search for recipes
        if search_criteria:
            recipes = ai_helper.search_recipes_by_criteria(search_criteria)
        else:
            # If no specific criteria, return a general set
            recipes = ai_helper.get_recipes_data(limit=10)

        return {
            "recipes": recipes,
            "criteria_found": search_criteria,
            "total_found": len(recipes)
        }

    except Exception as e:
        logger.error(f"Error in AI recipe search: {e}")
        return {"recipes": [], "message": "Error processing search query"}


@app.post("/ai/upload-recipe-file", response_model=FileUploadResponse)
async def upload_recipe_file(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    """Upload and parse a file containing recipe information"""
    try:
        if not ai_available:
            return FileUploadResponse(
                success=False,
                error="AI features are currently unavailable. Please contact the administrator."
            )

        # Validate file size (10MB limit)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return FileUploadResponse(
                success=False,
                error="File size too large. Please upload files smaller than 10MB."
            )

        # Reset file pointer
        await file.seek(0)

        # Detect file type
        try:
            import magic
            file_type = magic.from_buffer(file_content, mime=True)
        except:
            # Fallback if python-magic fails
            file_type = file.content_type or "application/octet-stream"

        file_extension = os.path.splitext(file.filename.lower())[1]

        logger.info(f"Processing file: {file.filename}, type: {file_type}, extension: {file_extension}")

        # Parse the file based on type
        parsing_result = await ai_helper.parse_recipe_file(
            file_content=file_content,
            filename=file.filename,
            file_type=file_type,
            file_extension=file_extension
        )

        if not parsing_result:
            return FileUploadResponse(
                success=False,
                error="Could not extract recipe information from the uploaded file."
            )

        # If we successfully extracted recipe data, store it temporarily
        temp_id = None
        if parsing_result.recipe_data:
            temp_id = ai_helper.store_temp_recipe(parsing_result.recipe_data.dict())

        return FileUploadResponse(
            success=True,
            message=f"Successfully parsed recipe from {file.filename}!",
            temp_id=temp_id,
            file_type=parsing_result.file_type,
            parsed_content=parsing_result.parsed_text[:500] + "..." if len(
                parsing_result.parsed_text) > 500 else parsing_result.parsed_text,
            recipe_data=parsing_result.recipe_data.dict() if parsing_result.recipe_data else None
        )

    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return FileUploadResponse(
            success=False,
            error=f"Error processing file: {str(e)}"
        )


@app.post("/ai/parse-recipe-from-text")
async def parse_recipe_from_text_advanced(
        text_content: str = Form(...),
        source_info: Optional[str] = Form(None),
        current_user: dict = Depends(get_current_user)
):
    """Parse recipe information from raw text content"""
    try:
        if not ai_available:
            return {"success": False, "error": "AI features are currently unavailable."}

        # Use AI to parse the text
        recipe_data = await ai_helper.parse_recipe_from_text_advanced(
            text_content,
            source_info=source_info
        )

        if not recipe_data:
            return {"success": False, "error": "Could not extract recipe information from the provided text."}

        # Store temporarily
        temp_id = ai_helper.store_temp_recipe(recipe_data)

        return {
            "success": True,
            "message": "Recipe parsed successfully from text!",
            "temp_id": temp_id,
            "recipe_data": recipe_data
        }

    except Exception as e:
        logger.error(f"Error parsing recipe from text: {e}")
        return {"success": False, "error": f"Error parsing text: {str(e)}"}


@app.post("/ai/parse-recipe")
async def parse_recipe_text(
        recipe_text: str,
        current_user: dict = Depends(get_current_user)
):
    """Parse recipe text and return formatted data for the add recipe form"""
    try:
        if not ai_available:
            return {"error": "AI features are currently unavailable."}

        # Parse the recipe text
        parsed_recipe = ai_helper.parse_recipe_from_text(recipe_text)

        if not parsed_recipe:
            return {"error": "Could not parse recipe from the provided text"}

        # Format for the form
        formatted_recipe = ai_helper.format_recipe_for_form(parsed_recipe)

        if not formatted_recipe:
            return {"error": "Could not format recipe for form"}

        # Store temporarily and return ID
        temp_id = ai_helper.store_temp_recipe(formatted_recipe)

        return {
            "temp_id": temp_id,
            "recipe_data": formatted_recipe,
            "message": "Recipe parsed successfully"
        }

    except Exception as e:
        logger.error(f"Error parsing recipe: {e}")
        return {"error": "Error parsing recipe text"}


@app.post("/store-temp-recipe")
async def store_temp_recipe(
        recipe_data: dict,
        current_user: dict = Depends(get_current_user)
):
    """Store recipe data temporarily for later retrieval"""
    try:
        if not ai_available:
            raise HTTPException(status_code=503, detail="AI features not available")

        # Validate and format the recipe data
        formatted_data = ai_helper.format_recipe_for_form(recipe_data)

        if not formatted_data:
            raise HTTPException(status_code=400, detail="Invalid recipe data format")

        temp_id = ai_helper.store_temp_recipe(formatted_data)

        return {
            "temp_id": temp_id,
            "message": "Recipe data stored temporarily",
            "expires_in_hours": 2
        }

    except Exception as e:
        logger.error(f"Error storing temp recipe: {e}")
        raise HTTPException(status_code=500, detail="Error storing recipe data")


# TEMPORARY RECIPE STORAGE ROUTES
@app.get("/temp-recipe/{temp_id}")
async def get_temp_recipe(temp_id: str):
    """Retrieve temporary recipe data for form auto-population"""
    if not ai_available:
        raise HTTPException(status_code=503, detail="AI features not available")

    try:
        recipe_data = ai_helper.get_temp_recipe(temp_id)

        if not recipe_data:
            raise HTTPException(status_code=404, detail="Temporary recipe not found or expired")

        return {"recipe_data": recipe_data}

    except Exception as e:
        logger.error(f"Error retrieving temp recipe: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving recipe data")


@app.delete("/temp-recipe/{temp_id}")
async def delete_temp_recipe(temp_id: str):
    """Delete temporary recipe data (cleanup)"""
    try:
        if not ai_available:
            raise HTTPException(status_code=503, detail="AI features not available")

        from .utils.ai_helper import temp_recipe_storage
        if temp_id in temp_recipe_storage:
            del temp_recipe_storage[temp_id]
            return {"message": "Temporary recipe data deleted"}
        else:
            raise HTTPException(status_code=404, detail="Temporary recipe not found")

    except Exception as e:
        logger.error(f"Error deleting temp recipe: {e}")
        raise HTTPException(status_code=500, detail="Error deleting recipe data")


@app.get("/temp-recipes/cleanup")
async def cleanup_temp_recipes():
    """Manual cleanup of expired temporary recipes (admin utility)"""
    if not ai_available:
        raise HTTPException(status_code=503, detail="AI features not available")

    try:
        ai_helper._cleanup_expired_temp_recipes()
        # Access the temp storage from the ai_helper module
        from .utils.ai_helper import temp_recipe_storage
        remaining_count = len(temp_recipe_storage)
        return {
            "message": "Cleanup completed",
            "remaining_temp_recipes": remaining_count
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Error during cleanup")


# Photo management utility routes
@app.post("/admin/fix-photo-urls")
async def fix_existing_photo_urls(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))):
    """Fix existing photo URLs in the database - Admin/Owner only"""
    if not db_available:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Find all recipes with old photo URLs
        recipes_with_photos = list(db.recipes.find({"photo_url": {"$exists": True, "$ne": None}}))

        fixed_count = 0
        for recipe in recipes_with_photos:
            old_url = recipe.get("photo_url")
            if old_url and old_url.startswith("/static/photos/"):
                # Extract filename and create new URL
                filename = old_url.replace("/static/photos/", "")
                new_url = f"http://127.0.0.1:8000/photos/{filename}"

                # Update the recipe
                db.recipes.update_one(
                    {"_id": recipe["_id"]},
                    {"$set": {"photo_url": new_url}}
                )
                fixed_count += 1

        return {
            "message": f"Fixed {fixed_count} photo URLs",
            "total_recipes_checked": len(recipes_with_photos)
        }

    except Exception as e:
        logger.error(f"Error fixing photo URLs: {e}")
        raise HTTPException(status_code=500, detail="Error fixing photo URLs")


# Utility routes
@app.get("/measuring-units")
async def get_measuring_units():
    return {"units": [unit.value for unit in MeasuringUnit]}


@app.get("/genres")
async def get_genres():
    return {"genres": [genre.value for genre in Genre]}


# if os.path.exists("frontend/build"):
#     app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
#
#
#     @app.get("/")
#     async def serve_root():
#         """Explicitly handle root route"""
#         import os
#         index_path = "/app/frontend/build/index.html"
#         logger.info(f"Root route: serving {index_path}")
#
#         if os.path.exists(index_path):
#             return FileResponse(index_path)
#         else:
#             raise HTTPException(status_code=404, detail=f"Root: Index not found at {index_path}")
#
#     # Serve React app for all non-API routes
#     @app.get("/{full_path:path}")
#     async def serve_react_app(full_path: str):
#         """Debug version to see what's happening"""
#         import os
#
#         # Log what we're trying to serve
#         logger.info(f"Serving request for path: '{full_path}'")
#
#         # Don't serve React app for API routes
#         if full_path.startswith(("api", "docs", "redoc", "health", "photos")):
#             logger.info(f"Blocking API route: {full_path}")
#             raise HTTPException(status_code=404, detail="Not found")
#
#         # Check build directory
#         app_dir = "/app"
#         build_dir = os.path.join(app_dir, "frontend", "build")
#         index_path = os.path.join(build_dir, "index.html")
#
#         logger.info(f"Looking for files in: {build_dir}")
#         logger.info(f"Index file path: {index_path}")
#         logger.info(f"Index file exists: {os.path.exists(index_path)}")
#
#         # List what's actually in the build directory
#         try:
#             build_contents = os.listdir(build_dir)
#             logger.info(f"Build directory contents: {build_contents}")
#         except Exception as e:
#             logger.error(f"Error listing build directory: {e}")
#             raise HTTPException(status_code=404, detail=f"Build directory error: {e}")
#
#         # Always serve index.html for now (for debugging)
#         if os.path.exists(index_path):
#             logger.info(f"Serving index.html from: {index_path}")
#             return FileResponse(index_path)
#         else:
#             raise HTTPException(status_code=404, detail=f"Index file not found at: {index_path}")


    # Root route - serve React app
    # @app.get("/")
    # async def read_root():
    #     return FileResponse("frontend/build/index.html")


# Health check endpoint (useful for deployment)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OnDEK Recipe App is running!"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
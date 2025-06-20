from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from enum import Enum
import re
from statistics import mean
import logging

# AI imports
from .utils.ai_helper import recipe_ai_helper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ondek Recipe API",
    description="A comprehensive recipe management API with AI integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Type"],
    max_age=600,
)

# Database connection
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
security = HTTPBearer()

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.ondek_recipe

    # Create default owner user if it doesn't exist
    if db.users.count_documents({"username": "owner"}) == 0:
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        owner_user = {
            "username": "owner",
            "email": "owner@ondekrecipe.com",
            "password": hashed_password,
            "role": "owner",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        db.users.insert_one(owner_user)
        print("✅ Default owner user created successfully!")
    else:
        # Make sure password is correct for owner user
        owner = db.users.find_one({"username": "owner"})
        is_valid = False
        try:
            is_valid = bcrypt.checkpw("admin123".encode('utf-8'), owner["password"].encode('utf-8'))
        except Exception:
            is_valid = False

        if not is_valid:
            # Update owner password
            hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.users.update_one(
                {"username": "owner"},
                {"$set": {"password": hashed_password, "updated_at": datetime.now()}}
            )
            print("✅ Owner password reset to 'admin123'")
        else:
            print("✅ Owner user exists with correct password")

    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    raise


# Pydantic Models
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


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


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


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


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class AIMessage(BaseModel):
    message: str


class AIResponse(BaseModel):
    response: str


# RATINGS AND FAVORITES MODELS
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
    rating_breakdown: dict


class FavoriteCreate(BaseModel):
    recipe_id: str


class FavoriteResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    created_at: datetime


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


# AI-RELATED MODELS
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime


class RecipeSearchRequest(BaseModel):
    ingredients: List[str]


# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
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


# BASIC ROUTES
@app.get("/")
async def root():
    return {"message": "Welcome to the Ondek Recipe API! 🍳"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


# AUTHENTICATION ROUTES
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
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
    # Debug logging
    print(f"Login attempt for username: {user.username}")

    db_user = db.users.find_one({"username": user.username})
    if not db_user:
        print(f"User not found: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debug logging
    print(f"Found user: {db_user['username']}, role: {db_user['role']}")

    if not verify_password(user.password, db_user["password"]):
        print(f"Password verification failed for: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debug logging
    print(f"Password verification successful for: {user.username}")

    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": db_user["username"]}, expires_delta=access_token_expires
    )

    user_response = UserResponse(
        id=str(db_user["_id"]),
        username=db_user["username"],
        email=db_user["email"],
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


# RECIPE ROUTES
@app.post("/recipes", response_model=RecipeResponse)
async def create_recipe(recipe: Recipe, current_user: dict = Depends(get_current_user)):
    recipe_doc = {
        "recipe_name": recipe.recipe_name,
        "description": recipe.description,
        "ingredients": [ing.dict() for ing in recipe.ingredients],
        "instructions": recipe.instructions,
        "serving_size": recipe.serving_size,
        "genre": recipe.genre.value,
        "prep_time": recipe.prep_time or 0,
        "cook_time": recipe.cook_time or 0,
        "notes": recipe.notes or [],
        "dietary_restrictions": recipe.dietary_restrictions or [],
        "created_by": current_user["username"],
        "created_at": datetime.utcnow()
    }

    result = db.recipes.insert_one(recipe_doc)
    recipe_doc["_id"] = result.inserted_id

    ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]
    return RecipeResponse(
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
        created_at=recipe_doc["created_at"]
    )


@app.get("/recipes", response_model=List[RecipeResponse])
async def get_recipes(
        search: Optional[str] = Query(None, description="Search recipes by name or ingredients"),
        genre: Optional[Genre] = Query(None, description="Filter by genre"),
        skip: int = Query(0, ge=0, description="Number of recipes to skip"),
        limit: int = Query(100, ge=1, le=100, description="Number of recipes to return")
):
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
            created_at=recipe_doc["created_at"]
        ))

    return recipes


@app.get("/recipes/{recipe_id}", response_model=EnhancedRecipeResponse)
async def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe_doc:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]
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
        created_at=recipe_doc["created_at"]
    )


@app.put("/recipes/{recipe_id}", response_model=EnhancedRecipeResponse)
async def update_recipe(
        recipe_id: str,
        recipe_update: RecipeUpdate,
        current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    # Check if recipe exists and user has permission
    existing_recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if user is the creator or has admin/owner role
    if (existing_recipe["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this recipe")

    # Build update document
    update_doc = {}

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

    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Update the recipe
    result = db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Return updated recipe
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
        created_at=updated_recipe["created_at"]
    )


@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    try:
        recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe_doc:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if (recipe_doc["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    return {"message": "Recipe deleted successfully"}


# RATING ROUTES
@app.post("/recipes/{recipe_id}/ratings", response_model=RatingResponse)
async def create_rating(
        recipe_id: str,
        rating_data: RatingCreate,
        current_user: dict = Depends(get_current_user)
):
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
@app.post("/recipes/{recipe_id}/favorite", response_model=FavoriteResponse)
async def add_to_favorites(recipe_id: str, current_user: dict = Depends(get_current_user)):
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
    result = db.favorites.delete_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not in favorites")

    return {"message": "Recipe removed from favorites"}


@app.get("/users/me/favorites", response_model=List[RecipeResponse])
async def get_user_favorites(current_user: dict = Depends(get_current_user)):
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
                recipes.append(RecipeResponse(
                    id=str(recipe_doc["_id"]),
                    recipe_name=recipe_doc["recipe_name"],
                    ingredients=ingredients,
                    instructions=recipe_doc["instructions"],
                    serving_size=recipe_doc["serving_size"],
                    genre=Genre(recipe_doc["genre"]),
                    created_by=recipe_doc["created_by"],
                    created_at=recipe_doc["created_at"]
                ))
        except InvalidId:
            continue

    return recipes


@app.get("/recipes/{recipe_id}/favorite-status")
async def check_favorite_status(recipe_id: str, current_user: dict = Depends(get_current_user)):
    favorite = db.favorites.find_one({
        "recipe_id": recipe_id,
        "user_id": str(current_user["_id"])
    })

    return {"is_favorited": favorite is not None}


# AI CHAT ROUTES
@app.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Main AI chat endpoint for recipe-related conversations
    """
    try:
        if not recipe_ai_helper.is_configured():
            return ChatResponse(
                response="AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key.",
                timestamp=datetime.now()
            )

        # Process the chat message
        response_text = await recipe_ai_helper.chat_about_recipes(
            user_message=chat_data.message,
            conversation_history=chat_data.conversation_history
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
    """
    Get recipe suggestions based on available ingredients
    """
    try:
        if not recipe_ai_helper.is_configured():
            return {"response": "AI features are currently unavailable."}

        suggestions = recipe_ai_helper.get_recipe_suggestions_by_ingredients(
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
    """
    Search recipes using natural language processing
    """
    try:
        if not recipe_ai_helper.is_configured():
            return {"recipes": [], "message": "AI features are currently unavailable."}

        # Extract search criteria from the query
        search_criteria = recipe_ai_helper.extract_search_intent(query)

        # Search for recipes
        if search_criteria:
            recipes = recipe_ai_helper.search_recipes_by_criteria(search_criteria)
        else:
            # If no specific criteria, return a general set
            recipes = recipe_ai_helper.get_recipes_data(limit=10)

        return {
            "recipes": recipes,
            "criteria_found": search_criteria,
            "total_found": len(recipes)
        }

    except Exception as e:
        logger.error(f"Error in AI recipe search: {e}")
        return {"recipes": [], "message": "Error processing search query"}


@app.get("/ai/recipe/{recipe_id}/details")
async def get_recipe_details_ai(
        recipe_id: str,
        current_user: dict = Depends(get_current_user)
):
    """
    Get detailed recipe information formatted for AI responses
    """
    try:
        recipe = recipe_ai_helper.get_recipe_by_id(recipe_id)

        if not recipe:
            return {"error": "Recipe not found"}

        return {"recipe": recipe}

    except Exception as e:
        logger.error(f"Error getting recipe details: {e}")
        return {"error": "Error retrieving recipe details"}


@app.get("/ai/status")
async def ai_status():
    """
    Check AI service status
    """
    return {
        "ai_configured": recipe_ai_helper.is_configured(),
        "model": recipe_ai_helper.model if recipe_ai_helper.is_configured() else None,
        "database_connected": db is not None
    }


# USER MANAGEMENT ROUTES
@app.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))):
    users = []
    for user_doc in db.users.find():
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


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: str,
        user_update: UserUpdate,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    if (str(user_doc["_id"]) != str(current_user["_id"]) and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to edit this user")

    update_doc = {"updated_at": datetime.now()}

    # Update email if provided
    if user_update.email is not None:
        if not validate_email(user_update.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        existing_user = db.users.find_one({"email": user_update.email, "_id": {"$ne": ObjectId(user_id)}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        update_doc["email"] = user_update.email

    # Update username if provided
    if user_update.username is not None:
        # Skip update if username is the same
        if user_update.username != user_doc.get("username"):
            # Check if username is already taken
            existing_user = db.users.find_one({"username": user_update.username, "_id": {"$ne": ObjectId(user_id)}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already registered")
            update_doc["username"] = user_update.username

    # Update first_name if provided
    if user_update.first_name is not None:
        update_doc["first_name"] = user_update.first_name

    # Update last_name if provided
    if user_update.last_name is not None:
        update_doc["last_name"] = user_update.last_name

    # Update password if provided
    if user_update.password is not None:
        update_doc["password"] = hash_password(user_update.password)

    # Only perform update if there are changes
    if len(update_doc) > 1:  # More than just "updated_at"
        print(f"Updating user {user_id} with: {update_doc}")
        result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_doc})
        print(f"Update result: {result.modified_count} documents modified")

    # Get the updated user document
    updated_user = db.users.find_one({"_id": ObjectId(user_id)})

    # Return updated user information
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
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    try:
        user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    if user_doc["role"] == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete owner user")

    if user_doc["role"] == "admin" and current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete admin users")

    db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}


# UTILITY ROUTES
@app.get("/measuring-units")
async def get_measuring_units():
    return {"units": [unit.value for unit in MeasuringUnit]}


@app.get("/genres")
async def get_genres():
    return {"genres": [genre.value for genre in Genre]}


# ADMIN UTILITY ROUTES
@app.get("/admin/update-recipe-times", include_in_schema=False)
async def update_recipe_times():
    """Add prep_time and cook_time fields to all recipes that don't have them"""
    try:
        result = db.recipes.update_many(
            {"prep_time": {"$exists": False}},  # Find recipes without prep_time
            {"$set": {"prep_time": 0, "cook_time": 0}}  # Set default values
        )

        return {
            "success": True,
            "modified_count": result.modified_count,
            "matched_count": result.matched_count,
            "message": f"Updated {result.modified_count} recipes"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/admin/reset-owner-password", include_in_schema=False)
async def reset_owner_password():
    owner = db.users.find_one({"username": "owner"})

    if not owner:
        # Create owner user
        hashed_password = hash_password("admin123")
        owner_user = {
            "username": "owner",
            "email": "owner@ondekrecipe.com",
            "password": hashed_password,
            "role": "owner",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        db.users.insert_one(owner_user)
        return {"message": "Owner user created successfully"}
    else:
        # Update owner password
        hashed_password = hash_password("admin123")
        db.users.update_one(
            {"username": "owner"},
            {"$set": {"password": hashed_password, "updated_at": datetime.now()}}
        )
        return {"message": "Owner password reset successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
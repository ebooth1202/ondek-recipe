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
from pydantic import BaseModel, EmailStr
from enum import Enum
import re

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Ondek Recipe API",
    description="A comprehensive recipe management API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
security = HTTPBearer()

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.ondek_recipe
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
    PINCH = "pinch"
    DASH = "dash"


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: MeasuringUnit


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class RecipeCreate(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre


class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    serving_size: Optional[int] = None
    genre: Optional[Genre] = None


class RecipeResponse(BaseModel):
    id: str
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre
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


# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


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


# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Ondek Recipe API! 🍳"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


# Authentication routes
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user already exists
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only allow owner/admin to create admin users
    if user.role in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Cannot create admin users through registration")

    # Hash password and create user
    hashed_password = hash_password(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role.value,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = db.users.insert_one(user_doc)

    return UserResponse(
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user_doc["created_at"]
    )


@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = db.users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
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
        role=UserRole(current_user["role"]),
        created_at=current_user["created_at"]
    )


# Recipe routes
@app.post("/recipes", response_model=RecipeResponse)
async def create_recipe(recipe: RecipeCreate, current_user: dict = Depends(get_current_user)):
    recipe_doc = {
        "recipe_name": recipe.recipe_name,
        "ingredients": [ingredient.dict() for ingredient in recipe.ingredients],
        "instructions": recipe.instructions,
        "serving_size": recipe.serving_size,
        "genre": recipe.genre.value,
        "created_by": current_user["username"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = db.recipes.insert_one(recipe_doc)

    return RecipeResponse(
        id=str(result.inserted_id),
        recipe_name=recipe.recipe_name,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        serving_size=recipe.serving_size,
        genre=recipe.genre,
        created_by=current_user["username"],
        created_at=recipe_doc["created_at"]
    )


@app.get("/recipes", response_model=List[RecipeResponse])
async def get_recipes(
        search: Optional[str] = Query(None, description="Search recipes by name or ingredients"),
        genre: Optional[Genre] = Query(None, description="Filter by genre"),
        skip: int = Query(0, ge=0, description="Number of recipes to skip"),
        limit: int = Query(100, ge=1, le=100, description="Number of recipes to return")
):
    # Build query
    query = {}

    if search:
        query["$or"] = [
            {"recipe_name": {"$regex": search, "$options": "i"}},
            {"ingredients.name": {"$regex": search, "$options": "i"}}
        ]

    if genre:
        query["genre"] = genre.value

    # Execute query
    cursor = db.recipes.find(query).skip(skip).limit(limit).sort("recipe_name", 1)
    recipes = []

    for recipe_doc in cursor:
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

    return recipes


@app.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: str):
    try:
        recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe_doc:
        raise HTTPException(status_code=404, detail="Recipe not found")

    ingredients = [Ingredient(**ing) for ing in recipe_doc["ingredients"]]

    return RecipeResponse(
        id=str(recipe_doc["_id"]),
        recipe_name=recipe_doc["recipe_name"],
        ingredients=ingredients,
        instructions=recipe_doc["instructions"],
        serving_size=recipe_doc["serving_size"],
        genre=Genre(recipe_doc["genre"]),
        created_by=recipe_doc["created_by"],
        created_at=recipe_doc["created_at"]
    )


@app.put("/recipes/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
        recipe_id: str,
        recipe_update: RecipeUpdate,
        current_user: dict = Depends(get_current_user)
):
    try:
        recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    if not recipe_doc:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if user can edit this recipe
    if (recipe_doc["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to edit this recipe")

    # Build update document
    update_doc = {"updated_at": datetime.now()}

    if recipe_update.recipe_name is not None:
        update_doc["recipe_name"] = recipe_update.recipe_name
    if recipe_update.ingredients is not None:
        update_doc["ingredients"] = [ing.dict() for ing in recipe_update.ingredients]
    if recipe_update.instructions is not None:
        update_doc["instructions"] = recipe_update.instructions
    if recipe_update.serving_size is not None:
        update_doc["serving_size"] = recipe_update.serving_size
    if recipe_update.genre is not None:
        update_doc["genre"] = recipe_update.genre.value

    # Update recipe
    db.recipes.update_one({"_id": ObjectId(recipe_id)}, {"$set": update_doc})

    # Return updated recipe
    updated_recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
    ingredients = [Ingredient(**ing) for ing in updated_recipe["ingredients"]]

    return RecipeResponse(
        id=str(updated_recipe["_id"]),
        recipe_name=updated_recipe["recipe_name"],
        ingredients=ingredients,
        instructions=updated_recipe["instructions"],
        serving_size=updated_recipe["serving_size"],
        genre=Genre(updated_recipe["genre"]),
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

    # Check if user can delete this recipe
    if (recipe_doc["created_by"] != current_user["username"] and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    return {"message": "Recipe deleted successfully"}


# User management routes
@app.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))):
    users = []
    for user_doc in db.users.find():
        users.append(UserResponse(
            id=str(user_doc["_id"]),
            username=user_doc["username"],
            email=user_doc["email"],
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

    # Check permissions
    if (str(user_doc["_id"]) != str(current_user["_id"]) and
            current_user["role"] not in ["admin", "owner"]):
        raise HTTPException(status_code=403, detail="Not authorized to edit this user")

    # Build update document
    update_doc = {"updated_at": datetime.now()}

    if user_update.email is not None:
        # Check if email already exists
        existing_user = db.users.find_one({"email": user_update.email, "_id": {"$ne": ObjectId(user_id)}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        update_doc["email"] = user_update.email

    if user_update.password is not None:
        update_doc["password"] = hash_password(user_update.password)

    # Update user
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_doc})

    # Return updated user
    updated_user = db.users.find_one({"_id": ObjectId(user_id)})
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
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

    # Prevent deletion of owner
    if user_doc["role"] == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete owner user")

    # Prevent admin from deleting another admin unless they're owner
    if user_doc["role"] == "admin" and current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete admin users")

    db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}


# AI Agent routes
@app.post("/ai/chat", response_model=AIResponse)
async def ai_chat(message: AIMessage, current_user: dict = Depends(get_current_user)):
    # Simple AI response for now - you can integrate with OpenAI later
    response_text = f"Thanks for your message: '{message.message}'. This is a placeholder response. AI integration coming soon!"

    return AIResponse(response=response_text)


# Utility routes
@app.get("/measuring-units")
async def get_measuring_units():
    return {"units": [unit.value for unit in MeasuringUnit]}


@app.get("/genres")
async def get_genres():
    return {"genres": [genre.value for genre in Genre]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
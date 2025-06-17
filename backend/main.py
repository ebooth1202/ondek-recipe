from fastapi import FastAPI, HTTPException, Depends, status
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
    allow_origins=["http://localhost:3000"],  # React frontend URL
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


class RecipeCreate(BaseModel):
    recipe_name: str
    ingredients: List[Ingredient]
    instructions: List[str]
    serving_size: int
    genre: Genre


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
    user_doc["_id"] = result.inserted_id

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
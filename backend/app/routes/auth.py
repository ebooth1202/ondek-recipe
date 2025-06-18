from fastapi import APIRouter, HTTPException, Depends, status, Response
from datetime import timedelta
import re

from ..database import db, Database
from ..models.user import UserCreate, UserLogin, UserResponse, UserRole, Token
from ..utils.password import hash_password, verify_password
from ..middleware.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user"""
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Prevent creating admin/owner users through registration
    if user.role in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Cannot create admin users through registration")

    hashed_password = hash_password(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role.value,
        "created_at": Database.get_current_datetime(),
        "updated_at": Database.get_current_datetime()
    }

    result = db.users.insert_one(user_doc)

    return UserResponse(
        id=str(result.inserted_id),
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user_doc["created_at"]
    )


@router.post("/login", response_model=Token)
async def login(response: Response, user: UserLogin):
    """Login and get access token"""
    # Debugging
    print(f"Attempting to log in user: {user.username}")

    db_user = db.users.find_one({"username": user.username})

    if not db_user:
        print(f"User {user.username} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debugging
    print(f"Found user: {db_user['username']} with role: {db_user['role']}")

    if not verify_password(user.password, db_user["password"]):
        print(f"Password verification failed for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate access token
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": db_user["username"]}, expires_delta=access_token_expires
    )

    # Debugging
    print(f"Login successful for user: {db_user['username']}")

    user_response = UserResponse(
        id=str(db_user["_id"]),
        username=db_user["username"],
        email=db_user["email"],
        role=UserRole(db_user["role"]),
        created_at=db_user["created_at"]
    )

    # Set a cookie with the token
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,  # 24 hours
        expires=86400,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get information about the current logged-in user"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=UserRole(current_user["role"]),
        created_at=current_user["created_at"]
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout the current user"""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}
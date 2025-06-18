# backend/app/database.py - Enhanced version with new indexes and default user setup

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from .config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    client = None
    database = None

    @classmethod
    def initialize(cls):
        try:
            cls.client = MongoClient(
                settings.mongo_uri,
                server_api=ServerApi('1')
            )
            cls.database = cls.client.ondek_recipe

            # Test connection
            cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas!")

            # Create indexes
            cls._create_indexes()

            # Create default admin user if it doesn't exist
            cls._ensure_default_user()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    def _create_indexes(cls):
        """Create database indexes for better performance"""
        try:
            # Recipe indexes
            cls.database.recipes.create_index("recipe_name")
            cls.database.recipes.create_index("genre")
            cls.database.recipes.create_index("created_by")
            cls.database.recipes.create_index([("recipe_name", "text"), ("instructions", "text")])

            # User indexes
            cls.database.users.create_index("username", unique=True)
            cls.database.users.create_index("email", unique=True)

            # Rating indexes
            cls.database.ratings.create_index("recipe_id")
            cls.database.ratings.create_index("user_id")
            cls.database.ratings.create_index([("recipe_id", 1), ("user_id", 1)],
                                              unique=True)  # Prevent duplicate ratings
            cls.database.ratings.create_index("rating")
            cls.database.ratings.create_index("created_at")

            # Favorite indexes
            cls.database.favorites.create_index("recipe_id")
            cls.database.favorites.create_index("user_id")
            cls.database.favorites.create_index([("recipe_id", 1), ("user_id", 1)],
                                                unique=True)  # Prevent duplicate favorites
            cls.database.favorites.create_index("created_at")

            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    @classmethod
    def _ensure_default_user(cls):
        """Ensure default owner user exists"""
        import bcrypt

        try:
            # Check if owner user exists
            owner = cls.database.users.find_one({"username": "owner"})

            if not owner:
                logger.info("Creating default owner user")
                # Hash the password
                hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                # Create owner user
                owner_user = {
                    "username": "owner",
                    "email": "owner@ondekrecipe.com",
                    "password": hashed_password,
                    "role": "owner",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }

                cls.database.users.insert_one(owner_user)
                logger.info("Default owner user created successfully")
            else:
                logger.info("Default owner user already exists")
        except Exception as e:
            logger.error(f"Error ensuring default user: {e}")

    @classmethod
    def get_database(cls):
        return cls.database

    @classmethod
    def get_current_datetime(cls):
        """Get current datetime for consistent datetime usage"""
        return datetime.now()


# Initialize database connection
Database.initialize()
db = Database.get_database()
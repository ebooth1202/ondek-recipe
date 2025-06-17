# backend/app/database.py - Enhanced version with new indexes

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from .config import settings
import logging

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
    def get_database(cls):
        return cls.database


# Initialize database connection
Database.initialize()
db = Database.get_database()
# backend/app/database.py - Enhanced version with better production handling

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from .config import settings
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class Database:
    client = None
    database = None
    connection_retries = 0
    max_retries = 3

    @classmethod
    def initialize(cls):
        """Initialize database connection with retry logic"""
        for attempt in range(cls.max_retries):
            try:
                cls._connect()
                break
            except Exception as e:
                cls.connection_retries += 1
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < cls.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Max database connection retries exceeded")
                    raise

    @classmethod
    def _connect(cls):
        """Establish database connection"""
        if not settings.mongo_uri:
            raise Exception("MONGO_URI or MONGODB_URL environment variable not set")

        cls.client = MongoClient(
            settings.mongo_uri,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,  # 10 second connection timeout
            maxPoolSize=50,  # Maximum connection pool size
            retryWrites=True,
            retryReads=True
        )

        # Test connection
        cls.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas!")

        # Get database
        cls.database = cls.client[settings.database_name]

        # Create indexes
        cls._create_indexes()

        # Create default admin user if it doesn't exist
        cls._ensure_default_user()

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
            cls.database.ratings.create_index([("recipe_id", 1), ("user_id", 1)], unique=True)
            cls.database.ratings.create_index("rating")
            cls.database.ratings.create_index("created_at")

            # Favorite indexes
            cls.database.favorites.create_index("recipe_id")
            cls.database.favorites.create_index("user_id")
            cls.database.favorites.create_index([("recipe_id", 1), ("user_id", 1)], unique=True)
            cls.database.favorites.create_index("created_at")

            # Issue tracking indexes
            cls.database.issues.create_index("type")
            cls.database.issues.create_index("severity")
            cls.database.issues.create_index("status")
            cls.database.issues.create_index("user_info.user_id")
            cls.database.issues.create_index("created_at")
            cls.database.issues.create_index([("type", 1), ("status", 1)])

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
                logger.info("Default login: username='owner', password='admin123'")
            else:
                logger.info("Default owner user already exists")
        except Exception as e:
            logger.error(f"Error ensuring default user: {e}")

    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls.database is None:
            logger.warning("Database not initialized")
            return None
        return cls.database

    @classmethod
    def is_connected(cls):
        """Check if database is connected"""
        if not cls.client or not cls.database:
            return False
        try:
            cls.client.admin.command('ping')
            return True
        except:
            return False

    @classmethod
    def get_current_datetime(cls):
        """Get current datetime for consistent datetime usage"""
        return datetime.now()


# Initialize database connection
try:
    Database.initialize()
    db = Database.get_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    db = None
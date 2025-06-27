import os
import logging
import json
import re
import io
import tempfile
import csv
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import requests
from urllib.parse import quote_plus, urlparse

# Set up logger FIRST
logger = logging.getLogger(__name__)

# Note: AI helper will be imported lazily to avoid circular imports
AI_HELPER_AVAILABLE = True  # Assume available until proven otherwise

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup4 not available - will use basic text extraction")

# Try to import database with error handling
try:
    try:
        from ..database import db

        logger.info("Database imported successfully from app.database")
    except ImportError:
        try:
            from app.database import db

            logger.info("Database imported successfully from app.database")
        except ImportError:
            try:
                from database import db

                logger.info("Database imported successfully using absolute import")
            except ImportError:
                import sys

                current_dir = os.path.dirname(os.path.abspath(__file__))

                potential_paths = [
                    os.path.join(current_dir, '..'),
                    os.path.join(current_dir, '..', '..'),
                    os.path.join(current_dir, '..', '..', '..'),
                ]

                database_found = False
                for path in potential_paths:
                    abs_path = os.path.abspath(path)
                    if abs_path not in sys.path:
                        sys.path.insert(0, abs_path)

                    try:
                        if os.path.exists(os.path.join(abs_path, 'database.py')):
                            from database import db

                            logger.info(f"Database imported successfully from path: {abs_path}")
                            database_found = True
                            break
                        elif os.path.exists(os.path.join(abs_path, 'app', 'database.py')):
                            from app.database import db

                            logger.info(f"Database imported successfully from app.database at: {abs_path}")
                            database_found = True
                            break
                    except ImportError:
                        continue

                if not database_found:
                    raise ImportError("Could not locate database module in any expected location")

    db_available = True
except Exception as e:
    logger.error(f"Failed to import database in tools: {e}")
    logger.warning("Internal recipe search and ingredient suggestions will not work without database access")


    # Creating a mock database for development/fallback
    class MockRecipeCollection:
        @staticmethod
        def find(query=None, *args, **kwargs):
            return MockCursor()

        @staticmethod
        def count_documents(query=None):
            return 0


    class MockCursor:
        def limit(self, n):
            return []

        def __iter__(self):
            return iter([])

        def __list__(self):
            return []


    class MockDatabase:
        recipes = MockRecipeCollection()
        favorites = MockRecipeCollection()


    db = MockDatabase()
    db_available = False
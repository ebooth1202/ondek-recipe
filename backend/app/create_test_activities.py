#!/usr/bin/env python3
"""
Script to create test activities in the database.
Run this once to populate your activities collection with sample data.
"""

from datetime import datetime, timedelta
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import your database connection
from app.database import db


def create_test_activities():
    """Create sample activities for testing the Activity Tracker interface"""

    # Check if activities collection already has data
    existing_count = db.activities.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Activities collection already has {existing_count} activities.")
        response = input("Do you want to add more test activities? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    # Sample test activities
    test_activities = [
        {
            "activity_type": "login",
            "category": "authentication",
            "user_info": {
                "user_id": "test_user_1",
                "username": "john_doe",
                "role": "user",
                "email": "john@example.com"
            },
            "context": {
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "browser": "Chrome",
                "page": "/auth/login"
            },
            "details": {
                "method": "POST",
                "endpoint": "/auth/login",
                "response_status": 200,
                "response_time_ms": 150
            },
            "description": "User logged in successfully",
            "tags": ["auto-tracked", "authentication", "post"],
            "metadata": {"tracked_by": "middleware", "version": "1.0"},
            "created_at": datetime.now() - timedelta(hours=2)
        },
        {
            "activity_type": "create_recipe",
            "category": "recipe_management",
            "user_info": {
                "user_id": "test_user_1",
                "username": "john_doe",
                "role": "user",
                "email": "john@example.com"
            },
            "context": {
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "browser": "Chrome",
                "page": "/recipes"
            },
            "details": {
                "method": "POST",
                "endpoint": "/recipes",
                "resource_id": "64a1b2c3d4e5f6789abcdef0",
                "resource_type": "recipe",
                "resource_name": "Chocolate Chip Cookies",
                "response_status": 201,
                "response_time_ms": 340
            },
            "description": "Created recipe: Chocolate Chip Cookies",
            "tags": ["auto-tracked", "recipe_management", "post"],
            "metadata": {"tracked_by": "middleware", "version": "1.0"},
            "created_at": datetime.now() - timedelta(hours=1, minutes=30)
        },
        {
            "activity_type": "search_recipes",
            "category": "search_browse",
            "user_info": {
                "user_id": "test_user_2",
                "username": "jane_smith",
                "role": "user",
                "email": "jane@example.com"
            },
            "context": {
                "ip_address": "192.168.1.101",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "browser": "Safari",
                "page": "/recipes"
            },
            "details": {
                "method": "GET",
                "endpoint": "/recipes",
                "query_params": {"search": "chocolate", "genre": "dessert"},
                "response_status": 200,
                "response_time_ms": 95
            },
            "description": "Searched for recipes",
            "tags": ["auto-tracked", "search_browse", "get"],
            "metadata": {"tracked_by": "middleware", "version": "1.0"},
            "created_at": datetime.now() - timedelta(minutes=45)
        },
        {
            "activity_type": "view_admin",
            "category": "admin_action",
            "user_info": {
                "user_id": "admin_user_1",
                "username": "admin_user",
                "role": "admin",
                "email": "admin@example.com"
            },
            "context": {
                "ip_address": "192.168.1.50",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "browser": "Chrome",
                "page": "/admin/activities"
            },
            "details": {
                "method": "GET",
                "endpoint": "/activities",
                "response_status": 200,
                "response_time_ms": 120
            },
            "description": "Accessed admin area",
            "tags": ["auto-tracked", "admin_action", "get"],
            "metadata": {"tracked_by": "middleware", "version": "1.0"},
            "created_at": datetime.now() - timedelta(minutes=10)
        },
        {
            "activity_type": "favorite_recipe",
            "category": "recipe_management",
            "user_info": {
                "user_id": "test_user_2",
                "username": "jane_smith",
                "role": "user",
                "email": "jane@example.com"
            },
            "context": {
                "ip_address": "192.168.1.101",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "browser": "Safari",
                "page": "/recipes/64a1b2c3d4e5f6789abcdef0"
            },
            "details": {
                "method": "POST",
                "endpoint": "/recipes/64a1b2c3d4e5f6789abcdef0/favorite",
                "resource_id": "64a1b2c3d4e5f6789abcdef0",
                "resource_type": "recipe",
                "response_status": 200,
                "response_time_ms": 85
            },
            "description": "Favorited recipe: Chocolate Chip Cookies",
            "tags": ["auto-tracked", "recipe_management", "post"],
            "metadata": {"tracked_by": "middleware", "version": "1.0"},
            "created_at": datetime.now() - timedelta(minutes=5)
        }
    ]

    # Insert test activities
    try:
        print("📝 Creating test activities...")
        result = db.activities.insert_many(test_activities)
        print(f"✅ Successfully created {len(result.inserted_ids)} test activities!")

        # Verify the collection was created
        count = db.activities.count_documents({})
        print(f"📊 Total activities in database: {count}")

        # List collections to confirm
        collections = db.list_collection_names()
        print(f"📁 Available collections: {collections}")

    except Exception as e:
        print(f"❌ Error creating test activities: {e}")

    print("\n🎉 You can now test your Activity Tracker interface!")
    print("🔗 Go to: http://localhost:3000/admin/activities")


if __name__ == "__main__":
    create_test_activities()
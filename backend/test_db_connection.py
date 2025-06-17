import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import sys


def test_mongodb_connection():
    # Load environment variables from .env file
    load_dotenv()

    # Get MongoDB URI from environment variable
    mongo_uri = os.getenv('MONGO_URI')

    if not mongo_uri:
        print("❌ Error: MONGO_URI environment variable not found!")
        print("Make sure you have a .env file with your MongoDB connection string.")
        return False

    try:
        print("🔄 Attempting to connect to MongoDB Atlas...")

        # Create MongoDB client with server API version
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))

        # Test the connection by pinging the server
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")

        # Get database
        db = client.ondek_recipe
        print(f"📊 Connected to database: {db.name}")

        # Test creating a collection and inserting a test document
        test_collection = db.test_connection
        test_doc = {"test": "connection successful", "timestamp": "2024"}

        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")

        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document cleaned up")

        # List existing collections
        collections = db.list_collection_names()
        if collections:
            print(f"📋 Existing collections: {collections}")
        else:
            print("📋 No collections found (this is normal for a new database)")

        # Close connection
        client.close()
        print("🔒 Connection closed successfully")

        return True

    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your MONGO_URI in the .env file")
        print("2. Ensure your IP address is whitelisted in MongoDB Atlas")
        print("3. Verify your username and password are correct")
        print("4. Check your internet connection")
        return False


def create_initial_collections():
    """Create initial collections with proper structure"""
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')

    if not mongo_uri:
        print("❌ MONGO_URI not found")
        return False

    try:
        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        db = client.ondek_recipe

        # Create collections
        collections_to_create = ['users', 'recipes']

        for collection_name in collections_to_create:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
            else:
                print(f"📋 Collection already exists: {collection_name}")

        # Create indexes for better performance
        print("🔄 Creating indexes...")

        # User indexes
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)

        # Recipe indexes
        db.recipes.create_index("recipe_name")
        db.recipes.create_index("genre")
        db.recipes.create_index("created_by")

        print("✅ Indexes created successfully")

        # Create default owner user if it doesn't exist
        existing_owner = db.users.find_one({"role": "owner"})
        if not existing_owner:
            from datetime import datetime
            import bcrypt

            # Hash default password
            password = "admin123"  # Change this!
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            owner_user = {
                "username": "owner",
                "email": "owner@ondek.com",
                "password": hashed_password.decode('utf-8'),
                "role": "owner",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            result = db.users.insert_one(owner_user)
            print(f"✅ Created default owner user with ID: {result.inserted_id}")
            print("⚠️  Default login: username='owner', password='admin123'")
            print("🔐 IMPORTANT: Change the default password immediately!")
        else:
            print("👤 Owner user already exists")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error creating collections: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Ondek Recipe App - Database Connection Test")
    print("=" * 50)

    # Test basic connection
    if test_mongodb_connection():
        print("\n" + "=" * 50)
        print("🔧 Setting up initial database structure...")

        # Create collections and initial data
        if create_initial_collections():
            print("\n✅ Database setup completed successfully!")
            print("🎉 Your Ondek Recipe app is ready to run!")
        else:
            print("\n❌ Failed to setup database structure")
            sys.exit(1)
    else:
        print("\n❌ Database connection failed")
        sys.exit(1)
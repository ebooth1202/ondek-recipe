# test_ai.py
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

print("Testing AI helper import...")

try:
    print("1. Testing module import...")
    import app.utils.ai_helper as ai_module

    print("✅ Module import successful!")

    print("2. Testing class import...")
    from app.utils.ai_helper import AIHelper

    print("✅ Class import successful!")

    print("3. Testing instance import...")
    from app.utils.ai_helper import ai_helper

    print("✅ Instance import successful!")
    print(f"AI Helper configured: {ai_helper.is_configured()}")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
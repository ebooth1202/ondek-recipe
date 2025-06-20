# test_instance.py
import sys
import os

sys.path.insert(0, os.getcwd())

try:
    print("Importing AIHelper class...")
    from app.utils.ai_helper import AIHelper

    print("✅ Class imported successfully!")

    print("Creating AIHelper instance...")
    ai_helper = AIHelper()
    print("✅ Instance created successfully!")
    print(f"AI Helper configured: {ai_helper.is_configured()}")

except Exception as e:
    print(f"❌ Error creating instance: {e}")
    import traceback

    traceback.print_exc()
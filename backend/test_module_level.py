# test_module_level.py
import sys
import os

sys.path.insert(0, os.getcwd())

try:
    print("Testing module-level execution...")

    # Let's manually execute what's in the ai_helper.py file
    print("1. Importing os...")
    import os

    print("2. Importing logging...")
    import logging

    print("3. Creating logger...")
    logger = logging.getLogger(__name__)

    print("4. Defining class...")


    class AIHelper:
        def __init__(self):
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.model = "gpt-3.5-turbo"

        def is_configured(self) -> bool:
            return bool(self.api_key)

        async def chat_about_recipes(self, user_message: str, conversation_history=None) -> str:
            if not self.is_configured():
                return "AI features require OpenAI API key configuration."
            return "AI response placeholder"

        def get_recipe_suggestions_by_ingredients(self, ingredients) -> str:
            if not self.is_configured():
                return "AI features require OpenAI API key configuration."
            return "Recipe suggestions placeholder"


    print("5. Creating instance...")
    ai_helper = AIHelper()
    print("✅ Module-level instance created successfully!")

    print("6. Testing the actual module import...")
    import app.utils.ai_helper

    print("✅ Module imported!")

    print("7. Checking if ai_helper exists in module...")
    if hasattr(app.utils.ai_helper, 'ai_helper'):
        print("✅ ai_helper found in module!")
        helper = app.utils.ai_helper.ai_helper
        print(f"Helper configured: {helper.is_configured()}")
    else:
        print("❌ ai_helper NOT found in module!")
        print(f"Module attributes: {dir(app.utils.ai_helper)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

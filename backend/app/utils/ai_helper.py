# backend/app/utils/ai_helper.py - Clean working version

import os
from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime, timedelta
import uuid
import re

logger = logging.getLogger(__name__)

# Try to import database with error handling
try:
    from app.database import db

    logger.info("Database imported successfully in AI helper")
    db_available_local = True
except Exception as e:
    logger.error(f"Failed to import database in AI helper: {e}")
    db = None
    db_available_local = False

# Temporary storage for recipe data
temp_recipe_storage = {}


class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        self.model = "gpt-3.5-turbo"

        # External search configuration
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.allowed_external_search = False

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key and self.client)

    def store_temp_recipe(self, recipe_data: Dict[str, Any]) -> str:
        """Store temporary recipe data and return a unique ID"""
        temp_id = str(uuid.uuid4())
        temp_recipe_storage[temp_id] = {
            "data": recipe_data,
            "timestamp": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=2)
        }
        self._cleanup_expired_temp_recipes()
        return temp_id

    def get_temp_recipe(self, temp_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve temporary recipe data by ID"""
        if temp_id in temp_recipe_storage:
            stored = temp_recipe_storage[temp_id]
            if datetime.now() < stored["expires_at"]:
                return stored["data"]
            else:
                del temp_recipe_storage[temp_id]
        return None

    def _cleanup_expired_temp_recipes(self):
        """Remove expired temporary recipe entries"""
        current_time = datetime.now()
        expired_keys = [
            key for key, value in temp_recipe_storage.items()
            if current_time >= value["expires_at"]
        ]
        for key in expired_keys:
            del temp_recipe_storage[key]

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None) -> str:
        """Main chat function for recipe-related conversations"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        try:
            # Extract search criteria
            search_criteria = self.extract_search_intent(user_message)
            logger.info(f"Extracted search criteria: {search_criteria}")

            # Search internal database
            internal_recipes = []
            if search_criteria:
                internal_recipes = self.search_recipes_by_criteria(search_criteria)
                logger.info(f"Found {len(internal_recipes)} recipes matching criteria: {search_criteria}")
            else:
                internal_recipes = self.get_recipes_data(limit=10)
                logger.info(f"No specific criteria found, returning {len(internal_recipes)} general recipes")

            # If we found recipes, generate response based on them
            if internal_recipes and len(internal_recipes) > 0:
                return await self._generate_internal_response(user_message, internal_recipes, search_criteria)
            else:
                return await self._generate_no_results_response(user_message, search_criteria)

        except Exception as e:
            logger.error(f"Error in chat_about_recipes: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."

    async def _generate_internal_response(self, user_message: str, recipes: List[Dict],
                                          search_criteria: Dict[str, Any]) -> str:
        """Generate response based on internal database recipes"""
        try:
            # Build a description of what we found
            criteria_description = ""
            if search_criteria:
                if search_criteria.get('ingredient') and search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('ingredient'):
                    criteria_description = f"recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes"

            if criteria_description:
                response = f"I found {len(recipes)} {criteria_description} in your database."
            else:
                response = f"I found {len(recipes)} recipes in your database."

            # Add recipe buttons
            for recipe in recipes[:5]:  # Limit to 5 recipes
                button = self.create_recipe_view_button(recipe)
                response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error generating internal response: {e}")
            return f"I found {len(recipes)} recipes in your database, but encountered an error formatting the response."

    async def _generate_no_results_response(self, user_message: str, search_criteria: Dict[str, Any]) -> str:
        """Generate response when no recipes are found"""
        criteria_text = ""
        if search_criteria:
            criteria_parts = []
            if search_criteria.get('ingredient'):
                criteria_parts.append(f"ingredient '{search_criteria['ingredient']}'")
            if search_criteria.get('genre'):
                criteria_parts.append(f"genre '{search_criteria['genre']}'")

            if criteria_parts:
                criteria_text = f" matching {' and '.join(criteria_parts)}"

        response = f"I couldn't find any recipes in your database{criteria_text}."
        response += "\n\nWould you like me to help you create a new recipe or search for recipes online?"

        # Add creation button
        button = self.create_recipe_action_button()
        response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

        return response

    def get_recipe_suggestions_by_ingredients(self, ingredients: List[str]) -> str:
        """Get recipe suggestions based on available ingredients"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        try:
            # Search for recipes containing any of the ingredients
            recipes_with_ingredients = []
            for ingredient in ingredients:
                matching_recipes = self.search_recipes_by_criteria({"ingredient": ingredient})
                recipes_with_ingredients.extend(matching_recipes)

            # Remove duplicates
            unique_recipes = {recipe['id']: recipe for recipe in recipes_with_ingredients}.values()

            if not unique_recipes:
                response = f"I couldn't find any recipes in your database that use {', '.join(ingredients)}."
                button = self.create_recipe_action_button()
                response += f"\n\nWould you like to create a new recipe?\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            # Format response
            recipe_list = ""
            for recipe in list(unique_recipes)[:5]:  # Limit to 5 suggestions
                recipe_list += f"\n• **{recipe['name']}** - {recipe['genre']} recipe for {recipe['serving_size']} people"
                recipe_list += f"\n  Total time: {recipe['total_time']} minutes"

            response = f"Great! I found some recipes in your database that use {', '.join(ingredients)}:\n{recipe_list}"
            return response

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {e}")
            return "Sorry, I couldn't retrieve recipe suggestions at the moment."

    def extract_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Extract search criteria from user message"""
        if not self.is_configured():
            return {}

        try:
            prompt = f"""
            Analyze this user message about recipes and extract search criteria as JSON:
            User message: "{user_message}"

            Extract any of these criteria if mentioned:
            - genre: breakfast, lunch, dinner, snack, dessert, appetizer
            - ingredient: any ingredient name mentioned
            - name: recipe name if specifically mentioned

            Return only valid JSON like:
            {{"genre": "dessert", "ingredient": "chocolate"}}
            {{"ingredient": "chicken"}}
            {{"genre": "breakfast"}}

            If no criteria found, return: {{}}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()
            logger.info(f"AI search extraction result: {result}")

            try:
                criteria = json.loads(result)
                logger.info(f"Parsed search criteria: {criteria}")
                return criteria
            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI search criteria: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return {}

    def search_recipes_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search recipes based on specific criteria"""
        try:
            if db is None:
                logger.warning("Database not available")
                return []

            query = {}

            if "genre" in criteria:
                query["genre"] = {"$regex": criteria["genre"], "$options": "i"}

            if "ingredient" in criteria:
                escaped_ingredient = re.escape(criteria["ingredient"])
                query["ingredients.name"] = {"$regex": f"\\b{escaped_ingredient}\\b", "$options": "i"}

            if "name" in criteria:
                query["recipe_name"] = {"$regex": criteria["name"], "$options": "i"}

            logger.info(f"MongoDB query: {query}")
            recipes = list(db.recipes.find(query).limit(20))
            logger.info(f"Found {len(recipes)} recipes from database")

            return [self._format_recipe_for_ai(recipe) for recipe in recipes]

        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []

    def get_recipes_data(self, limit: int = 50) -> List[Dict]:
        """Retrieve recipes from database for AI context"""
        try:
            if db is None:
                logger.warning("Database not available")
                return []

            recipes = list(db.recipes.find().limit(limit))
            processed_recipes = []

            for recipe in recipes:
                processed_recipe = {
                    "id": str(recipe["_id"]),
                    "name": recipe["recipe_name"],
                    "description": recipe.get("description", ""),
                    "genre": recipe["genre"],
                    "serving_size": recipe["serving_size"],
                    "prep_time": recipe.get("prep_time", 0),
                    "cook_time": recipe.get("cook_time", 0),
                    "total_time": (recipe.get("prep_time", 0) + recipe.get("cook_time", 0)),
                    "ingredients": [
                        f"{ing['quantity']} {ing['unit']} {ing['name']}"
                        for ing in recipe["ingredients"]
                    ],
                    "instructions": recipe["instructions"],
                    "notes": recipe.get("notes", []),
                    "dietary_restrictions": recipe.get("dietary_restrictions", []),
                    "created_by": recipe["created_by"],
                    "created_at": recipe["created_at"].strftime("%Y-%m-%d") if recipe.get("created_at") else ""
                }
                processed_recipes.append(processed_recipe)

            return processed_recipes
        except Exception as e:
            logger.error(f"Error retrieving recipes: {e}")
            return []

    def _format_recipe_for_ai(self, recipe: Dict) -> Dict:
        """Format recipe for AI consumption"""
        return {
            "id": str(recipe["_id"]),
            "name": recipe["recipe_name"],
            "description": recipe.get("description", ""),
            "genre": recipe["genre"],
            "serving_size": recipe["serving_size"],
            "prep_time": recipe.get("prep_time", 0),
            "cook_time": recipe.get("cook_time", 0),
            "total_time": (recipe.get("prep_time", 0) + recipe.get("cook_time", 0)),
            "ingredients": [
                f"{ing['quantity']} {ing['unit']} {ing['name']}"
                for ing in recipe["ingredients"]
            ],
            "instructions": recipe["instructions"],
            "notes": recipe.get("notes", []),
            "dietary_restrictions": recipe.get("dietary_restrictions", []),
            "created_by": recipe["created_by"],
            "created_at": recipe["created_at"].strftime("%Y-%m-%d") if recipe.get("created_at") else ""
        }

    def create_recipe_view_button(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Create action button to view a specific recipe"""
        return {
            "type": "action_button",
            "text": f"View {recipe['name']}",
            "action": "view_recipe",
            "url": f"/recipes/{recipe['id']}",
            "metadata": {
                "recipe_id": recipe['id'],
                "recipe_name": recipe['name'],
                "type": "view_recipe"
            }
        }

    def create_recipe_action_button(self, recipe_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create action button data for recipe creation"""
        button_data = {
            "type": "action_button",
            "text": "Add Recipe",
            "action": "create_recipe"
        }

        if recipe_data:
            temp_id = self.store_temp_recipe(recipe_data)
            button_data["url"] = f"/add-recipe?temp_id={temp_id}"
            button_data["text"] = "Add This Recipe"
        else:
            button_data["url"] = "/add-recipe"

        return button_data


# Global AI helper instance
ai_helper = AIHelper()
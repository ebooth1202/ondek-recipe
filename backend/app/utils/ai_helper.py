# backend/app/utils/ai_helper.py
import os
from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import re
from datetime import datetime
from ..database import db
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key and self.client)

    def get_recipes_data(self, limit: int = 50) -> List[Dict]:
        """Retrieve recipes from database for AI context"""
        try:
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

    def search_recipes_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search recipes based on specific criteria"""
        try:
            query = {}

            # Handle different search criteria
            if "genre" in criteria:
                query["genre"] = {"$regex": criteria["genre"], "$options": "i"}

            if "ingredient" in criteria:
                query["ingredients.name"] = {"$regex": criteria["ingredient"], "$options": "i"}

            if "name" in criteria:
                query["recipe_name"] = {"$regex": criteria["name"], "$options": "i"}

            if "max_time" in criteria:
                # Search by total time
                query["$expr"] = {
                    "$lte": [
                        {"$add": [{"$ifNull": ["$prep_time", 0]}, {"$ifNull": ["$cook_time", 0]}]},
                        criteria["max_time"]
                    ]
                }

            if "dietary_restrictions" in criteria:
                query["dietary_restrictions"] = {"$in": criteria["dietary_restrictions"]}

            recipes = list(db.recipes.find(query).limit(20))
            return [self._format_recipe_for_ai(recipe) for recipe in recipes]

        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict]:
        """Get specific recipe by ID"""
        try:
            if not ObjectId.is_valid(recipe_id):
                return None

            recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
            if recipe:
                return self._format_recipe_for_ai(recipe)
            return None
        except Exception as e:
            logger.error(f"Error getting recipe by ID: {e}")
            return None

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

    def extract_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Extract search criteria from user message using AI"""
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
            - max_time: maximum cooking time in minutes if mentioned
            - dietary_restrictions: gluten_free, dairy_free, egg_free

            Return only valid JSON like:
            {{"genre": "dinner", "ingredient": "chicken", "max_time": 30}}

            If no criteria found, return: {{}}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI search criteria: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return {}

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None) -> str:
        """Main chat function for recipe-related conversations"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        try:
            # Extract search criteria from user message
            search_criteria = self.extract_search_intent(user_message)

            # Get relevant recipes based on criteria or general collection
            if search_criteria:
                relevant_recipes = self.search_recipes_by_criteria(search_criteria)
                context_type = "searched"
            else:
                # Get a sample of recipes for general context
                relevant_recipes = self.get_recipes_data(limit=10)
                context_type = "general"

            # Build context for AI
            recipe_context = ""
            if relevant_recipes:
                recipe_context = "\n\nAvailable recipes in the database:\n"
                for i, recipe in enumerate(relevant_recipes[:10], 1):  # Limit to 10 for context
                    recipe_context += f"\n{i}. **{recipe['name']}** ({recipe['genre']})\n"
                    recipe_context += f"   - Serves: {recipe['serving_size']}\n"
                    recipe_context += f"   - Total time: {recipe['total_time']} minutes\n"
                    recipe_context += f"   - Key ingredients: {', '.join(recipe['ingredients'][:3])}...\n"
                    if recipe['dietary_restrictions']:
                        recipe_context += f"   - Dietary: {', '.join(recipe['dietary_restrictions'])}\n"
                    recipe_context += f"   - Created by: {recipe['created_by']}\n"

            # Build conversation messages
            system_message = f"""You are a helpful cooking assistant for the Ondek Recipe app. You have access to a recipe database and can help users find recipes, answer cooking questions, and provide culinary advice.

Current context: You have access to {len(relevant_recipes)} recipes from the database ({context_type} based on user query).

Guidelines:
- Be friendly, helpful, and enthusiastic about cooking
- When recommending recipes, mention specific ones from the database with their names
- Include practical cooking tips and suggestions
- If asked about specific recipes, provide detailed information including ingredients and instructions
- Help users find recipes based on their preferences, dietary restrictions, or available ingredients
- If no recipes match their criteria, suggest alternatives or ask clarifying questions

{recipe_context}

Remember: Always be helpful and provide specific recipe recommendations when appropriate!"""

            messages = [{"role": "system", "content": system_message}]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Limit history to last 6 messages

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error in chat_about_recipes: {e}")
            return f"I'm sorry, I encountered an error while processing your request. Please try again."

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
                return f"I couldn't find any recipes in the database that use {', '.join(ingredients)}. Would you like me to suggest some general recipes or help you with something else?"

            # Format response
            recipe_list = ""
            for recipe in list(unique_recipes)[:5]:  # Limit to 5 suggestions
                recipe_list += f"\n• **{recipe['name']}** - {recipe['genre']} recipe for {recipe['serving_size']} people"
                recipe_list += f"\n  Total time: {recipe['total_time']} minutes"

            response = f"Great! I found some recipes in our database that use {', '.join(ingredients)}:\n{recipe_list}"
            response += f"\n\nWould you like me to provide the full recipe details for any of these?"

            return response

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {e}")
            return "Sorry, I couldn't retrieve recipe suggestions at the moment."

    # Legacy methods for backward compatibility
    async def generate_recipe_suggestions(self, ingredients: List[str]) -> str:
        """Generate recipe suggestions based on available ingredients (legacy method)"""
        return self.get_recipe_suggestions_by_ingredients(ingredients)

    async def help_with_recipe_creation(self, user_input: str) -> str:
        """Help users with recipe creation questions (legacy method)"""
        return await self.chat_about_recipes(user_input)

    async def suggest_recipe_improvements(self, recipe_name: str, ingredients: List[Dict],
                                          instructions: List[str]) -> str:
        """Suggest improvements for an existing recipe"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        ingredients_text = "\n".join(
            [f"- {ing['quantity']} {ing['unit']} {ing['name']}" for ing in ingredients])
        instructions_text = "\n".join([f"{i + 1}. {inst}" for i, inst in enumerate(instructions)])

        prompt = f"""
        Please review this recipe and suggest improvements:

        Recipe Name: {recipe_name}

        Ingredients:
        {ingredients_text}

        Instructions:
        {instructions_text}

        Provide suggestions for:
        1. Ingredient improvements or substitutions
        2. Technique improvements
        3. Flavor enhancements
        4. Timing optimizations
        5. Presentation tips

        Keep suggestions practical and helpful.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert chef reviewing recipes and providing constructive improvement suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error analyzing recipe: {e}")
            return f"Sorry, I couldn't analyze the recipe right now. Error: {str(e)}"

    async def general_cooking_chat(self, message: str,
                                   conversation_history: Optional[List[Dict]] = None) -> str:
        """Handle general cooking-related conversations (legacy method)"""
        return await self.chat_about_recipes(message, conversation_history)

    def parse_recipe_from_text(self, text: str) -> Optional[Dict]:
        """
        Parse a recipe from natural language text
        Returns a dictionary with recipe components
        """
        try:
            # Simple regex patterns to extract recipe components
            recipe_data = {
                "recipe_name": "",
                "ingredients": [],
                "instructions": [],
                "serving_size": 1,
                "genre": "dinner"
            }

            # Extract recipe name (usually first line or after "Recipe:")
            name_patterns = [
                r"Recipe Name?:\s*(.+)",
                r"^(.+?)(?:\n|Ingredients)",
                r"# (.+)"
            ]

            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    recipe_data["recipe_name"] = match.group(1).strip()
                    break

            # Extract ingredients
            ingredients_section = re.search(
                r"Ingredients?:?\s*\n(.*?)(?=Instructions?:|Directions?:|Steps?:|\n\n|\Z)",
                text,
                re.IGNORECASE | re.DOTALL
            )

            if ingredients_section:
                ingredient_lines = ingredients_section.group(1).strip().split('\n')
                for line in ingredient_lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Try to parse quantity, unit, and name
                        ingredient_match = re.match(
                            r'[\-\*]?\s*(\d+(?:\.\d+)?)\s*(\w+)?\s+(.+)',
                            line
                        )
                        if ingredient_match:
                            quantity = float(ingredient_match.group(1))
                            unit = ingredient_match.group(2) or "piece"
                            name = ingredient_match.group(3).strip()

                            recipe_data["ingredients"].append({
                                "name": name,
                                "quantity": quantity,
                                "unit": unit
                            })

            # Extract instructions
            instructions_section = re.search(
                r"(?:Instructions?|Directions?|Steps?):?\s*\n(.*?)(?=Notes?:|\n\n|\Z)",
                text,
                re.IGNORECASE | re.DOTALL
            )

            if instructions_section:
                instruction_lines = instructions_section.group(1).strip().split('\n')
                for line in instruction_lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove numbering and bullets
                        cleaned_line = re.sub(r'^\d+\.\s*|^\-\s*|\*\s*', '', line)
                        if cleaned_line:
                            recipe_data["instructions"].append(cleaned_line)

            # Extract serving size
            serving_match = re.search(r"Serves?:?\s*(\d+)", text, re.IGNORECASE)
            if serving_match:
                recipe_data["serving_size"] = int(serving_match.group(1))

            return recipe_data

        except Exception as e:
            logger.error(f"Error parsing recipe: {e}")
            return None

    def suggest_ingredient_substitutions(self, ingredient_name: str) -> List[str]:
        """Suggest common substitutions for an ingredient"""
        substitutions = {
            "butter": ["margarine", "coconut oil", "vegetable oil", "applesauce"],
            "milk": ["almond milk", "soy milk", "coconut milk", "oat milk"],
            "eggs": ["applesauce", "banana", "flax eggs", "chia eggs"],
            "flour": ["almond flour", "coconut flour", "oat flour", "rice flour"],
            "sugar": ["honey", "maple syrup", "stevia", "brown sugar"],
            "salt": ["sea salt", "kosher salt", "herb salt", "garlic salt"],
            "onion": ["shallots", "green onions", "leeks", "onion powder"],
            "garlic": ["garlic powder", "shallots", "garlic scapes"],
            "lemon juice": ["lime juice", "vinegar", "white wine"],
            "heavy cream": ["coconut cream", "evaporated milk", "cashew cream"]
        }

        ingredient_lower = ingredient_name.lower()
        for key, subs in substitutions.items():
            if key in ingredient_lower:
                return subs

        return ["Check online for substitutions for this ingredient"]


# Global AI helper instance
ai_helper = AIHelper()
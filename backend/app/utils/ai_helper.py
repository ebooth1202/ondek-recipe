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
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"

        # External search configuration
        self.search_api_key = os.getenv("SEARCH_API_KEY")  # For external recipe search APIs
        self.allowed_external_search = False  # Flag to control external searches

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

    def count_recipes_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """Count recipes matching criteria without retrieving them"""
        try:
            query = {}

            if "genre" in criteria:
                query["genre"] = {"$regex": criteria["genre"], "$options": "i"}
            if "ingredient" in criteria:
                query["ingredients.name"] = {"$regex": criteria["ingredient"], "$options": "i"}
            if "name" in criteria:
                query["recipe_name"] = {"$regex": criteria["name"], "$options": "i"}
            if "max_time" in criteria:
                query["$expr"] = {
                    "$lte": [
                        {"$add": [{"$ifNull": ["$prep_time", 0]}, {"$ifNull": ["$cook_time", 0]}]},
                        criteria["max_time"]
                    ]
                }
            if "dietary_restrictions" in criteria:
                query["dietary_restrictions"] = {"$in": criteria["dietary_restrictions"]}

            return db.recipes.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting recipes: {e}")
            return 0

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

    def detect_external_search_request(self, user_message: str) -> bool:
        """Detect if user is requesting external search or giving permission"""
        external_keywords = [
            "search the internet", "look online", "find on web", "search web",
            "yes, search", "go ahead", "please search", "look it up",
            "from the internet", "online recipes", "web search"
        ]

        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in external_keywords)

    def extract_search_parameters(self, user_message: str) -> Dict[str, Any]:
        """Extract specific search parameters from user message"""
        if not self.is_configured():
            return {}

        try:
            prompt = f"""
            Extract search parameters from this user message:
            "{user_message}"

            Look for:
            - specific_websites: any websites mentioned (e.g., "allrecipes.com", "food.com")
            - cuisine_type: specific cuisine mentioned (e.g., "italian", "asian", "mexican")
            - difficulty_level: cooking skill level (e.g., "easy", "beginner", "advanced")
            - meal_type: specific meal types (e.g., "quick meals", "one-pot", "healthy")
            - additional_constraints: any other specific requirements

            Return JSON format:
            {{"specific_websites": ["allrecipes.com"], "cuisine_type": "italian", "difficulty_level": "easy"}}

            If nothing specific found, return: {{}}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse search parameters: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error extracting search parameters: {e}")
            return {}

    async def search_external_recipes(self, criteria: Dict[str, Any],
                                      search_params: Dict[str, Any] = None) -> List[Dict]:
        """Search for recipes from external sources"""
        try:
            # This is a placeholder for external recipe search
            # You would implement actual API calls to recipe websites here

            search_query = self._build_external_search_query(criteria, search_params)

            # Simulate external search results
            external_results = [
                {
                    "name": f"External Recipe for {criteria.get('ingredient', 'cooking')}",
                    "source": search_params.get('specific_websites', ['web'])[0] if search_params else "web",
                    "description": "Found from external search",
                    "url": "https://example.com/recipe",
                    "ingredients": ["Sample ingredients from external source"],
                    "instructions": ["Sample instructions from external source"],
                    "cuisine_type": search_params.get('cuisine_type', 'general') if search_params else "general"
                }
            ]

            return external_results

        except Exception as e:
            logger.error(f"Error in external recipe search: {e}")
            return []

    def _build_external_search_query(self, criteria: Dict[str, Any],
                                     search_params: Dict[str, Any] = None) -> str:
        """Build search query for external APIs"""
        query_parts = []

        if criteria.get('ingredient'):
            query_parts.append(f"recipe {criteria['ingredient']}")
        if criteria.get('genre'):
            query_parts.append(criteria['genre'])
        if criteria.get('name'):
            query_parts.append(criteria['name'])

        if search_params:
            if search_params.get('cuisine_type'):
                query_parts.append(search_params['cuisine_type'])
            if search_params.get('difficulty_level'):
                query_parts.append(search_params['difficulty_level'])

        return " ".join(query_parts) if query_parts else "recipes"

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None) -> str:
        """Enhanced main chat function with internal-first search logic"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        try:
            # Step 1: Always check internal database first
            search_criteria = self.extract_search_intent(user_message)

            # Search internal database
            internal_recipes = []
            recipe_count = 0

            if search_criteria:
                internal_recipes = self.search_recipes_by_criteria(search_criteria)
                recipe_count = self.count_recipes_by_criteria(search_criteria)
            else:
                # For general queries, get a sample
                internal_recipes = self.get_recipes_data(limit=10)
                recipe_count = len(internal_recipes)

            # Step 2: Check if we found relevant recipes internally
            if internal_recipes and recipe_count > 0:
                # We found recipes in the database - provide them
                return await self._generate_internal_response(user_message, internal_recipes,
                                                              conversation_history, search_criteria)

            # Step 3: No recipes found internally - check if user wants external search
            if self.detect_external_search_request(user_message):
                # User has given permission for external search
                search_params = self.extract_search_parameters(user_message)
                external_recipes = await self.search_external_recipes(search_criteria, search_params)

                return await self._generate_external_response(user_message, external_recipes,
                                                              search_criteria, search_params,
                                                              conversation_history)

            # Step 4: Ask for permission to search externally
            return self._generate_permission_request(search_criteria, user_message)

        except Exception as e:
            logger.error(f"Error in chat_about_recipes: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."

    async def _generate_internal_response(self, user_message: str, recipes: List[Dict],
                                          conversation_history: Optional[List[Dict]],
                                          search_criteria: Dict[str, Any]) -> str:
        """Generate response based on internal database recipes"""
        try:
            # Build context for AI
            recipe_context = f"\n\nI found {len(recipes)} recipe(s) in your database:\n"
            for i, recipe in enumerate(recipes[:10], 1):
                recipe_context += f"\n{i}. **{recipe['name']}** ({recipe['genre']})\n"
                recipe_context += f"   - Serves: {recipe['serving_size']}\n"
                recipe_context += f"   - Total time: {recipe['total_time']} minutes\n"
                recipe_context += f"   - Key ingredients: {', '.join(recipe['ingredients'][:3])}...\n"
                if recipe['dietary_restrictions']:
                    recipe_context += f"   - Dietary: {', '.join(recipe['dietary_restrictions'])}\n"
                recipe_context += f"   - Created by: {recipe['created_by']}\n"

            system_message = f"""You are a helpful cooking assistant for the Ondek Recipe app. You have access to the user's personal recipe database and should provide helpful information based on what's available.

IMPORTANT: You are currently working with recipes from the user's personal database only. These are recipes they have saved or created.

Current results: Found {len(recipes)} recipes matching their request.

{recipe_context}

Guidelines:
- Be friendly and enthusiastic about the recipes found in their database
- Provide specific recommendations from their collection
- Include practical cooking tips
- If they want more options, offer to search the internet for additional recipes
- Always prioritize their saved recipes first"""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-6:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating internal response: {e}")
            return "I found recipes in your database, but encountered an error formatting the response."

    async def _generate_external_response(self, user_message: str, external_recipes: List[Dict],
                                          search_criteria: Dict[str, Any], search_params: Dict[str, Any],
                                          conversation_history: Optional[List[Dict]]) -> str:
        """Generate response based on external search results"""
        try:
            if not external_recipes:
                return "I searched the internet as requested, but couldn't find recipes matching your criteria. Would you like to try different search terms or check different websites?"

            # Build context for external results
            external_context = f"\n\nI searched the internet and found these recipes:\n"
            for i, recipe in enumerate(external_recipes[:5], 1):
                external_context += f"\n{i}. **{recipe['name']}** (from {recipe['source']})\n"
                external_context += f"   - {recipe['description']}\n"
                if recipe.get('url'):
                    external_context += f"   - URL: {recipe['url']}\n"

            search_info = ""
            if search_params:
                if search_params.get('specific_websites'):
                    search_info += f"Searched on: {', '.join(search_params['specific_websites'])}\n"
                if search_params.get('cuisine_type'):
                    search_info += f"Cuisine focus: {search_params['cuisine_type']}\n"

            system_message = f"""You are a helpful cooking assistant. The user asked you to search the internet for recipes since nothing was found in their personal database.

External search results: Found {len(external_recipes)} recipes from the internet.
{search_info}

{external_context}

Guidelines:
- Present the external recipes you found
- Mention that these are from the internet, not their personal database
- Ask if they'd like full details for any recipe
- Offer to help them save promising recipes to their database
- Be helpful in explaining the differences between their saved recipes and internet finds"""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-4:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating external response: {e}")
            return "I found some recipes online, but encountered an error presenting them. Please try again."

    def _generate_permission_request(self, search_criteria: Dict[str, Any], user_message: str) -> str:
        """Generate a request for permission to search externally"""
        criteria_text = ""
        if search_criteria:
            criteria_parts = []
            if search_criteria.get('ingredient'):
                criteria_parts.append(f"ingredient '{search_criteria['ingredient']}'")
            if search_criteria.get('genre'):
                criteria_parts.append(f"genre '{search_criteria['genre']}'")
            if search_criteria.get('name'):
                criteria_parts.append(f"recipe name '{search_criteria['name']}'")
            if search_criteria.get('max_time'):
                criteria_parts.append(f"cooking time under {search_criteria['max_time']} minutes")
            if search_criteria.get('dietary_restrictions'):
                criteria_parts.append(f"dietary restrictions: {', '.join(search_criteria['dietary_restrictions'])}")

            if criteria_parts:
                criteria_text = f" matching {' and '.join(criteria_parts)}"

        return f"""I've searched your personal recipe database but couldn't find anything{criteria_text} that matches what you're looking for.

Would you like me to search the internet to find some recipes that match your request? If so, I can help you find options and you can decide if you want to save any of them to your database.

You can also specify:
- Particular websites you'd like me to focus on (like AllRecipes, Food Network, etc.)
- Specific cuisine types or cooking styles
- Difficulty level preferences
- Any other search parameters

Just let me know if you'd like me to proceed with an internet search and any specific preferences you have!"""

    # Keep existing methods for backward compatibility
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
                return f"""I couldn't find any recipes in your database that use {', '.join(ingredients)}.

Would you like me to search the internet for recipes using these ingredients? I can look for:
- Recipes from specific cooking websites
- Particular cuisine styles
- Easy vs. advanced cooking levels
- Quick meal options

Just let me know if you'd like me to search online and any preferences you have!"""

            # Format response
            recipe_list = ""
            for recipe in list(unique_recipes)[:5]:  # Limit to 5 suggestions
                recipe_list += f"\n• **{recipe['name']}** - {recipe['genre']} recipe for {recipe['serving_size']} people"
                recipe_list += f"\n  Total time: {recipe['total_time']} minutes"

            response = f"Great! I found some recipes in your database that use {', '.join(ingredients)}:\n{recipe_list}"
            response += f"\n\nWould you like me to provide the full recipe details for any of these, or would you like me to search the internet for additional options?"

            return response

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {e}")
            return "Sorry, I couldn't retrieve recipe suggestions at the moment."

    # Other existing methods remain the same...
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
        """Parse a recipe from natural language text"""
        try:
            recipe_data = {
                "recipe_name": "",
                "ingredients": [],
                "instructions": [],
                "serving_size": 1,
                "genre": "dinner"
            }

            # Extract recipe name
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
# backend/app/utils/ai_helper.py - Refactored Rupert AI Helper

import os
from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import re
from datetime import datetime, timedelta
import logging
import uuid

# Import the tools
from app.toolset.tools import get_tool, list_available_tools

logger = logging.getLogger(__name__)

# Temporary storage for recipe data and recipe lists
temp_recipe_storage = {}
temp_recipe_lists = {}


class RupertAIHelper:
    """Main AI Helper for Rupert - orchestrates tools and manages conversations"""

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

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key and self.client)

    # === TEMPORARY STORAGE MANAGEMENT ===

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

    def store_temp_recipe_list(self, recipe_list: List[Dict[str, Any]], search_criteria: Dict[str, Any] = None) -> str:
        """Store temporary recipe list and return a unique ID"""
        temp_id = str(uuid.uuid4())
        temp_recipe_lists[temp_id] = {
            "recipes": recipe_list,
            "search_criteria": search_criteria or {},
            "timestamp": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=1)
        }
        self._cleanup_expired_temp_recipe_lists()
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

    def get_temp_recipe_list(self, temp_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve temporary recipe list by ID"""
        if temp_id in temp_recipe_lists:
            stored = temp_recipe_lists[temp_id]
            if datetime.now() < stored["expires_at"]:
                return stored
            else:
                del temp_recipe_lists[temp_id]
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

    def _cleanup_expired_temp_recipe_lists(self):
        """Remove expired temporary recipe list entries"""
        current_time = datetime.now()
        expired_keys = [
            key for key, value in temp_recipe_lists.items()
            if current_time >= value["expires_at"]
        ]
        for key in expired_keys:
            del temp_recipe_lists[key]

    # === INTENT DETECTION ===

    def _is_capability_question(self, user_message: str) -> bool:
        """Detect if the user is asking about Rupert's capabilities"""
        user_lower = user_message.lower()
        capability_indicators = [
            "are you able to", "can you", "do you have the ability to", "are you capable of",
            "do you support", "can you search", "do you search", "are you able", "can rupert",
            "what can you do", "what are you capable of", "do you look up", "do you find",
            "are you connected to", "do you have access to", "can you access",
            "what sites", "what websites", "which sites", "which websites"
        ]
        return any(indicator in user_lower for indicator in capability_indicators)

    def _detect_external_search_request(self, user_message: str) -> bool:
        """Detect if user is requesting external search"""
        external_keywords = [
            "search the internet", "look online", "find on web", "search web",
            "yes, search", "go ahead", "please search", "look it up",
            "from the internet", "online recipes", "web search",
            "recipe online", "find online", "search online", " online"
        ]
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in external_keywords)

    def _detect_recipe_creation_intent(self, user_message: str) -> Optional[str]:
        """Detect if user wants help creating a recipe"""
        creation_keywords = [
            "help me create", "help me add", "how to create", "how to add",
            "want to create", "want to add", "need to create", "need to add",
            "help creating", "help adding", "create a recipe", "add a recipe",
            "like to add"
        ]
        user_lower = user_message.lower()
        if any(keyword in user_lower for keyword in creation_keywords):
            return "help_create"
        return None

    def _is_recipe_related_query(self, user_message: str, search_criteria: Dict[str, Any]) -> bool:
        """Determine if the user's message is actually recipe-related"""
        if self._is_capability_question(user_message):
            return False

        if search_criteria:
            return True

        recipe_keywords = [
            "recipe", "cook", "cooking", "bake", "baking", "ingredient", "ingredients",
            "meal", "food", "dish", "kitchen", "eat", "eating", "dinner", "lunch",
            "breakfast", "snack", "dessert", "appetizer", "cuisine", "culinary"
        ]

        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in recipe_keywords)

    # === SEARCH CRITERIA EXTRACTION ===

    def extract_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Extract search criteria from user message using AI"""
        if not self.is_configured() or self._is_capability_question(user_message):
            return {}

        try:
            prompt = f"""
            Analyze this user message about recipes and extract search criteria as JSON:
            User message: "{user_message}"

            IMPORTANT: Only extract criteria if the user is actually asking to FIND or SEARCH for recipes.

            Extract any of these criteria if mentioned:
            - genre: breakfast, lunch, dinner, snack, dessert, appetizer
            - ingredient: any ingredient name mentioned (be very specific)
            - name: recipe name if specifically mentioned
            - max_time: maximum cooking time in minutes if mentioned
            - dietary_restrictions: gluten_free, dairy_free, egg_free

            Return only valid JSON like:
            {{"genre": "dessert", "ingredient": "peanut butter"}}
            {{"ingredient": "chicken"}}
            {{"genre": "breakfast"}}

            If no criteria found or if asking about capabilities, return: {{}}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()
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

    def extract_search_parameters(self, user_message: str) -> Dict[str, Any]:
        """Extract specific search parameters from user message"""
        if not self.is_configured():
            return {}

        try:
            prompt = f"""
            Extract search parameters from this user message:
            "{user_message}"

            Look for:
            - specific_websites: any websites mentioned
            - cuisine_type: specific cuisine mentioned
            - difficulty_level: cooking skill level
            - meal_type: specific meal types

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
                return {}

        except Exception as e:
            logger.error(f"Error extracting search parameters: {e}")
            return {}

    # === ACTION BUTTON CREATION ===

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

    # === RESPONSE GENERATION ===

    async def _generate_internal_response(self, user_message: str, recipes: List[Dict],
                                          conversation_history: Optional[List[Dict]],
                                          search_criteria: Dict[str, Any]) -> str:
        """Generate response based on internal database recipes with pagination"""
        try:
            criteria_description = ""
            if search_criteria:
                if search_criteria.get('ingredient') and search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('ingredient'):
                    criteria_description = f"recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes"

            total_recipes = len(recipes)
            show_initial = min(5, total_recipes)

            if criteria_description:
                response = f"I found {total_recipes} {criteria_description} in your database."
            else:
                response = f"I found {total_recipes} recipes in your database."

            # Show first 5 recipes as buttons
            recipes_to_show = recipes[:show_initial]
            for recipe in recipes_to_show:
                button = self.create_recipe_view_button(recipe)
                response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 recipes, add "Show All" button
            if total_recipes > 5:
                temp_id = self.store_temp_recipe_list(recipes, search_criteria)
                show_all_button = {
                    "type": "action_button",
                    "text": f"Show All {total_recipes} Recipes",
                    "action": "show_all_recipes",
                    "metadata": {
                        "temp_id": temp_id,
                        "total_count": total_recipes,
                        "criteria_description": criteria_description
                    }
                }
                response += f"\n\n[ACTION_BUTTON:{json.dumps(show_all_button)}]"

            return response

        except Exception as e:
            logger.error(f"Error generating internal response: {e}")
            return f"I found {len(recipes)} recipes but encountered an error formatting the response."

    async def _generate_external_response(self, user_message: str, external_recipes: List[Dict],
                                          search_criteria: Dict[str, Any], search_params: Dict[str, Any],
                                          conversation_history: Optional[List[Dict]]) -> str:
        """Generate response for external recipe search results"""
        try:
            if not external_recipes:
                response = "I searched the internet but couldn't find recipes matching your criteria."
                button = self.create_recipe_action_button()
                response += f"\n\nOr you can create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            total_recipes = len(external_recipes)
            show_initial = min(5, total_recipes)
            recipes_to_show = external_recipes[:show_initial]

            response = f"I searched the internet and found {total_recipes} recipes! Here are the first {show_initial}:"

            # Add action buttons for external recipes
            for recipe in recipes_to_show:
                formatter_tool = get_tool('format_recipe_data')
                if formatter_tool:
                    formatted_recipe = formatter_tool.execute(recipe)
                    if formatted_recipe:
                        button = self.create_recipe_action_button(formatted_recipe)
                        response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 external recipes, add "Show All" button
            if total_recipes > 5:
                temp_id = self.store_temp_recipe_list(external_recipes, search_criteria)
                show_all_button = {
                    "type": "action_button",
                    "text": f"Show All {total_recipes} External Recipes",
                    "action": "show_all_external_recipes",
                    "metadata": {
                        "temp_id": temp_id,
                        "total_count": total_recipes,
                        "source": "external"
                    }
                }
                response += f"\n\n[ACTION_BUTTON:{json.dumps(show_all_button)}]"

            return response

        except Exception as e:
            logger.error(f"Error generating external response: {e}")
            return "I found some recipes online, but encountered an error presenting them."

    async def _generate_general_conversation_response(self, user_message: str,
                                                      conversation_history: Optional[List[Dict]]) -> str:
        """Generate response for general, non-recipe conversation"""
        try:
            if self._is_capability_question(user_message):
                return self._generate_capability_response(user_message)

            system_message = """You are Rupert, a friendly cooking assistant for the Ondek Recipe app. 

            The user has sent you a message that doesn't seem to be specifically about recipes or cooking. 
            Respond naturally and conversationally like a helpful cooking assistant would.

            Keep responses conversational and warm."""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-4:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Add recipe button if appropriate
            if self._should_show_add_recipe_button(user_message, ai_response):
                button = self.create_recipe_action_button()
                ai_response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return ai_response

        except Exception as e:
            logger.error(f"Error generating general conversation response: {e}")
            return "Hey there! I'm Rupert, your cooking assistant. How can I help you with your culinary adventures today?"

    def _generate_capability_response(self, user_message: str) -> str:
        """Generate response for capability questions"""
        user_lower = user_message.lower()

        # Check for specific external sites mentioned
        external_sites = {
            "pinterest": "Pinterest",
            "allrecipes": "AllRecipes",
            "food.com": "Food.com",
            "food network": "Food Network",
            "epicurious": "Epicurious"
        }

        mentioned_site = None
        for site_key, site_name in external_sites.items():
            if site_key in user_lower:
                mentioned_site = site_name
                break

        if mentioned_site:
            response = f"""Yes, I can search for recipes on the internet, including {mentioned_site}!

Here's what I can do:
• Search various recipe websites including {mentioned_site}, AllRecipes, Food Network, and more
• Find recipes with specific ingredients or dietary restrictions
• Look for recipes by cuisine type or difficulty level
• Help you discover new cooking ideas from across the web

Would you like me to search for something specific? Just tell me what kind of recipe you're interested in!"""
        else:
            response = """Yes, I can search for recipes on the internet! I have the ability to look up recipes from various popular cooking websites including:

• Pinterest
• AllRecipes 
• Food Network
• Food.com
• Epicurious
• And many other recipe sites

Here's what I can help you with:
• Search for recipes with specific ingredients
• Find recipes by cuisine type
• Look for recipes based on dietary restrictions
• Find easy recipes for beginners or advanced recipes for experienced cooks

Would you like me to search for something specific?"""

        return response

    def _should_show_add_recipe_button(self, user_message: str, ai_response: str) -> bool:
        """Determine if we should show an 'Add Recipe' button"""
        add_recipe_keywords = [
            "add recipe", "create recipe", "new recipe", "save recipe",
            "how to add", "help me create", "want to add", "need to create"
        ]

        user_lower = user_message.lower()
        response_lower = ai_response.lower()

        return any(keyword in user_lower for keyword in add_recipe_keywords) or \
            ("recipe" in response_lower and ("ingredients:" in response_lower or "instructions:" in response_lower))

    # === ACTION HANDLERS ===

    def handle_show_all_recipes_action(self, temp_id: str) -> str:
        """Handle the 'show all recipes' action"""
        try:
            stored_data = self.get_temp_recipe_list(temp_id)
            if not stored_data:
                return "Sorry, the recipe list has expired. Please search again."

            recipes = stored_data["recipes"]
            search_criteria = stored_data.get("search_criteria", {})

            criteria_description = ""
            if search_criteria:
                if search_criteria.get('ingredient') and search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('ingredient'):
                    criteria_description = f"recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes"

            response = f"Here are all {len(recipes)} {criteria_description}:"

            for recipe in recipes:
                button = self.create_recipe_view_button(recipe)
                response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error handling show all recipes action: {e}")
            return "Sorry, I encountered an error retrieving the full recipe list."

    # === MAIN CHAT FUNCTION ===

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None,
                                 action_type: Optional[str] = None,
                                 action_metadata: Optional[Dict] = None) -> str:
        """Main chat function - orchestrates tools and manages conversation flow"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        try:
            # Handle special actions first
            if action_type == "show_all_recipes" and action_metadata and action_metadata.get("temp_id"):
                return self.handle_show_all_recipes_action(action_metadata["temp_id"])

            # Check if this is a capability question first
            if self._is_capability_question(user_message):
                return await self._generate_general_conversation_response(user_message, conversation_history)

            # Check for recipe creation intent
            creation_intent = self._detect_recipe_creation_intent(user_message)
            if creation_intent == "help_create":
                button = self.create_recipe_action_button()
                return f"I'd be happy to help you create a new recipe! Click the button below to get started.\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # Extract search criteria
            search_criteria = self.extract_search_intent(user_message)
            is_recipe_related = self._is_recipe_related_query(user_message, search_criteria)

            # Search internal database if we have criteria
            internal_recipes = []
            if search_criteria and is_recipe_related:
                db_search_tool = get_tool('search_internal_recipes')
                if db_search_tool:
                    internal_recipes = db_search_tool.execute(search_criteria)

            # Handle different scenarios
            if self._detect_external_search_request(user_message):
                # User specifically requested external search
                search_params = self.extract_search_parameters(user_message)
                external_search_tool = get_tool('search_external_recipes')
                if external_search_tool:
                    external_recipes = external_search_tool.execute(search_criteria, search_params)
                    return await self._generate_external_response(user_message, external_recipes,
                                                                  search_criteria, search_params,
                                                                  conversation_history)

            elif internal_recipes and len(internal_recipes) > 0:
                # We found recipes in the database
                return await self._generate_internal_response(user_message, internal_recipes,
                                                              conversation_history, search_criteria)

            elif search_criteria and is_recipe_related:
                # No internal recipes found, offer external search
                response = f"I couldn't find any recipes in your database"

                if search_criteria.get('ingredient') or search_criteria.get('genre'):
                    response += " matching your criteria."
                    response += "\n\nWould you like me to search the internet to find some recipes that match your request?"
                else:
                    response += "."
                    response += "\n\nWould you like me to search the internet for recipes?"

                button = self.create_recipe_action_button()
                response += f"\n\nOr create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            else:
                # Handle general conversation
                return await self._generate_general_conversation_response(user_message, conversation_history)

        except Exception as e:
            logger.error(f"Error in chat_about_recipes: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."

    # === INGREDIENT-BASED SUGGESTIONS ===

    def get_recipe_suggestions_by_ingredients(self, ingredients: List[str]) -> str:
        """Get recipe suggestions based on available ingredients"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        try:
            suggestion_tool = get_tool('get_ingredient_suggestions')
            if not suggestion_tool:
                return "Recipe suggestion tool not available."

            unique_recipes = suggestion_tool.execute(ingredients)

            if not unique_recipes:
                response = f"""I couldn't find any recipes in your database that use {', '.join(ingredients)}.

Would you like me to search the internet for recipes using these ingredients?"""
                button = self.create_recipe_action_button()
                response += f"\n\nOr create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            # Apply pagination
            total_recipes = len(unique_recipes)
            show_initial = min(5, total_recipes)
            recipes_to_show = unique_recipes[:show_initial]

            response = f"Great! I found {total_recipes} recipes in your database that use {', '.join(ingredients)}."

            # Add action buttons for shown recipes
            for recipe in recipes_to_show:
                button = self.create_recipe_view_button(recipe)
                response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 recipes, add "Show All" button
            if total_recipes > 5:
                search_criteria = {"ingredients_used": ingredients}
                temp_id = self.store_temp_recipe_list(unique_recipes, search_criteria)
                show_all_button = {
                    "type": "action_button",
                    "text": f"Show All {total_recipes} Recipes",
                    "action": "show_all_recipes",
                    "metadata": {
                        "temp_id": temp_id,
                        "total_count": total_recipes,
                        "criteria_description": f"recipes using {', '.join(ingredients)}"
                    }
                }
                response += f"\n\n[ACTION_BUTTON:{json.dumps(show_all_button)}]"

            return response

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {e}")
            return "Sorry, I couldn't retrieve recipe suggestions at the moment."

    # === FILE PARSING ===

    async def parse_recipe_file(self, file_content: bytes, filename: str, file_type: str, file_extension: str) -> \
    Optional[Dict]:
        """Parse recipe file using the file parsing tool"""
        try:
            file_parser = get_tool('parse_recipe_file')
            if not file_parser:
                return None

            parsing_result = file_parser.execute(file_content, filename, file_type, file_extension)

            if parsing_result and parsing_result.get('parsed_text'):
                # Use AI to extract recipe data from parsed text
                recipe_data = await self._parse_recipe_from_text_advanced(
                    parsing_result['parsed_text'],
                    source_info=f"Uploaded file: {filename}"
                )

                parsing_result['recipe_data'] = recipe_data
                return parsing_result

            return parsing_result

        except Exception as e:
            logger.error(f"Error parsing recipe file: {e}")
            return None

    async def _parse_recipe_from_text_advanced(self, text_content: str, source_info: Optional[str] = None) -> Optional[
        Dict[str, Any]]:
        """Advanced recipe parsing from text using AI"""
        try:
            if not self.is_configured() or len(text_content) < 50:
                return None

            system_prompt = """You are a recipe extraction specialist. Extract complete recipe information and return as JSON.

Extract the following information:
{
  "recipe_name": "string (required)",
  "description": "string (optional)",
  "ingredients": [
    {
      "name": "ingredient name",
      "quantity": number,
      "unit": "cup|tablespoon|teaspoon|ounce|pound|gram|piece|whole|stick|pinch|dash"
    }
  ],
  "instructions": ["step 1", "step 2", ...],
  "serving_size": number (default 4),
  "genre": "breakfast|lunch|dinner|snack|dessert|appetizer",
  "prep_time": number (minutes, 0 if not specified),
  "cook_time": number (minutes, 0 if not specified),
  "notes": ["note 1", "note 2", ...] (optional),
  "dietary_restrictions": ["gluten_free", "dairy_free", "egg_free"] (optional)
}

Return ONLY the JSON object, no other text."""

            user_prompt = f"""Extract recipe information from this text:

Source: {source_info or 'User provided text'}

Text content:
{text_content}

Return the recipe data as JSON only."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )

            result_text = response.choices[0].message.content.strip()

            # Clean up the response
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            try:
                recipe_data = json.loads(result_text)

                # Format the extracted data using the formatter tool
                formatter_tool = get_tool('format_recipe_data')
                if formatter_tool:
                    formatted_recipe = formatter_tool.execute(recipe_data)
                    if formatted_recipe:
                        logger.info(f"Successfully extracted recipe: {formatted_recipe.get('recipe_name', 'Unknown')}")
                        return formatted_recipe

                return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                return None

        except Exception as e:
            logger.error(f"Error in advanced recipe parsing: {e}")
            return None


# Global AI helper instance
ai_helper = RupertAIHelper()
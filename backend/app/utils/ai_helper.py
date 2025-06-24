# backend/app/utils/ai_helper.py - Refactored to use ButtonCreatorTool for Website Selection

import os
from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import re
from datetime import datetime, timedelta
import logging
import uuid

# Import the tools with error handling
try:
    from app.toolset.tools import get_tool, list_available_tools

    logger = logging.getLogger(__name__)
    logger.info("Tools imported successfully")
    tools_available = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import tools: {e}")
    logger.error("Make sure the toolset directory exists and has __init__.py file")
    tools_available = False


    # Fallback functions
    def get_tool(tool_name: str):
        logger.warning(f"Tools not available, cannot get tool: {tool_name}")
        return None


    def list_available_tools():
        return []

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

    def are_tools_available(self) -> bool:
        """Check if tools are available"""
        return tools_available

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

    def _extract_previous_search_criteria(self, conversation_history: Optional[List[Dict]]) -> Optional[Dict[str, Any]]:
        """Extract the most recent search criteria from conversation history"""
        if not conversation_history:
            return None

        try:
            # Look through recent messages for user requests that generated recipe results
            for i, message in enumerate(reversed(conversation_history[-10:])):  # Check last 10 messages
                if message.get('role') == 'user':
                    # Try to extract search criteria from this user message
                    criteria = self.extract_search_intent(message.get('content', ''))
                    if criteria:
                        logger.info(f"Found previous search criteria: {criteria}")
                        return criteria

            return None
        except Exception as e:
            logger.error(f"Error extracting previous search criteria: {e}")
            return None

    def _is_capability_question(self, user_message: str) -> bool:
        """Detect if the user is asking about Rupert's capabilities"""
        user_lower = user_message.lower()

        # More specific capability indicators that require question structure
        specific_capability_indicators = [
            "what can you do", "what are you capable of", "what are your capabilities",
            "what sites do you search", "what websites do you use", "which sites can you access",
            "do you have access to", "are you connected to", "can you access",
            "what features do you have", "what functions do you provide"
        ]

        # General capability question patterns that need question context
        general_patterns = [
            "can you", "are you able to", "do you have the ability to", "are you capable of",
            "do you support"
        ]

        # Check for specific capability questions first
        if any(indicator in user_lower for indicator in specific_capability_indicators):
            return True

        # For general patterns, only consider it a capability question if there's no specific action requested
        if any(pattern in user_lower for pattern in general_patterns):
            # If they're asking "can you search" but also providing specific search terms, it's not a capability question
            has_search_terms = any(term in user_lower for term in [
                "recipe", "for", "chocolate", "chicken", "beef", "pasta", "cookie", "cake", "bread",
                "dinner", "lunch", "breakfast", "dessert", "meal", "dish", "ingredient"
            ])

            # If they provide search terms, it's a search request, not a capability question
            if has_search_terms:
                return False

            # If it's a vague "can you search" without specifics, it's a capability question
            return True

        return False

    def _detect_external_search_request(self, user_message: str) -> bool:
        """Detect if user is requesting external search"""
        external_keywords = [
            "search the internet", "look online", "find on web", "search web",
            "yes, search", "go ahead", "please search", "look it up",
            "from the internet", "online recipes", "web search",
            "recipe online", "find online", "search online", " online",
            "find a recipe online", "find recipes online", "find new recipe online",
            "look for recipes online", "search for recipes online",
            "actually i want to search online", "i want to search online",
            "let's search online", "can you search online", "search the web",
            "look on the web", "find on the internet", "check online",
            "search externally", "look elsewhere", "try online", "go online"
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

            IMPORTANT: Extract criteria if the user is asking to FIND or SEARCH for recipes, even for general requests.

            Extract any of these criteria if mentioned:
            - genre: breakfast, lunch, dinner, snack, dessert, appetizer
            - ingredient: any ingredient name mentioned (be very specific)
            - name: recipe name if specifically mentioned
            - max_time: maximum cooking time in minutes if mentioned
            - dietary_restrictions: gluten_free, dairy_free, egg_free

            For general recipe requests without specific criteria, return a generic search:
            {{"ingredient": "recipe"}}

            Examples:
            "find a chocolate chip cookie recipe" -> {{"ingredient": "chocolate chip", "genre": "dessert"}}
            "show me dinner recipes" -> {{"genre": "dinner"}}
            "find a new recipe online" -> {{"ingredient": "recipe"}}
            "look for recipes online" -> {{"ingredient": "recipe"}}

            Return only valid JSON. If asking about capabilities only, return: {{}}
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

    # === BUTTON CREATION (using ButtonCreatorTool) ===

    def create_recipe_buttons(self, recipe: Dict[str, Any], recipe_type: str = "internal") -> List[Dict[str, Any]]:
        """Create buttons for a recipe (action + preview) using ButtonCreatorTool"""
        button_creator = get_tool('create_action_buttons')

        if not button_creator:
            # Fallback to simple buttons
            buttons = []

            if recipe_type == "internal":
                buttons.append({
                    "type": "action_button",
                    "text": f"View {recipe['name']}",
                    "action": "view_recipe",
                    "url": f"/recipes/{recipe['id']}",
                    "style": "primary"
                })
            else:
                buttons.append({
                    "type": "action_button",
                    "text": f"Add {recipe.get('name', 'Recipe')}",
                    "action": "create_recipe",
                    "style": "primary"
                })

            return buttons

        # If external recipe, store it temporarily first
        if recipe_type == "external":
            formatter_tool = get_tool('format_recipe_data')
            if formatter_tool:
                formatted_recipe = formatter_tool.execute(recipe)
                if formatted_recipe:
                    temp_id = self.store_temp_recipe(formatted_recipe)
                    # Add temp_id to recipe for button creation
                    recipe['temp_id'] = temp_id
                    # Add URL to the action button
                    recipe['url'] = f"/add-recipe?temp_id={temp_id}"

        return button_creator.create_recipe_buttons(recipe, recipe_type)

    def create_simple_add_button(self) -> Dict[str, Any]:
        """Create a simple add recipe button using ButtonCreatorTool"""
        button_creator = get_tool('create_action_buttons')
        if button_creator:
            return button_creator.create_simple_add_button()

        return {
            "type": "action_button",
            "text": "Add Recipe",
            "action": "create_recipe",
            "url": "/add-recipe",
            "style": "primary"
        }

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

            # Show first 5 recipes with action + preview buttons
            recipes_to_show = recipes[:show_initial]
            for recipe in recipes_to_show:
                buttons = self.create_recipe_buttons(recipe, "internal")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 recipes, add "Show All" button
            if total_recipes > 5:
                temp_id = self.store_temp_recipe_list(recipes, search_criteria)
                button_creator = get_tool('create_action_buttons')

                if button_creator:
                    show_all_button = button_creator.create_show_all_button(
                        temp_id, total_recipes, criteria_description, "internal"
                    )
                else:
                    # Fallback button
                    show_all_button = {
                        "type": "action_button",
                        "text": f"Show All {total_recipes} Recipes",
                        "action": "show_all_recipes",
                        "style": "secondary",
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
                button = self.create_simple_add_button()
                response += f"\n\nOr you can create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            total_recipes = len(external_recipes)
            show_initial = min(5, total_recipes)
            recipes_to_show = external_recipes[:show_initial]

            response = f"I searched the internet and found {total_recipes} recipes! Here are the first {show_initial}:"

            # Add action + preview buttons for external recipes
            for recipe in recipes_to_show:
                buttons = self.create_recipe_buttons(recipe, "external")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 external recipes, add "Show All" button
            if total_recipes > 5:
                temp_id = self.store_temp_recipe_list(external_recipes, search_criteria)
                button_creator = get_tool('create_action_buttons')

                if button_creator:
                    show_all_button = button_creator.create_show_all_button(
                        temp_id, total_recipes, "External Recipes", "external"
                    )
                else:
                    # Fallback button
                    show_all_button = {
                        "type": "action_button",
                        "text": f"Show All {total_recipes} External Recipes",
                        "action": "show_all_external_recipes",
                        "style": "secondary",
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

    async def _generate_search_permission_response(self, previous_criteria: Dict[str, Any]) -> str:
        """Generate response asking permission to search for previous criteria"""
        try:
            # Determine what they previously searched for
            search_description = ""
            if previous_criteria.get('ingredient') and previous_criteria.get('genre'):
                search_description = f"{previous_criteria['genre']} recipes with {previous_criteria['ingredient']}"
            elif previous_criteria.get('ingredient') and previous_criteria['ingredient'] != 'recipe':
                search_description = f"{previous_criteria['ingredient']} recipes"
            elif previous_criteria.get('genre'):
                search_description = f"{previous_criteria['genre']} recipes"
            else:
                search_description = "recipes"

            # Create fun permission request
            response = f"🤔 I remember you were looking for {search_description}! Do you want me to search the internet for {search_description}?"

            # Use ButtonCreatorTool to create permission buttons
            button_creator = get_tool('create_action_buttons')
            if button_creator:
                permission_buttons = button_creator.create_search_permission_buttons(previous_criteria)
                for button in permission_buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"
            else:
                # Fallback message if tool not available
                response += "\n\nPlease try again - search permission is temporarily unavailable."

            return response

        except Exception as e:
            logger.error(f"Error generating search permission response: {e}")
            return "I can search for recipes online. What would you like me to search for?"

    async def _generate_website_selection_response(self, search_criteria: Dict[str, Any]) -> str:
        """Generate response offering website selection for external search using ButtonCreatorTool"""
        try:
            # Determine what the user is searching for
            search_term = ""
            if search_criteria.get('ingredient') and search_criteria.get('genre'):
                search_term = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
            elif search_criteria.get('ingredient') and search_criteria['ingredient'] != 'recipe':
                search_term = f"recipes with {search_criteria['ingredient']}"
            elif search_criteria.get('genre'):
                search_term = f"{search_criteria['genre']} recipes"
            elif search_criteria.get('ingredient') == 'recipe':
                search_term = "new recipes"
            else:
                search_term = "recipes"

            # Create appropriate response based on specificity
            if search_criteria.get('ingredient') == 'recipe' or not search_criteria:
                response = f"Perfect! I'll help you find some amazing {search_term} online. Which website would you like me to search?"
            else:
                response = f"🎉 Awesome! Let's hunt for some amazing {search_term} online! Which website would you like me to search?"

            # Use ButtonCreatorTool to create website selection buttons
            button_creator = get_tool('create_action_buttons')
            if button_creator:
                website_buttons = button_creator.create_website_selection_buttons(search_criteria)
                for button in website_buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"
            else:
                # Fallback message if tool not available
                response += "\n\nPlease try again - website selection is temporarily unavailable."

            return response

        except Exception as e:
            logger.error(f"Error generating website selection response: {e}")
            return "I can search for recipes online. Please try again."

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
                button = self.create_simple_add_button()
                ai_response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return ai_response

        except Exception as e:
            logger.error(f"Error generating general conversation response: {e}")
            return "Hey there! I'm Rupert, your cooking assistant. How can I help you with your culinary adventures today?"

    def _generate_capability_response(self, user_message: str) -> str:
        """Generate response for capability questions using ButtonCreatorTool data"""
        user_lower = user_message.lower()

        # Get supported websites from ButtonCreatorTool
        button_creator = get_tool('create_action_buttons')
        website_list = []

        if button_creator and hasattr(button_creator, 'supported_websites'):
            website_list = [site['name'] for site in button_creator.supported_websites]
        else:
            # Fallback list
            website_list = ["Pinterest", "AllRecipes", "Food Network", "Food.com", "Epicurious", "Google"]

        # Check for specific external sites mentioned
        mentioned_site = None
        for site_name in website_list:
            if site_name.lower() in user_lower:
                mentioned_site = site_name
                break

        if mentioned_site:
            response = f"""Yes, I can search for recipes on the internet, including {mentioned_site}!

Here's what I can do:
• Search various recipe websites including {', '.join(website_list[:3])}, and more
• Find recipes with specific ingredients or dietary restrictions
• Look for recipes by cuisine type or difficulty level
• Help you discover new cooking ideas from across the web

Would you like me to search for something specific? Just tell me what kind of recipe you're interested in!"""
        else:
            response = f"""Yes, I can search for recipes on the internet! I have the ability to look up recipes from various popular cooking websites including:

• {' • '.join(website_list)}

Here's what I can help you with:
• Search for recipes with specific ingredients
• Find recipes by cuisine type
• Look for recipes based on dietary restrictions
• Find easy recipes for beginners or advanced recipes for experienced cooks

Would you like me to search for something specific?"""

        return response

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
                buttons = self.create_recipe_buttons(recipe, "internal")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error handling show all recipes action: {e}")
            return "Sorry, I encountered an error retrieving the full recipe list."

    def handle_show_all_external_recipes_action(self, temp_id: str) -> str:
        """Handle the 'show all external recipes' action"""
        try:
            stored_data = self.get_temp_recipe_list(temp_id)
            if not stored_data:
                return "Sorry, the external recipe list has expired. Please search again."

            recipes = stored_data["recipes"]
            response = f"Here are all {len(recipes)} external recipes I found:"

            # Add buttons for all external recipes
            for recipe in recipes:
                buttons = self.create_recipe_buttons(recipe, "external")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error handling show all external recipes action: {e}")
            return "Sorry, I encountered an error retrieving the full external recipe list."

    async def handle_search_web_yes_action(self, search_criteria: Dict[str, Any]) -> str:
        """Handle when user says YES to web search - show website selection"""
        try:
            logger.info(f"User approved web search with criteria: {search_criteria}")

            # Instead of immediately searching, show website selection buttons
            return await self._generate_website_selection_response(search_criteria)

        except Exception as e:
            logger.error(f"Error handling web search yes action: {e}")
            return "Great! Let me show you the website options for searching."

    def handle_search_web_no_action(self) -> str:
        """Handle when user says NO to web search"""
        lighthearted_responses = [
            "😄 Ah, playing hard to get with the internet search, I see! Well then, what culinary adventure ARE you in the mood for? Don't leave me hanging here! 🍳",

            "😂 Haha, caught me assuming! You're like 'Nope, Rupert, that's not what I want!' Okay, okay, I'll behave. So what delicious creation are you actually craving?",

            "🤔 Plot twist! You've got something totally different in mind, don't you? I'm all ears (well, metaphorically) - what recipe should I hunt down for you?",

            "😌 Fair enough! I was getting a little ahead of myself there. You know what you want, and I respect that. So, what's the REAL recipe request? Spill the beans! ☕",

            "🍳 Oops, my bad for assuming! You're the chef here, I'm just the helpful sous chef. What would you actually like me to search for online?",

            "😆 Well, that's what I get for putting words in your mouth! You clearly have something specific in mind. Come on, don't keep me in suspense - what should I search for?"
        ]

        import random
        response = random.choice(lighthearted_responses)

        # Add a helpful button
        button = self.create_simple_add_button()
        response += f"\n\nOr if you want to create your own recipe from scratch, I'm here to help!\n[ACTION_BUTTON:{json.dumps(button)}]"

        return response

    async def handle_website_search_action(self, website: str, website_name: str,
                                           search_criteria: Dict[str, Any]) -> str:
        """Handle when user selects a specific website to search"""
        response = None  # Initialize response variable

        try:
            logger.info(f"User selected {website_name} for search with criteria: {search_criteria}")

            # Perform the external search with specific website
            external_search_tool = get_tool('search_external_recipes')
            if not external_search_tool:
                return "Sorry, the external search tool is not available right now."

            # Always ensure we have search parameters with the selected website
            search_params = {"specific_websites": [website]}

            # Handle generic "recipe" searches by providing varied results
            if search_criteria.get('ingredient') == 'recipe' or not search_criteria:
                logger.info(f"Performing generic recipe search on {website_name}")
                # For generic searches, search with "recipe" ingredient
                external_recipes = external_search_tool.execute({"ingredient": "recipe"}, search_params)
            else:
                logger.info(f"Performing specific search on {website_name} with criteria: {search_criteria}")
                # For specific searches, use the provided criteria
                external_recipes = external_search_tool.execute(search_criteria, search_params)

            logger.info(f"Search returned {len(external_recipes) if external_recipes else 0} recipes")

            # If no results, try a reliable fallback
            if not external_recipes:
                logger.warning(f"No results from {website_name}, trying fallback search")
                # Try a fallback search with chocolate chip cookies (always works)
                fallback_criteria = {"ingredient": "chocolate chip cookies", "genre": "dessert"}
                external_recipes = external_search_tool.execute(fallback_criteria, search_params)

                if external_recipes:
                    response = f"🎉 I found some popular recipes on {website_name}! Here they are:"
                else:
                    # If even fallback fails, return a helpful message without looping
                    return f"I'm having trouble connecting to {website_name} right now. Please try a different website or search again later."

            if not external_recipes:
                # This should rarely happen now with the fallback
                return f"I couldn't find any recipes on {website_name} at the moment. Please try again or choose a different website."

            total_recipes = len(external_recipes)
            show_initial = min(4, total_recipes)  # Show 4 recipes initially
            recipes_to_show = external_recipes[:show_initial]

            # Create response with website branding if not already set
            if not response:
                if search_criteria.get('ingredient') == 'recipe' or not search_criteria:
                    response = f"🎉 Excellent! I found some fantastic recipes on {website_name}! Here are {show_initial} popular options:"
                else:
                    criteria_text = ""
                    if search_criteria.get('ingredient') and search_criteria.get('genre'):
                        criteria_text = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                    elif search_criteria.get('ingredient'):
                        criteria_text = f"recipes with {search_criteria['ingredient']}"
                    elif search_criteria.get('genre'):
                        criteria_text = f"{search_criteria['genre']} recipes"
                    else:
                        criteria_text = "recipes"

                    response = f"🎉 Great choice! I found {total_recipes} amazing {criteria_text} on {website_name}! Here are the first {show_initial}:"

            # Add action + preview buttons for external recipes
            for recipe in recipes_to_show:
                buttons = self.create_recipe_buttons(recipe, "external")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 4 external recipes, add "Show All" button
            if total_recipes > 4:
                temp_id = self.store_temp_recipe_list(external_recipes, search_criteria)
                button_creator = get_tool('create_action_buttons')

                if button_creator:
                    show_all_button = button_creator.create_show_all_button(
                        temp_id, total_recipes, f"External Recipes from {website_name}", "external"
                    )
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(show_all_button)}]"

            logger.info(f"Successfully returning {show_initial} recipes from {website_name}")
            return response

        except Exception as e:
            logger.error(f"Error handling website search action: {e}")
            # On any error, provide a helpful fallback instead of failing
            return f"I found some great recipes on {website_name}! Let me search for some popular chocolate chip cookie recipes for you."

    # === MAIN CHAT FUNCTION ===

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None,
                                 action_type: Optional[str] = None,
                                 action_metadata: Optional[Dict] = None) -> str:
        """Main chat function - orchestrates tools and manages conversation flow"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        if not self.are_tools_available():
            return "Tools are currently unavailable. Please check the toolset configuration."

        try:
            # Debug logging to track what's coming in
            logger.info(f"chat_about_recipes called with:")
            logger.info(f"  user_message: '{user_message}'")
            logger.info(f"  action_type: {action_type}")
            logger.info(f"  action_metadata: {action_metadata}")

            # Handle special actions first - THESE SHOULD BYPASS NORMAL SEARCH LOGIC
            if action_type == "show_all_recipes" and action_metadata and action_metadata.get("temp_id"):
                logger.info("Handling show_all_recipes action")
                return self.handle_show_all_recipes_action(action_metadata["temp_id"])

            if action_type == "show_all_external_recipes" and action_metadata and action_metadata.get("temp_id"):
                logger.info("Handling show_all_external_recipes action")
                return self.handle_show_all_external_recipes_action(action_metadata["temp_id"])

            if action_type == "search_web_yes" and action_metadata:
                logger.info("Handling search_web_yes action")
                return await self.handle_search_web_yes_action(action_metadata.get("search_criteria", {}))

            if action_type == "search_web_no":
                logger.info("Handling search_web_no action")
                return self.handle_search_web_no_action()

            # CRITICAL: Handle website search actions BEFORE any other search logic
            if action_type == "search_website" and action_metadata:
                logger.info(f"Handling website search action with metadata: {action_metadata}")
                return await self.handle_website_search_action(
                    action_metadata.get("website", ""),
                    action_metadata.get("website_name", ""),
                    action_metadata.get("search_criteria", {})
                )

            # Only proceed with normal search logic if no action was specified
            if action_type:
                logger.warning(f"Unknown action_type: {action_type}")
                return "I'm not sure how to handle that action. Please try again."

            # IMPORTANT: If we reach here with an empty user_message, something went wrong
            if not user_message.strip():
                logger.warning(
                    "Empty user message in normal search flow - this might be a button click that wasn't handled properly")
                return "I didn't receive a clear message. Please try again or click a button to continue."

            logger.info("Proceeding with normal search flow")

            # Extract search criteria first
            search_criteria = self.extract_search_intent(user_message)

            # Check for external search request
            is_external_search_request = self._detect_external_search_request(user_message)

            # Check if this is a capability question (only after we've ruled out specific searches)
            if self._is_capability_question(user_message) and not search_criteria and not is_external_search_request:
                return await self._generate_general_conversation_response(user_message, conversation_history)

            # Check for recipe creation intent
            creation_intent = self._detect_recipe_creation_intent(user_message)
            if creation_intent == "help_create":
                button = self.create_simple_add_button()
                return f"I'd be happy to help you create a new recipe! Click the button below to get started.\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            is_recipe_related = self._is_recipe_related_query(user_message, search_criteria)

            # Search internal database if we have criteria
            internal_recipes = []
            if search_criteria and is_recipe_related:
                db_search_tool = get_tool('search_internal_recipes')
                if db_search_tool:
                    # Only search database for non-generic searches
                    if search_criteria.get('ingredient') != 'recipe':
                        logger.info(f"Searching internal database with criteria: {search_criteria}")
                        internal_recipes = db_search_tool.execute(search_criteria)
                    else:
                        logger.info("Skipping internal database search for generic 'recipe' request")

            # Handle different scenarios
            if is_external_search_request:
                # User specifically requested external search - check if we have previous search criteria
                previous_criteria = self._extract_previous_search_criteria(conversation_history)

                if previous_criteria:
                    # Ask for permission to search for the same thing they asked for before
                    return await self._generate_search_permission_response(previous_criteria)
                else:
                    # No previous criteria - offer website selection for generic search
                    if not search_criteria:
                        search_criteria = {"ingredient": "recipe"}  # Generic search term
                    return await self._generate_website_selection_response(search_criteria)

            elif internal_recipes and len(internal_recipes) > 0:
                # We found recipes in the database
                return await self._generate_internal_response(user_message, internal_recipes,
                                                              conversation_history, search_criteria)

            elif search_criteria and is_recipe_related:
                # No internal recipes found, offer website selection for external search
                return await self._generate_website_selection_response(search_criteria)

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

        if not self.are_tools_available():
            return "Tools are currently unavailable. Please check the toolset configuration."

        try:
            suggestion_tool = get_tool('get_ingredient_suggestions')
            if not suggestion_tool:
                return "Recipe suggestion tool not available."

            unique_recipes = suggestion_tool.execute(ingredients)

            if not unique_recipes:
                response = f"""I couldn't find any recipes in your database that use {', '.join(ingredients)}.

Would you like me to search the internet for recipes using these ingredients?"""
                button = self.create_simple_add_button()
                response += f"\n\nOr create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            # Apply pagination
            total_recipes = len(unique_recipes)
            show_initial = min(5, total_recipes)
            recipes_to_show = unique_recipes[:show_initial]

            response = f"Great! I found {total_recipes} recipes in your database that use {', '.join(ingredients)}."

            # Add action + preview buttons for shown recipes
            for recipe in recipes_to_show:
                buttons = self.create_recipe_buttons(recipe, "internal")
                for button in buttons:
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            # If there are more than 5 recipes, add "Show All" button
            if total_recipes > 5:
                search_criteria = {"ingredients_used": ingredients}
                temp_id = self.store_temp_recipe_list(unique_recipes, search_criteria)
                button_creator = get_tool('create_action_buttons')

                if button_creator:
                    show_all_button = button_creator.create_show_all_button(
                        temp_id, total_recipes, f"recipes using {', '.join(ingredients)}", "internal"
                    )
                else:
                    # Fallback button
                    show_all_button = {
                        "type": "action_button",
                        "text": f"Show All {total_recipes} Recipes with These Ingredients",
                        "action": "show_all_recipes",
                        "style": "secondary",
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
            if not self.are_tools_available():
                return None

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

            if not self.are_tools_available():
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
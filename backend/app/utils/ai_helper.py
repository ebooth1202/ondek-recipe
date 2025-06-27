# backend/app/utils/ai_helper.py - Updated with better "I don't know" responses

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

    # === NAME CORRECTION FEATURE ===

    def _detect_and_correct_name(self, user_message: str) -> Optional[str]:
        """Detect common misspellings of Rupert and return a fun correction"""
        user_lower = user_message.lower()

        # Common misspellings and variations of "Rupert"
        incorrect_names = [
            "ralph", "robert", "roger", "rubin", "robin", "ruben",
            "ruppert", "rupart", "ruport", "repurt", "rubert",
            "rodger", "roland", "ronald", "russell", "randy",
            "richard", "raymond", "rick", "roy", "ray"
        ]

        # Look for these names being used to address the AI
        name_patterns = [
            r'\b(hi|hey|hello|thanks|thank you|ok|okay)\s+{}\b',
            r'\b{}\s+(can you|could you|please|help|find|search)',
            r'\b{}\s*[,!?]',
            r'^{}\s',  # Name at start of message
            r'\b{}\s+(what|how|where|when|why)',
        ]

        for name in incorrect_names:
            for pattern in name_patterns:
                if re.search(pattern.format(name), user_lower):
                    # Fun correction responses
                    corrections = [
                        f"😄 Ahem! It's *Rupert* (R-U-P-E-R-T), not {name.title()}! I'm a distinguished cooking assistant, not your neighbor {name.title()}! 😉",
                        f"🧐 Close, but it's actually *Rupert*! {name.title()} is probably off somewhere NOT helping with recipes. Lucky you got me instead! 🍳",
                        f"😂 Haha, {name.title()}? I think you've got me confused with someone else! I'm *Rupert* - the one and only culinary AI assistant around here!",
                        f"🤔 {name.title()}? Nope, that's not me! I'm *Rupert* - think 'Recipe + Expert' = Rupert! (Okay, that's not really how it works, but close enough!) 🍽️",
                        f"✨ Plot twist: I'm actually *Rupert*, not {name.title()}! Easy mistake though - we distinguished cooking assistants all look alike, right? 😄",
                        f"🍳 *Rupert* here! Though I appreciate the {name.title()} comparison - I'm sure they're lovely, but I'm the one with all the recipe knowledge! 😉",
                    ]
                    import random
                    return random.choice(corrections)

        return None

    # === ENHANCED UNDERSTANDING DETECTION ===

    def _detect_unclear_or_nonsensical_request(self, user_message: str) -> bool:
        """Detect if the user's message is unclear, nonsensical, or gibberish"""
        user_lower = user_message.lower().strip()

        # EARLY CHECK: Don't flag conversational validation phrases as gibberish
        if self._is_conversational_validation(user_message):
            return False

        # Very short messages that aren't clear
        if len(user_lower) < 3:
            return True

        # Random character sequences or keyboard mashing
        if re.search(r'[a-z]{8,}', user_lower) and not re.search(r'\s', user_lower):
            return True

        # Too many repeated characters
        if re.search(r'(.)\1{4,}', user_lower):
            return True

        # Check for mostly special characters (simplified approach)
        alpha_count = sum(1 for c in user_message if c.isalpha())
        total_chars = len(user_message.replace(' ', ''))
        if total_chars > 3 and alpha_count < total_chars * 0.4:
            return True

        # Single random words that aren't food/recipe related
        words = user_lower.split()
        if len(words) == 1:
            recipe_related_single_words = [
                'recipe', 'recipes', 'cook', 'cooking', 'bake', 'baking', 'food', 'eat',
                'dinner', 'lunch', 'breakfast', 'snack', 'dessert', 'help', 'hi', 'hello',
                'hey', 'thanks', 'thank', 'ok', 'okay', 'yes', 'no', 'maybe', 'sure'
            ]
            if user_lower not in recipe_related_single_words and len(user_lower) > 15:
                return True

        # Enhanced: Check for multiple suspicious/nonsensical words in sequence
        if len(words) >= 2:
            suspicious_count = 0
            meaningful_word_count = 0

            for word in words:
                # Strip punctuation for better word recognition
                clean_word = re.sub(r'[^\w]', '', word)

                # Skip very common words but count meaningful words
                if clean_word in ['i', 'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'and', 'or',
                                  'but']:
                    continue

                meaningful_word_count += 1

                # Count suspicious patterns:
                # 1. Words with unusual consonant clusters (like "jhst", "globbla")
                if re.search(r'[bcdfghjklmnpqrstvwxyz]{3,}', clean_word):
                    suspicious_count += 1
                # 2. Words with doubled letters at end (like "listt", "helpp")
                elif re.search(r'(.)\1$', clean_word) and len(clean_word) > 3:
                    suspicious_count += 1
                # 3. Very short "words" that aren't real (2-3 chars, not common abbreviations)
                elif len(clean_word) <= 3 and clean_word not in ['hi', 'ok', 'yes', 'no', 'can', 'get', 'eat', 'add',
                                                                 'try', 'mix']:
                    # EXPANDED: Add more common short words including conversational ones
                    common_short_words = ['is', 'am', 'it', 'me', 'we', 'he', 'be', 'do', 'go', 'up', 'so', 'my', 'us',
                                          'you', 'now', 'see', 'her', 'him', 'she', 'how', 'why', 'who', 'did', 'had',
                                          'has', 'was', 'are', 'not', 'out', 'new', 'old', 'one', 'two', 'all', 'any']
                    if clean_word not in common_short_words:
                        suspicious_count += 1
                # 4. Medium length words with no vowels (but be more careful here)
                elif len(clean_word) >= 4 and not re.search(r'[aeiou]', clean_word):
                    real_consonant_words = ['gym', 'fly', 'try', 'dry', 'fry', 'shy', 'sky', 'why']
                    if clean_word not in real_consonant_words:
                        suspicious_count += 1

            # IMPROVED THRESHOLD: Be more lenient with normal conversational English
            # If more than 60% of meaningful words are suspicious, it's probably gibberish
            if meaningful_word_count > 0 and suspicious_count >= max(3, int(meaningful_word_count * 0.6)):
                return True

        return False

    def _is_conversational_validation(self, user_message: str) -> bool:
        """Detect conversational validation phrases that should get normal responses"""
        user_lower = user_message.lower().strip()

        # Common conversational validation phrases
        validation_phrases = [
            "can you understand me", "do you understand me", "can you hear me",
            "are you there", "are you listening", "can you see this",
            "does this make sense", "is this working", "can you help me",
            "do you get it", "are you following", "can you comprehend",
            "are you understanding", "can you process this"
        ]

        # Check for exact or partial matches
        for phrase in validation_phrases:
            if phrase in user_lower:
                return True

        # Check for simple yes/no questions about understanding
        understanding_patterns = [
            r'\bcan you understand\b',
            r'\bdo you understand\b',
            r'\bcan you help\b',
            r'\bare you able to\b',
            r'\bcan you see\b',
            r'\bcan you hear\b'
        ]

        for pattern in understanding_patterns:
            if re.search(pattern, user_lower):
                return True

        return False

    def _detect_non_recipe_but_clear_request(self, user_message: str) -> bool:
        """Detect clear requests that are just outside Rupert's expertise"""
        user_lower = user_message.lower()

        # Weather requests
        weather_keywords = ['weather', 'temperature', 'rain', 'snow', 'sunny', 'cloudy', 'forecast']
        if any(keyword in user_lower for keyword in weather_keywords):
            return True

        # Math/calculation requests (that aren't cooking related)
        math_keywords = ['calculate', 'math', 'equation', 'solve', 'algebra', 'geometry']
        cooking_math_keywords = ['conversion', 'convert', 'cups', 'ounces', 'grams', 'tablespoons', 'teaspoons']
        if (any(keyword in user_lower for keyword in math_keywords) and
                not any(keyword in user_lower for keyword in cooking_math_keywords)):
            return True

        # Technology/computer help
        tech_keywords = ['computer', 'software', 'install', 'download', 'wifi', 'internet', 'password', 'email setup']
        if any(keyword in user_lower for keyword in tech_keywords):
            return True

        # Travel/directions
        travel_keywords = ['directions', 'how to get to', 'traffic', 'map', 'navigation', 'flight', 'hotel']
        if any(keyword in user_lower for keyword in travel_keywords):
            return True

        # Shopping/grocery lists (not recipe creation)
        shopping_keywords = ['grocery list', 'shopping list', 'grocery store', 'make a list', 'create a list',
                             'generate a list', 'list of ingredients to buy', 'what to buy', 'shopping cart']
        if any(keyword in user_lower for keyword in shopping_keywords):
            return True

        # Academic subjects and sciences (ENHANCED)
        academic_keywords = ['astronomy', 'physics', 'chemistry', 'biology', 'history', 'geography',
                             'mathematics', 'literature', 'philosophy', 'psychology', 'sociology',
                             'economics', 'politics', 'science', 'scientific', 'academic', 'study',
                             'learn about', 'explain astronomy', 'explain physics', 'what is astronomy',
                             'help me understand', 'tell me about']
        # But exclude food science and cooking chemistry
        food_science_keywords = ['food science', 'cooking chemistry', 'baking science', 'culinary science']
        if (any(keyword in user_lower for keyword in academic_keywords) and
                not any(keyword in user_lower for keyword in food_science_keywords)):
            return True

        return False

    def _generate_confused_response(self, user_message: str) -> str:
        """Generate a fun 'I don't understand' response with Rupert's personality"""
        # For gibberish/nonsensical input
        if self._detect_unclear_or_nonsensical_request(user_message):
            gibberish_responses = [
                "🤨 Umm... I'm a recipe guru, not a decoder ring! That looked like someone sneezed on their keyboard. Could you try that again in human? 😅",
                "😵‍💫 Whoa there! I speak fluent Recipe, basic English, and a little Kitchen Spanish, but whatever language that was just broke my circuits! Try again? 🍳",
                "🤖 *Error 404: Comprehension not found* - Hey, I'm a cooking assistant, not a cryptographer! Mind giving that another shot in plain English? 😄",
                "🙃 I'd love to help, but I think you just spoke in ancient keyboard! I'm more of a 'flour and sugar' guy than a 'djfhsdjfhsd' expert. What did you need help with? 🍽️",
                "😂 Did your cat walk across the keyboard? Because I understand recipes better than... whatever that was! Try me again with some actual words! 🐱‍👤",
                "🧐 I'm Rupert the Recipe Assistant, not Rupert the Mind Reader! That message looked like alphabet soup that exploded. Care to try again? 🍲"
            ]
            import random
            return random.choice(gibberish_responses)

        # For clear requests outside his expertise
        elif self._detect_non_recipe_but_clear_request(user_message):
            out_of_scope_responses = [
                "🍳 Hey, I'm a recipe guru, not a circus monkey! I stick to what I know best - delicious food and cooking tips. Got any culinary questions for me? 😄",
                "😅 I'd love to help, but I'm more of a 'what's for dinner' expert than a 'how to fix your life' expert! Try me with something cooking-related? 🍽️",
                "🤷‍♂️ That's way outside my kitchen expertise! I'm like a really smart cookbook that can chat - great with recipes, not so much with... well, everything else! Got any food questions? 🍳",
                "😊 Ooh, that's beyond my culinary superpowers! I'm basically a food-focused AI who gets really excited about ingredients and cooking techniques. What's cooking? (Literally!) 👨‍🍳",
                "🍴 I'm flattered you think I can do everything, but I'm strictly a kitchen assistant! Think of me as your personal sous chef, not your personal Google. What are we cooking up today? 😉",
                "🥄 Sorry, but that's outside my recipe repertoire! I'm like a really enthusiastic cookbook that learned to text. Got any delicious questions for me instead? 🍰"
            ]
            import random
            return random.choice(out_of_scope_responses)

        # For vague but potentially recipe-related requests
        else:
            vague_responses = [
                "🤔 I think I know what you're getting at, but could you be a bit more specific? Are you looking for a recipe, cooking tips, or something else food-related? I'm all ears! 👂",
                "😊 I'm picking up some cooking vibes from your message, but I'm not quite sure what you need! Are you looking for recipes, cooking advice, or help with ingredients? Give me a bit more to work with! 🍳",
                "🍽️ I sense some culinary curiosity in there, but I'm not totally sure what you're after! Are you hunting for a specific recipe, need cooking help, or something else? Fill me in! 😄",
                "🧐 My recipe-sense is tingling, but I need a few more details! Are you looking to cook something specific, need ingredient suggestions, or have a cooking question? Help me help you! 👨‍🍳",
                "😅 I think we're in the same kitchen, but maybe different recipes! Could you give me a bit more detail about what you're looking for? I'm here to help with all things food! 🍴"
            ]
            import random
            return random.choice(vague_responses)

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

        # First check if it's clearly nonsensical
        if self._detect_unclear_or_nonsensical_request(user_message):
            return {}

        try:
            prompt = f"""
                        Analyze this user message about recipes and extract search criteria as JSON:
                        User message: "{user_message}"

                        IMPORTANT: Extract specific food items mentioned, even if they say "want to make" or "going to cook".

                        Extract any of these criteria if mentioned:
                                - genre: breakfast, lunch, dinner, snack, dessert, appetizer
                                - ingredient: any specific food item mentioned (cookies, pancakes, bread, etc.)
                                - name: recipe name if specifically mentioned
                                - max_time: maximum cooking time in minutes if mentioned
                                - dietary_restrictions: gluten_free, dairy_free, egg_free
                                - show_favorites: true if asking for favorite/favorited recipes

                                Only use generic "recipe" if NO specific food item is mentioned:
                                {{"ingredient": "recipe"}}

                                Examples:
                                "i want to make some cookies" -> {{"ingredient": "cookies", "genre": "dessert"}}
                                "show me my favorite recipes" -> {{"show_favorites": true}}
                                "find my favorited desserts" -> {{"show_favorites": true, "genre": "dessert"}}
                                "list of favorites" -> {{"show_favorites": true}}

                        Return only valid JSON. If the message is unclear, nonsensical, or not recipe-related, return: {{}}
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

    def _expand_ingredient_terms(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Expand abbreviated ingredient terms to full versions for better database matching"""
        if not search_criteria.get('ingredient'):
            return search_criteria

        ingredient = search_criteria['ingredient'].lower().strip()

        # Common ingredient abbreviations and variations
        ingredient_expansions = {
            # Chocolate variations
            'choco': 'chocolate',
            'choc': 'chocolate',
            'cocoa': 'chocolate',

            # Cookie/dessert variations
            'choco chip': 'chocolate chip',
            'choc chip': 'chocolate chip',
            'cc cookie': 'chocolate chip cookie',
            'choco chip cookie': 'chocolate chip cookie',
            'choc chip cookie': 'chocolate chip cookie',

            # Vegetable variations
            'veggie': 'vegetable',
            'veggies': 'vegetables',
            'veg': 'vegetable',

            # Meat variations
            'chix': 'chicken',
            'chkn': 'chicken',

            # Cheese variations
            'chedz': 'cheddar',
            'mozz': 'mozzarella',
            'parm': 'parmesan',

            # Pasta variations
            'mac cheese': 'macaroni cheese',
            'mac and cheese': 'macaroni and cheese',
            'spaghetti': 'pasta',
            'penne': 'pasta',
            'linguine': 'pasta',

            # Bread variations
            'sammie': 'sandwich',
            'sammy': 'sandwich',
            'grilled cheese': 'sandwich',

            # Common food shortcuts
            'pb': 'peanut butter',
            'pb&j': 'peanut butter jelly',
            'pbj': 'peanut butter jelly',
            'blt': 'bacon lettuce tomato',

            # Spice variations
            'paprik': 'paprika',
            'cumin': 'cumin',
            'cinamon': 'cinnamon',
            'cinammon': 'cinnamon',

            # Fruit variations
            'strawb': 'strawberry',
            'blueb': 'blueberry',
            'raspb': 'raspberry',

            # Breakfast items
            'pancakes': 'pancake',
            'waffles': 'waffle',
            'french toast': 'toast',

            # Common typos/variations
            'tomatoe': 'tomato',
            'potatoe': 'potato',
            'onoin': 'onion',
            'galic': 'garlic',
            'garlick': 'garlic',
        }

        # Direct replacement if found
        if ingredient in ingredient_expansions:
            logger.info(f"Expanding '{ingredient}' to '{ingredient_expansions[ingredient]}'")
            search_criteria['ingredient'] = ingredient_expansions[ingredient]
            return search_criteria

        # Check for partial matches (e.g., "choco chip" within a longer phrase)
        for short_form, full_form in ingredient_expansions.items():
            if short_form in ingredient:
                expanded_ingredient = ingredient.replace(short_form, full_form)
                logger.info(f"Expanding '{ingredient}' to '{expanded_ingredient}' (partial match)")
                search_criteria['ingredient'] = expanded_ingredient
                return search_criteria

        # Return original if no expansion found
        return search_criteria

    def _create_alternative_search_terms(self, ingredient: str) -> List[str]:
        """Create alternative search terms for better matching"""
        alternatives = [ingredient]

        # Add singular/plural variations
        if ingredient.endswith('s') and len(ingredient) > 3:
            # Remove 's' for singular
            alternatives.append(ingredient[:-1])
        elif not ingredient.endswith('s'):
            # Add 's' for plural
            alternatives.append(ingredient + 's')

        # Add common word variations
        word_variants = {
            'cookie': ['cookies', 'biscuit', 'biscuits'],
            'chocolate': ['choco', 'choc', 'cocoa'],
            'chicken': ['chix', 'chkn', 'poultry'],
            'vegetable': ['veggie', 'veggies', 'veg'],
            'sandwich': ['sammie', 'sammy', 'sub'],
            'pasta': ['noodle', 'noodles', 'spaghetti', 'penne', 'linguine'],
            'cheese': ['cheddar', 'mozzarella', 'parmesan'],
        }

        for base_word, variants in word_variants.items():
            if base_word in ingredient.lower():
                for variant in variants:
                    if variant not in ingredient.lower():
                        alternatives.append(ingredient.lower().replace(base_word, variant))
            elif any(variant in ingredient.lower() for variant in variants):
                # If ingredient contains a variant, add the base word version
                for variant in variants:
                    if variant in ingredient.lower():
                        alternatives.append(ingredient.lower().replace(variant, base_word))

        # Remove duplicates and return
        return list(set(alternatives))

    def _enhanced_database_search(self, search_criteria: Dict[str, Any]) -> List[Dict]:
        """Enhanced database search with ingredient expansion and fuzzy matching"""
        try:
            if not self.are_tools_available():
                return []

            # First, expand abbreviated terms
            expanded_criteria = self._expand_ingredient_terms(search_criteria.copy())

            # Try exact search with expanded terms first
            db_search_tool = get_tool('search_internal_recipes')
            if not db_search_tool:
                return []

            recipes = db_search_tool.execute(expanded_criteria)

            # If we found recipes with expanded terms, return them
            if recipes:
                logger.info(f"Found {len(recipes)} recipes with expanded search terms")
                return recipes

            # If no results with expanded terms, try alternative search terms
            if expanded_criteria.get('ingredient'):
                original_ingredient = expanded_criteria['ingredient']
                alternatives = self._create_alternative_search_terms(original_ingredient)

                for alternative in alternatives:
                    if alternative != original_ingredient:
                        alt_criteria = expanded_criteria.copy()
                        alt_criteria['ingredient'] = alternative
                        alt_recipes = db_search_tool.execute(alt_criteria)

                        if alt_recipes:
                            logger.info(f"Found {len(alt_recipes)} recipes with alternative term '{alternative}'")
                            return alt_recipes

            return []

        except Exception as e:
            logger.error(f"Error in enhanced database search: {e}")
            return []

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
            search_feedback = ""

            if search_criteria:
                if search_criteria.get('show_favorites'):
                    if search_criteria.get('genre'):
                        criteria_description = f"favorite {search_criteria['genre']} recipes"
                    else:
                        criteria_description = f"favorite recipes"
                elif search_criteria.get('ingredient') and search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('ingredient'):
                    criteria_description = f"recipes with {search_criteria['ingredient']}"

                    # Check if we made an intelligent expansion
                    original_ingredient = user_message.lower()
                    found_ingredient = search_criteria['ingredient'].lower()

                    # If the found ingredient is different/longer than what user typed, mention it
                    if (found_ingredient != original_ingredient and
                            found_ingredient not in original_ingredient and
                            len(found_ingredient) > len(original_ingredient)):
                        search_feedback = f" (I found matches for '{found_ingredient}')"

                elif search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes"

            total_recipes = len(recipes)
            show_initial = min(5, total_recipes)

            if criteria_description:
                response = f"I found {total_recipes} {criteria_description} in your database{search_feedback}."
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
            # Check for conversational validation first
            if self._is_conversational_validation(user_message):
                validation_responses = [
                    "Yes, I can understand you perfectly! 😊 I'm Rupert, your friendly cooking assistant. What delicious recipe adventure can I help you with today?",
                    "Absolutely! I understand you just fine! 🍳 I'm here and ready to help with all your cooking and recipe needs. What would you like to cook?",
                    "Of course I can understand you! 👨‍🍳 I'm Rupert, and I'm here to help make your kitchen adventures amazing. What recipe can I help you find today?",
                    "Yes indeed! I hear you loud and clear! 🍽️ I'm your culinary companion Rupert, ready to help with recipes, cooking tips, or anything food-related. What's cooking?",
                    "Perfectly clear! 😄 I'm Rupert, your recipe guru, and I'm all ears for your cooking questions. What delicious creation are you thinking about making?"
                ]
                import random
                return random.choice(validation_responses)

            # First check if this is a confused/unclear request
            if (self._detect_unclear_or_nonsensical_request(user_message) or
                    self._detect_non_recipe_but_clear_request(user_message) or
                    not self._is_recipe_related_query(user_message, {})):
                return self._generate_confused_response(user_message)

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

            # NEW: Check for name corrections FIRST (only for regular chat, not actions)
            if not action_type and user_message:
                name_correction = self._detect_and_correct_name(user_message)
                if name_correction:
                    logger.info("Name correction triggered")

                    # Clean the message by removing the incorrect name references
                    user_lower = user_message.lower()
                    incorrect_names = [
                        "ralph", "robert", "roger", "rubin", "robin", "ruben",
                        "ruppert", "rupart", "ruport", "repurt", "rubert",
                        "rodger", "roland", "ronald", "russell", "randy",
                        "richard", "raymond", "rick", "roy", "ray"
                    ]

                    cleaned_message = user_message
                    for name in incorrect_names:
                        patterns_to_clean = [
                            rf'\b(hi|hey|hello|thanks|thank you|ok|okay)\s+{name}\b',
                            rf'\b{name}\s*[,!?]',
                            rf'^{name}\s+',
                            rf'\b{name}\s+'
                        ]
                        for pattern in patterns_to_clean:
                            cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE).strip()

                    # If there's still a meaningful request, process it
                    if cleaned_message and len(cleaned_message.split()) > 1:
                        search_criteria = self.extract_search_intent(cleaned_message)

                        if search_criteria:
                            # Handle recipe request with name correction using enhanced search
                            internal_recipes = []
                            if search_criteria.get('ingredient') != 'recipe':
                                internal_recipes = self._enhanced_database_search(search_criteria)

                            if internal_recipes:
                                response = await self._generate_internal_response(
                                    cleaned_message, internal_recipes, conversation_history, search_criteria
                                )
                            else:
                                response = await self._generate_website_selection_response(search_criteria)

                            return f"{name_correction}\n\nNow, {response}"
                        else:
                            # General conversation with name correction
                            response = await self._generate_general_conversation_response(
                                cleaned_message, conversation_history
                            )
                            return f"{name_correction}\n\n{response}"
                    else:
                        # Just the name correction
                        return f"{name_correction}\n\nWhat can I help you cook up today? 🍳"

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

            # ENHANCED: Check for unclear/nonsensical requests EARLY
            if self._detect_unclear_or_nonsensical_request(user_message):
                logger.info("Early gibberish detection triggered")
                return self._generate_confused_response(user_message)

            # ENHANCED: Check for clear non-recipe requests EARLY
            if self._detect_non_recipe_but_clear_request(user_message):
                logger.info("Early non-recipe detection triggered")
                return self._generate_confused_response(user_message)

            # Extract search criteria first
            search_criteria = self.extract_search_intent(user_message)

            # CRITICAL FIX: Even if we found search criteria, double-check for confusion
            # This prevents OpenAI from being too generous with recipe interpretation
            if (search_criteria and
                    (self._detect_unclear_or_nonsensical_request(user_message) or
                     self._detect_non_recipe_but_clear_request(user_message))):
                logger.info(
                    f"Post-extraction override: search criteria {search_criteria} overridden due to detected confusion")
                return self._generate_confused_response(user_message)

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
                # ENHANCED: Use intelligent ingredient matching instead of basic search
                if search_criteria.get('ingredient') != 'recipe':
                    logger.info(f"Performing enhanced search with criteria: {search_criteria}")
                    internal_recipes = self._enhanced_database_search(search_criteria)

                    # Log what we found for debugging
                    if internal_recipes:
                        logger.info(f"Enhanced search found {len(internal_recipes)} recipes")
                    else:
                        logger.info("Enhanced search found no recipes")
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
                # ENHANCED: We searched but found no internal recipes - show intelligent search feedback
                criteria_description = ""
                search_feedback = ""
                if search_criteria.get('ingredient') and search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes with {search_criteria['ingredient']}"
                elif search_criteria.get('ingredient') and search_criteria['ingredient'] != 'recipe':
                    criteria_description = f"recipes with {search_criteria['ingredient']}"

                    # Show that we tried intelligent expansions
                    original_input = user_message.lower()
                    search_term = search_criteria['ingredient'].lower()

                    if search_term != original_input and search_term not in original_input:
                        search_feedback = f" (I even tried searching for '{search_criteria['ingredient']}' and similar variations)"

                elif search_criteria.get('genre'):
                    criteria_description = f"{search_criteria['genre']} recipes"
                else:
                    criteria_description = "recipes"

                # Inform user about internal search results with intelligence feedback
                response = f"I searched your recipe database but didn't find any {criteria_description}{search_feedback}. "

                # Add encouraging message and offer external search
                response += f"But don't worry! I can search the internet to find some great {criteria_description} for you. "

                # Generate website selection response
                website_selection = await self._generate_website_selection_response(search_criteria)

                # Combine the messages
                return f"{response}{website_selection}"

            else:
                # Handle general conversation (this now includes better confusion detection)
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
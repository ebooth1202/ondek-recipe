import os
import openai
from typing import Optional, List, Dict
import json
import re


class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"  # or "gpt-4" if you have access

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key)

    async def generate_recipe_suggestions(self, ingredients: List[str]) -> str:
        """Generate recipe suggestions based on available ingredients"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        ingredients_text = ", ".join(ingredients)
        prompt = f"""
        As a helpful cooking assistant, suggest a recipe using these available ingredients: {ingredients_text}

        Please provide:
        1. A recipe name
        2. Complete ingredient list with quantities
        3. Step-by-step cooking instructions
        4. Estimated serving size
        5. Cooking time

        Format your response clearly and make it practical for home cooking.
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are a helpful cooking assistant specializing in recipe creation and cooking advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I couldn't generate recipe suggestions at the moment. Error: {str(e)}"

    async def help_with_recipe_creation(self, user_input: str) -> str:
        """Help users with recipe creation questions"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        prompt = f"""
        As a cooking assistant for the Ondek Recipe app, help the user with their recipe-related question: "{user_input}"

        Provide helpful, practical cooking advice. If they're asking about:
        - Ingredient substitutions
        - Cooking techniques
        - Recipe modifications
        - Serving size adjustments
        - Cooking times and temperatures

        Give specific, actionable advice that they can use in their recipe.
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are a helpful cooking assistant for a recipe management app. Provide practical, accurate cooking advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I couldn't help with that question right now. Error: {str(e)}"

    async def suggest_recipe_improvements(self, recipe_name: str, ingredients: List[Dict],
                                          instructions: List[str]) -> str:
        """Suggest improvements for an existing recipe"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        ingredients_text = "\n".join([f"- {ing['quantity']} {ing['unit']} {ing['name']}" for ing in ingredients])
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
            response = openai.ChatCompletion.create(
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
            return f"Sorry, I couldn't analyze the recipe right now. Error: {str(e)}"

    async def general_cooking_chat(self, message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """Handle general cooking-related conversations"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        messages = [
            {"role": "system",
             "content": "You are a friendly cooking assistant for the Ondek Recipe app. Help users with cooking questions, recipe advice, meal planning, and anything food-related. Be encouraging and helpful!"}
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current message
        messages.append({"role": "user", "content": message})

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=400,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sorry, I couldn't respond right now. Error: {str(e)}"

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
            print(f"Error parsing recipe: {e}")
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
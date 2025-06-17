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
            messages.exten
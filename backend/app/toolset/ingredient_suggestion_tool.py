from .base_imports import *
from .database_search_tool import DatabaseSearchTool


class IngredientSuggestionTool:
    """Tool for finding recipes based on available ingredients"""

    def __init__(self):
        self.name = "get_ingredient_suggestions"
        self.description = "Find recipes that use specific ingredients from user's pantry"

    def execute(self, ingredients: List[str]) -> List[Dict]:
        """Get recipe suggestions based on available ingredients"""
        try:
            if not db_available:
                return []

            recipes_with_ingredients = []
            db_search_tool = DatabaseSearchTool()

            for ingredient in ingredients:
                matching_recipes = db_search_tool.execute({"ingredient": ingredient})
                recipes_with_ingredients.extend(matching_recipes)

            unique_recipes = list({recipe['id']: recipe for recipe in recipes_with_ingredients}.values())
            return unique_recipes

        except Exception as e:
            logger.error(f"Error getting ingredient suggestions: {e}")
            return []
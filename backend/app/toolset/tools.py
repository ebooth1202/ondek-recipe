# backend/app/toolset/tools.py - Tool registry and utilities

from .recipe_search_tool import RecipeSearchTool
from .database_search_tool import DatabaseSearchTool
from .ingredient_suggestion_tool import IngredientSuggestionTool
from .file_parsing_tool import FileParsingTool
from .recipe_formatter_tool import RecipeFormatterTool
from .recipe_scaling_tool import RecipeScalingTool
from .cooking_technique_explainer_tool import CookingTechniqueExplainerTool
from .button_creator_tool import ButtonCreatorTool
from .recipe_cache import recipe_cache

# Tool registry for easy access
TOOLS = {
    'search_external_recipes': RecipeSearchTool(),
    'search_internal_recipes': DatabaseSearchTool(),
    'get_ingredient_suggestions': IngredientSuggestionTool(),
    'parse_recipe_file': FileParsingTool(),
    'format_recipe_data': RecipeFormatterTool(),
    'create_action_buttons': ButtonCreatorTool(),
    'scale_recipe': RecipeScalingTool(),
    'explain_cooking_technique': CookingTechniqueExplainerTool()
}


def get_tool(tool_name: str):
    """Get a tool by name"""
    return TOOLS.get(tool_name)


def list_available_tools():
    """List all available tools"""
    return list(TOOLS.keys())


def get_cache_stats():
    """Get recipe cache statistics"""
    return recipe_cache.get_stats()


def clear_recipe_cache():
    """Clear the recipe cache"""
    recipe_cache.clear()
    return "Recipe cache cleared successfully"
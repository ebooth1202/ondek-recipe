from .base_imports import *
from .recipe_formatter_tool import RecipeFormatterTool


class ButtonCreatorTool:
    """Tool for creating action buttons with preview and website selection functionality"""

    def __init__(self):
        self.name = "create_action_buttons"
        self.description = "Create action buttons with preview and website selection functionality"

        self.supported_websites = [
            {
                "name": "Pinterest",
                "url": "pinterest.com",
                "icon": "📌",
                "color": "#bd081c",
                "description": "Visual recipe discovery platform"
            },
            # {
            #     "name": "AllRecipes",
            #     "url": "allrecipes.com",
            #     "icon": "🥄",
            #     "color": "#e43125",
            #     "description": "Trusted recipe community"
            # },
            # {
            #     "name": "Food Network",
            #     "url": "foodnetwork.com",
            #     "icon": "📺",
            #     "color": "#fa6918",
            #     "description": "Professional chef recipes"
            # },
            {
                "name": "Food.com",
                "url": "food.com",
                "icon": "🍽️",
                "color": "#ff6b35",
                "description": "Community recipe sharing"
            },
            {
                "name": "Epicurious",
                "url": "epicurious.com",
                "icon": "👨‍🍳",
                "color": "#333333",
                "description": "Gourmet cooking magazine"
            },
            # {
            #     "name": "Google",
            #     "url": "google.com",
            #     "icon": "🔍",
            #     "color": "#4285f4",
            #     "description": "Search across all recipe sites"
            # }
        ]

    def create_recipe_buttons(self, recipe: Dict[str, Any], recipe_type: str = "internal") -> List[Dict[str, Any]]:
        """Create both action and preview buttons for a recipe"""
        formatter = RecipeFormatterTool()
        preview_data = formatter.format_for_preview(recipe)

        buttons = []

        if recipe_type == "internal":
            buttons.append({
                "type": "action_button",
                "text": f"View {recipe['name']}",
                "action": "view_recipe",
                "url": f"/recipes/{recipe['id']}",
                "style": "primary",
                "metadata": {
                    "recipe_id": recipe['id'],
                    "recipe_name": recipe['name'],
                    "type": "view_recipe",
                    "source": "internal"
                }
            })
        else:
            # FIXED: For external recipes, include the full recipe data for adding to database
            button_data = {
                "type": "action_button",
                "text": f"Add {recipe.get('name', 'Recipe')}",
                "action": "add_external_recipe",  # Changed from "create_recipe" to be more specific
                "style": "primary",
                "metadata": {
                    "recipe_name": recipe.get('name', 'Unknown Recipe'),
                    "type": "add_external_recipe",
                    "source": "external",
                    "recipe_data": recipe,  # Include the full recipe data
                    "original_url": recipe.get('url', '')  # Keep original URL for reference
                }
            }
            # REMOVED: No longer setting button URL to external recipe URL
            # This ensures the button triggers an action instead of navigating to external URL

            buttons.append(button_data)

        preview_metadata = {
            "recipe_name": recipe.get('name', 'Unknown Recipe'),
            "type": "preview_recipe",
            "source": recipe_type
        }

        if recipe_type == "internal" and 'id' in recipe:
            preview_metadata['recipe_id'] = recipe['id']

        buttons.append({
            "type": "preview_button",
            "text": "📋 Preview",
            "action": "preview_recipe",
            "style": "secondary",
            "preview_data": preview_data,
            "metadata": preview_metadata
        })

        return buttons

    def create_simple_add_button(self) -> Dict[str, Any]:
        """Create a simple add recipe button without preview functionality"""
        return {
            "type": "action_button",
            "text": "Add Recipe",
            "action": "create_recipe",
            "url": "/add-recipe",
            "style": "primary",
            "metadata": {
                "type": "add_recipe_simple",
                "source": "manual"
            }
        }

    def create_search_permission_buttons(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fun Yes/No buttons for search permission"""

        ingredient = search_criteria.get('ingredient', 'recipes')
        if ingredient == 'recipe':
            ingredient = 'recipes'

        return [
            {
                "type": "permission_button",
                "text": f"🌟 Yes! Search for {ingredient}",
                "action": "search_web_yes",
                "style": "success",
                "metadata": {
                    "search_criteria": search_criteria,
                    "permission": "yes",
                    "type": "search_permission"
                }
            },
            {
                "type": "permission_button",
                "text": "😅 Nope, something else!",
                "action": "search_web_no",
                "style": "secondary",
                "metadata": {
                    "permission": "no",
                    "type": "search_permission"
                }
            }
        ]

    def create_website_selection_buttons(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create website selection buttons for external search"""
        logger.info(f"Creating website selection buttons with search_criteria: {search_criteria}")

        buttons = []

        for website in self.supported_websites:
            button = {
                "type": "website_selection_button",
                "text": f"{website['icon']} {website['name']}",
                "action": "search_website",
                "style": "website",
                "metadata": {
                    "website": website['url'],
                    "website_name": website['name'],
                    "search_criteria": search_criteria,
                    "color": website['color'],
                    "description": website['description']
                }
            }
            buttons.append(button)
            logger.info(f"Created button for {website['name']} with action: {button['action']}")

        logger.info(f"Total buttons created: {len(buttons)}")
        return buttons

    def get_website_info(self, website_url: str) -> Optional[Dict[str, Any]]:
        """Get website configuration by URL"""
        for website in self.supported_websites:
            if website['url'] == website_url:
                return website
        return None

    def get_all_supported_websites(self) -> List[Dict[str, Any]]:
        """Get list of all supported websites"""
        return self.supported_websites.copy()

    def create_show_all_button(self, temp_id: str, total_count: int,
                               criteria_description: str, source: str = "internal") -> Dict[str, Any]:
        """Create a 'show all' button for paginated results"""
        action_type = "show_all_external_recipes" if source == "external" else "show_all_recipes"
        button_text = f"Show All {total_count} {'External ' if source == 'external' else ''}Recipes"

        return {
            "type": "action_button",
            "text": button_text,
            "action": action_type,
            "style": "secondary",
            "metadata": {
                "temp_id": temp_id,
                "total_count": total_count,
                "criteria_description": criteria_description,
                "source": source
            }
        }
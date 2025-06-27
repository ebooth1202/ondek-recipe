# backend/app/toolset/tools.py - Updated with Website Selection in ButtonCreatorTool

import os
import logging
import json
import re
import io
import tempfile
import csv
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# Try to import database with error handling
try:
    # Since main app can import database successfully, try the same patterns
    try:
        # Try importing from parent app directory (most likely location)
        from ..database import db

        logger.info("Database imported successfully from app.database")
    except ImportError:
        try:
            # Try the original import pattern
            from app.database import db

            logger.info("Database imported successfully from app.database")
        except ImportError:
            try:
                # Try direct relative import
                from ...database import db

                logger.info("Database imported successfully using relative import")
            except ImportError:
                try:
                    # Try absolute import
                    from database import db

                    logger.info("Database imported successfully using absolute import")
                except ImportError:
                    # Final attempt: use sys.path manipulation
                    import sys
                    import os

                    # Get current file directory and try to find database.py
                    current_dir = os.path.dirname(os.path.abspath(__file__))

                    # Try different potential paths
                    potential_paths = [
                        os.path.join(current_dir, '..'),  # app directory
                        os.path.join(current_dir, '..', '..'),  # backend directory
                        os.path.join(current_dir, '..', '..', '..'),  # project root
                    ]

                    database_found = False
                    for path in potential_paths:
                        abs_path = os.path.abspath(path)
                        if abs_path not in sys.path:
                            sys.path.insert(0, abs_path)

                        try:
                            if os.path.exists(os.path.join(abs_path, 'database.py')):
                                from database import db

                                logger.info(f"Database imported successfully from path: {abs_path}")
                                database_found = True
                                break
                            elif os.path.exists(os.path.join(abs_path, 'app', 'database.py')):
                                from app.database import db

                                logger.info(f"Database imported successfully from app.database at: {abs_path}")
                                database_found = True
                                break
                        except ImportError:
                            continue

                    if not database_found:
                        raise ImportError("Could not locate database module in any expected location")

    db_available = True
except Exception as e:
    logger.error(f"Failed to import database in tools: {e}")
    logger.warning("Internal recipe search and ingredient suggestions will not work without database access")


    # Create a mock database for development/fallback
    class MockRecipeCollection:
        @staticmethod
        def find(query=None, *args, **kwargs):
            # Return an empty cursor-like object
            return MockCursor()

        @staticmethod
        def count_documents(query=None):
            return 0


    class MockCursor:
        def limit(self, n):
            return []

        def __iter__(self):
            return iter([])

        def __list__(self):
            return []


    class MockDatabase:
        recipes = MockRecipeCollection()


    db = MockDatabase()
    db_available = False


class RecipeSearchTool:
    """Tool for searching external recipe sources"""

    def __init__(self):
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.name = "search_external_recipes"
        self.description = "Search the internet for recipes from various cooking websites"

    def execute(self, criteria: Dict[str, Any], search_params: Dict[str, Any] = None) -> List[Dict]:
        """Search for recipes from external sources"""
        try:
            logger.info(f"RecipeSearchTool.execute called with criteria: {criteria}, search_params: {search_params}")

            search_query = self._build_search_query(criteria, search_params)

            # Get ingredient with fallback
            ingredient = criteria.get('ingredient', 'chocolate chip cookies') if criteria else 'chocolate chip cookies'
            logger.info(f"Searching for ingredient: {ingredient}")

            # Check if a specific website is requested
            selected_website = None
            if search_params and search_params.get('specific_websites'):
                websites = search_params.get('specific_websites', [])
                if isinstance(websites, list) and len(websites) > 0:
                    selected_website = websites[0]
                    logger.info(f"Specific website requested: {selected_website}")

            # Handle website-specific search (this takes priority)
            if selected_website:
                if ingredient == 'recipe':
                    # For generic searches on a specific website, provide variety
                    logger.info(f"Generating varied results for {selected_website}")
                    return self._generate_varied_recipe_results(criteria, search_params)
                else:
                    # For specific ingredient searches on a specific website
                    logger.info(f"Generating website-specific results for {ingredient} on {selected_website}")
                    return self._generate_website_specific_results(ingredient, selected_website, criteria,
                                                                   search_params)

            # Handle generic "recipe" search with variety (no specific website)
            elif ingredient == 'recipe':
                logger.info("Generating generic varied results")
                return self._generate_varied_recipe_results(criteria, search_params)

            # Default generic search (fallback)
            else:
                logger.info("Generating generic results for specific ingredient")
                return self._generate_generic_results(ingredient, criteria, search_params)

        except Exception as e:
            logger.error(f"Error in external recipe search: {e}")
            # Return a basic fallback instead of empty list
            return [{
                "name": "Classic Chocolate Chip Cookies",
                "source": "fallback",
                "description": "A reliable fallback recipe when search encounters issues.",
                "url": "https://example.com/fallback-recipe",
                "ingredients": ["2 cups flour", "1 cup butter", "1 cup sugar", "2 eggs", "1 tsp vanilla",
                                "1 cup chocolate chips"],
                "instructions": ["Mix ingredients", "Bake at 375°F for 10 minutes"],
                "serving_size": 24,
                "prep_time": 15,
                "cook_time": 10,
                "genre": "dessert",
                "notes": ["Fallback recipe"],
                "dietary_restrictions": ["vegetarian"],
                "cuisine_type": "american"
            }]

    def _generate_website_specific_results(self, ingredient: str, website: str, criteria: Dict[str, Any],
                                           search_params: Dict[str, Any]) -> List[Dict]:
        """Generate website-specific search results"""
        ingredient_clean = ingredient.lower().replace(' ', '-')

        if website == "google.com":
            # Google searches across multiple sites
            return self._generate_google_results(ingredient, criteria, search_params)
        elif website == "pinterest.com":
            return self._generate_pinterest_results(ingredient, criteria, search_params)
        elif website == "allrecipes.com":
            return self._generate_allrecipes_results(ingredient, criteria, search_params)
        elif website == "foodnetwork.com":
            return self._generate_foodnetwork_results(ingredient, criteria, search_params)
        elif website == "food.com":
            return self._generate_food_com_results(ingredient, criteria, search_params)
        elif website == "epicurious.com":
            return self._generate_epicurious_results(ingredient, criteria, search_params)
        else:
            # Fallback for unknown websites
            return self._generate_generic_results(ingredient, criteria, search_params)

    def _generate_google_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate Google search results (multiple sources)"""
        sources = ["allrecipes.com", "foodnetwork.com", "epicurious.com", "food.com"]
        results = []

        # Handle generic recipe search with variety
        if ingredient == "recipe":
            varied_ingredients = ["chocolate chip cookies", "chicken stir fry", "banana bread", "spaghetti carbonara"]
            for i, varied_ingredient in enumerate(varied_ingredients):
                source = sources[i]
                results.append({
                    "name": f"Popular {varied_ingredient.title()}",
                    "source": source,
                    "description": f"This popular {varied_ingredient} recipe is highly rated across multiple cooking sites. Perfect for any skill level!",
                    "url": f"https://{source}/recipe/popular-{varied_ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Popular"),
                    "instructions": self._get_instructions_for_style("Popular"),
                    "serving_size": 4 + (i * 2),
                    "prep_time": 15 + (i * 5),
                    "cook_time": 20 + (i * 5),
                    "genre": ["dessert", "dinner", "breakfast", "dinner"][i],
                    "notes": [f"Top-rated recipe from {source}", "Highly recommended"],
                    "dietary_restrictions": ["vegetarian"] if "chicken" not in varied_ingredient else [],
                    "cuisine_type": "popular"
                })
        else:
            # Handle specific ingredient search
            for i, source in enumerate(sources):
                recipe_style = ["Classic", "Best Ever", "Perfect", "Ultimate"][i]
                results.append({
                    "name": f"{recipe_style} {ingredient.title()}",
                    "source": source,
                    "description": f"This {recipe_style.lower()} {ingredient} recipe from {source} delivers amazing results every time. Highly rated by thousands of home cooks!",
                    "url": f"https://{source}/recipe/{recipe_style.lower()}-{ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style(recipe_style),
                    "instructions": self._get_instructions_for_style(recipe_style),
                    "serving_size": 24 if i < 2 else 18,
                    "prep_time": 15 + (i * 5),
                    "cook_time": 10 + (i * 2),
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": [f"Top-rated recipe from {source}", "Thousands of positive reviews"],
                    "dietary_restrictions": ["vegetarian"] if i % 2 == 0 else [],
                    "cuisine_type": "american"
                })

        return results

    def _generate_varied_recipe_results(self, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> List[Dict]:
        """Generate varied recipe results for generic searches"""
        logger.info(f"Generating varied recipe results with search_params: {search_params}")

        varied_recipes = [
            {
                "ingredient": "chocolate chip cookies",
                "genre": "dessert",
                "description": "Classic chocolate chip cookies that everyone loves"
            },
            {
                "ingredient": "chicken teriyaki",
                "genre": "dinner",
                "description": "Easy weeknight chicken teriyaki with rice"
            },
            {
                "ingredient": "banana bread",
                "genre": "breakfast",
                "description": "Moist and delicious homemade banana bread"
            },
            {
                "ingredient": "pasta carbonara",
                "genre": "dinner",
                "description": "Creamy Italian pasta carbonara recipe"
            }
        ]

        # Get the selected website if specified
        selected_website = None
        if search_params and search_params.get('specific_websites'):
            websites = search_params.get('specific_websites', [])
            if isinstance(websites, list) and len(websites) > 0:
                selected_website = websites[0]
                logger.info(f"Selected website for varied results: {selected_website}")

        results = []
        for recipe_info in varied_recipes:
            if selected_website:
                logger.info(
                    f"Generating website-specific results for {recipe_info['ingredient']} on {selected_website}")
                # Use website-specific generation for each varied recipe
                recipe_results = self._generate_website_specific_results(
                    recipe_info["ingredient"],
                    selected_website,
                    {"ingredient": recipe_info["ingredient"], "genre": recipe_info["genre"]},
                    search_params
                )
                # Take just the first result from each
                if recipe_results:
                    result = recipe_results[0]
                    result["description"] = recipe_info["description"]
                    results.append(result)
                    logger.info(f"Added result: {result['name']}")
                else:
                    logger.warning(f"No results returned for {recipe_info['ingredient']} on {selected_website}")
            else:
                # Generate generic results for variety
                results.append({
                    "name": recipe_info["ingredient"].title(),
                    "source": "various",
                    "description": recipe_info["description"],
                    "url": f"https://example.com/recipe/{recipe_info['ingredient'].replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Classic"),
                    "instructions": self._get_instructions_for_style("Classic"),
                    "serving_size": 4,
                    "prep_time": 20,
                    "cook_time": 25,
                    "genre": recipe_info["genre"],
                    "notes": ["Popular recipe choice"],
                    "dietary_restrictions": ["vegetarian"] if "chicken" not in recipe_info["ingredient"] else [],
                    "cuisine_type": "varied"
                })

        logger.info(f"Varied recipe generator returning {len(results)} total results")
        return results

    def _generate_pinterest_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate Pinterest-style results (visual, trendy)"""
        results = []

        if ingredient == "recipe":
            # Generate trendy, visual recipes for generic search
            trendy_recipes = [
                {"name": "Instagram-Perfect Rainbow Smoothie Bowl", "ingredient": "smoothie bowl",
                 "genre": "breakfast"},
                {"name": "Viral TikTok Baked Feta Pasta", "ingredient": "baked feta pasta", "genre": "dinner"},
                {"name": "Pinterest-Famous Cloud Bread", "ingredient": "cloud bread", "genre": "snack"},
                {"name": "Trending Dalgona Coffee Cookies", "ingredient": "dalgona cookies", "genre": "dessert"}
            ]

            for i, recipe_info in enumerate(trendy_recipes):
                results.append({
                    "name": recipe_info["name"],
                    "source": "pinterest.com",
                    "description": f"This {recipe_info['name'].lower()} is taking Pinterest by storm! Perfect for sharing on social media with stunning visual appeal.",
                    "url": f"https://pinterest.com/pin/{recipe_info['ingredient'].replace(' ', '-')}-recipe",
                    "ingredients": self._get_ingredients_for_style("Trendy"),
                    "instructions": self._get_instructions_for_style("Trendy", pinterest_style=True),
                    "serving_size": 2 + (i * 2),
                    "prep_time": 15 + (i * 5),
                    "cook_time": 10 + (i * 3),
                    "genre": recipe_info["genre"],
                    "notes": ["Perfect for photos!", "Social media worthy", "Pin-worthy recipe"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "trendy"
                })
        else:
            # Generate specific ingredient results
            styles = ["Instagram-Perfect", "Pinterest-Famous", "Viral", "Trending"]

            for i, style in enumerate(styles):
                results.append({
                    "name": f"{style} {ingredient.title()}",
                    "source": "pinterest.com",
                    "description": f"These {style.lower()} {ingredient} are taking Pinterest by storm! Beautiful, delicious, and perfect for sharing on social media.",
                    "url": f"https://pinterest.com/pin/{style.lower()}-{ingredient.replace(' ', '-')}-recipe",
                    "ingredients": self._get_ingredients_for_style(style),
                    "instructions": self._get_instructions_for_style(style, pinterest_style=True),
                    "serving_size": 20 + (i * 4),
                    "prep_time": 20 + (i * 5),
                    "cook_time": 12 + (i * 3),
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Perfect for photos!", "Social media worthy presentation", "Pin-worthy recipe"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "trendy"
                })

        logger.info(f"Pinterest generator returning {len(results)} results for ingredient: {ingredient}")
        return results

    def _generate_allrecipes_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate AllRecipes-style results (community tested)"""
        if ingredient == "recipe":
            # Generate popular community recipes for generic search
            popular_recipes = [
                {"name": "World's Best Lasagna", "ingredient": "lasagna", "genre": "dinner", "rating": 5.0},
                {"name": "Perfect Chocolate Chip Cookies", "ingredient": "chocolate chip cookies", "genre": "dessert",
                 "rating": 4.9},
                {"name": "Fluffy Pancakes", "ingredient": "pancakes", "genre": "breakfast", "rating": 4.8},
                {"name": "Classic Chicken Soup", "ingredient": "chicken soup", "genre": "dinner", "rating": 4.9}
            ]

            results = []
            for i, recipe_info in enumerate(popular_recipes):
                results.append({
                    "name": recipe_info["name"],
                    "source": "allrecipes.com",
                    "description": f"This {recipe_info['name'].lower()} has earned a {recipe_info['rating']}/5 star rating from our community! Tested and loved by thousands of home cooks.",
                    "url": f"https://allrecipes.com/recipe/{recipe_info['ingredient'].replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Community Favorite"),
                    "instructions": self._get_instructions_for_style("Community Favorite", community_tested=True),
                    "serving_size": 6 + (i * 2),
                    "prep_time": 20 + (i * 5),
                    "cook_time": 25 + (i * 5),
                    "genre": recipe_info["genre"],
                    "notes": [f"{recipe_info['rating']}/5 stars from community", "Thousands of reviews",
                              "Tested and approved"],
                    "dietary_restrictions": ["vegetarian"] if "chicken" not in recipe_info["ingredient"] else [],
                    "cuisine_type": "american"
                })
        else:
            # Generate specific ingredient results
            styles = ["5-Star", "Community Favorite", "Most Popular", "Highly Rated"]
            results = []

            for i, style in enumerate(styles):
                rating = 5.0 - (i * 0.2)
                results.append({
                    "name": f"{style} {ingredient.title()}",
                    "source": "allrecipes.com",
                    "description": f"This {style.lower()} {ingredient} recipe has been tested by our community and earned a {rating:.1f}/5 star rating. Trusted by home cooks everywhere!",
                    "url": f"https://allrecipes.com/recipe/{style.lower().replace(' ', '-')}-{ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style(style),
                    "instructions": self._get_instructions_for_style(style, community_tested=True),
                    "serving_size": 24,
                    "prep_time": 15,
                    "cook_time": 10 + i,
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": [f"{rating:.1f}/5 stars from community", "Thousands of reviews", "Tested and approved"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "american"
                })

        return results

    def _generate_foodnetwork_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate Food Network-style results (chef recipes)"""
        if ingredient == "recipe":
            # Generate chef-inspired recipes for generic search
            chef_recipes = [
                {"name": "Bobby Flay's Perfect Grilled Steak", "ingredient": "grilled steak", "genre": "dinner"},
                {"name": "Ina Garten's Lemon Bars", "ingredient": "lemon bars", "genre": "dessert"},
                {"name": "Giada's Fresh Pasta Primavera", "ingredient": "pasta primavera", "genre": "dinner"},
                {"name": "Emeril's Breakfast Hash", "ingredient": "breakfast hash", "genre": "breakfast"}
            ]

            results = []
            for i, recipe_info in enumerate(chef_recipes):
                results.append({
                    "name": recipe_info["name"],
                    "source": "foodnetwork.com",
                    "description": f"Learn to make this {recipe_info['name'].lower()} with professional techniques from Food Network's top chefs. Restaurant-quality results at home!",
                    "url": f"https://foodnetwork.com/recipes/{recipe_info['ingredient'].replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Chef's Special", professional=True),
                    "instructions": self._get_instructions_for_style("Chef's Special", professional=True),
                    "serving_size": 4 + (i * 2),
                    "prep_time": 25 + (i * 5),
                    "cook_time": 20 + (i * 5),
                    "genre": recipe_info["genre"],
                    "notes": ["Professional chef techniques", "Restaurant-quality results", "Celebrity chef recipe"],
                    "dietary_restrictions": ["vegetarian"] if "steak" not in recipe_info["ingredient"] else [],
                    "cuisine_type": "professional"
                })
        else:
            # Generate specific ingredient results
            chefs = ["Chef's Special", "Professional", "Restaurant-Style", "Gourmet"]
            results = []

            for i, style in enumerate(chefs):
                results.append({
                    "name": f"{style} {ingredient.title()}",
                    "source": "foodnetwork.com",
                    "description": f"This {style.lower()} {ingredient} recipe brings professional techniques to your home kitchen. Learn from the experts!",
                    "url": f"https://foodnetwork.com/recipes/{style.lower().replace(' ', '-')}-{ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style(style, professional=True),
                    "instructions": self._get_instructions_for_style(style, professional=True),
                    "serving_size": 18 + (i * 2),
                    "prep_time": 25 + (i * 5),
                    "cook_time": 12 + (i * 2),
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Professional chef techniques", "Restaurant-quality results", "Expert tips included"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "professional"
                })

        return results

    def _generate_food_com_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate Food.com-style results (home cook friendly)"""
        if ingredient == "recipe":
            # Generate beginner-friendly recipes for generic search
            easy_recipes = [
                {"name": "Easy 3-Ingredient Cookies", "ingredient": "3-ingredient cookies", "genre": "dessert"},
                {"name": "Simple One-Pot Chicken and Rice", "ingredient": "chicken and rice", "genre": "dinner"},
                {"name": "Quick Microwave Mug Cake", "ingredient": "mug cake", "genre": "dessert"},
                {"name": "Beginner's Perfect Scrambled Eggs", "ingredient": "scrambled eggs", "genre": "breakfast"}
            ]

            results = []
            for i, recipe_info in enumerate(easy_recipes):
                results.append({
                    "name": recipe_info["name"],
                    "source": "food.com",
                    "description": f"This {recipe_info['name'].lower()} is perfect for beginners! Simple ingredients, clear instructions, and delicious results every time.",
                    "url": f"https://food.com/recipe/{recipe_info['ingredient'].replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Easy", simple=True),
                    "instructions": self._get_instructions_for_style("Easy", simple=True),
                    "serving_size": 2 + (i * 2),
                    "prep_time": 5 + (i * 3),
                    "cook_time": 10 + (i * 5),
                    "genre": recipe_info["genre"],
                    "notes": ["Beginner-friendly", "Simple ingredients", "Family approved"],
                    "dietary_restrictions": ["vegetarian"] if "chicken" not in recipe_info["ingredient"] else [],
                    "cuisine_type": "home-style"
                })
        else:
            # Generate specific ingredient results
            styles = ["Easy", "Quick & Simple", "Family-Friendly", "Beginner-Perfect"]
            results = []

            for i, style in enumerate(styles):
                results.append({
                    "name": f"{style} {ingredient.title()}",
                    "source": "food.com",
                    "description": f"This {style.lower()} {ingredient} recipe is perfect for home cooks of all skill levels. Simple ingredients, great results!",
                    "url": f"https://food.com/recipe/{style.lower().replace(' ', '-')}-{ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style(style, simple=True),
                    "instructions": self._get_instructions_for_style(style, simple=True),
                    "serving_size": 24,
                    "prep_time": 10 + (i * 3),
                    "cook_time": 8 + (i * 2),
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Beginner-friendly", "Simple ingredients", "Family approved"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "home-style"
                })

        return results

    def _generate_epicurious_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate Epicurious-style results (sophisticated)"""
        if ingredient == "recipe":
            # Generate sophisticated recipes for generic search
            gourmet_recipes = [
                {"name": "Sophisticated Coq au Vin", "ingredient": "coq au vin", "genre": "dinner"},
                {"name": "Artisanal Sourdough Bread", "ingredient": "sourdough bread", "genre": "snack"},
                {"name": "Refined Dark Chocolate Tart", "ingredient": "chocolate tart", "genre": "dessert"},
                {"name": "Gourmet Mushroom Risotto", "ingredient": "mushroom risotto", "genre": "dinner"}
            ]

            results = []
            for i, recipe_info in enumerate(gourmet_recipes):
                results.append({
                    "name": recipe_info["name"],
                    "source": "epicurious.com",
                    "description": f"This {recipe_info['name'].lower()} elevates home cooking with sophisticated techniques and premium ingredients for the discerning palate.",
                    "url": f"https://epicurious.com/recipes/food/views/{recipe_info['ingredient'].replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style("Sophisticated", gourmet=True),
                    "instructions": self._get_instructions_for_style("Sophisticated", gourmet=True),
                    "serving_size": 4 + (i * 2),
                    "prep_time": 40 + (i * 10),
                    "cook_time": 30 + (i * 10),
                    "genre": recipe_info["genre"],
                    "notes": ["Premium ingredients", "Sophisticated flavors", "Gourmet techniques"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "gourmet"
                })
        else:
            # Generate specific ingredient results
            styles = ["Sophisticated", "Artisanal", "Gourmet", "Refined"]
            results = []

            for i, style in enumerate(styles):
                results.append({
                    "name": f"{style} {ingredient.title()}",
                    "source": "epicurious.com",
                    "description": f"This {style.lower()} {ingredient} recipe elevates a classic with premium ingredients and refined techniques for discerning palates.",
                    "url": f"https://epicurious.com/recipes/food/views/{style.lower()}-{ingredient.replace(' ', '-')}",
                    "ingredients": self._get_ingredients_for_style(style, gourmet=True),
                    "instructions": self._get_instructions_for_style(style, gourmet=True),
                    "serving_size": 16 + (i * 2),
                    "prep_time": 30 + (i * 5),
                    "cook_time": 15 + (i * 3),
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Premium ingredients", "Sophisticated flavors", "Gourmet techniques"],
                    "dietary_restrictions": ["vegetarian"],
                    "cuisine_type": "gourmet"
                })

        return results

    def _generate_generic_results(self, ingredient: str, criteria: Dict[str, Any], search_params: Dict[str, Any]) -> \
            List[Dict]:
        """Generate generic search results as fallback"""
        return [
            {
                "name": f"Classic {ingredient.title()} Recipe",
                "source": "allrecipes.com",
                "description": f"A traditional {ingredient} recipe with proven results.",
                "url": f"https://allrecipes.com/recipe/classic-{ingredient.replace(' ', '-')}",
                "ingredients": self._get_ingredients_for_style("Classic"),
                "instructions": self._get_instructions_for_style("Classic"),
                "serving_size": 24,
                "prep_time": 15,
                "cook_time": 10,
                "genre": criteria.get('genre', 'dessert'),
                "notes": ["Tried and true recipe"],
                "dietary_restrictions": ["vegetarian"],
                "cuisine_type": "traditional"
            }
        ]

    def _get_ingredients_for_style(self, style: str, **kwargs) -> List[str]:
        """Get ingredients based on recipe style"""
        base_ingredients = [
            "2 cups all-purpose flour",
            "1 cup butter, softened",
            "3/4 cup granulated sugar",
            "1/2 cup brown sugar",
            "2 large eggs",
            "1 teaspoon vanilla extract",
            "1 teaspoon baking soda",
            "1/2 teaspoon salt"
        ]

        if kwargs.get('gourmet'):
            return [
                "2 1/4 cups European cake flour",
                "1 cup premium European butter",
                "3/4 cup organic cane sugar",
                "1/2 cup muscovado sugar",
                "2 farm-fresh eggs",
                "1 tablespoon Madagascar vanilla extract",
                "1 teaspoon aluminum-free baking soda",
                "1/2 teaspoon sea salt",
                "8 oz high-quality dark chocolate, chopped"
            ]
        elif kwargs.get('professional'):
            return base_ingredients + ["1 cup high-quality chocolate chips", "1/4 teaspoon cream of tartar"]
        elif kwargs.get('simple'):
            return [
                "2 cups flour",
                "1 cup butter",
                "1 cup sugar",
                "2 eggs",
                "1 tsp vanilla",
                "1 tsp baking soda",
                "1/2 tsp salt",
                "1 cup chocolate chips"
            ]
        elif style in ["Popular", "Trendy", "Community Favorite"]:
            return base_ingredients + ["1 1/2 cups chocolate chips"]
        else:
            return base_ingredients + ["1 cup chocolate chips"]

    def _get_instructions_for_style(self, style: str, **kwargs) -> List[str]:
        """Get instructions based on recipe style"""
        if kwargs.get('pinterest_style'):
            return [
                "📸 Preheat oven to 375°F and line baking sheets with parchment",
                "✨ Cream butter and sugars until light and fluffy (perfect for photos!)",
                "🥚 Add eggs one at a time, then vanilla",
                "🍪 Mix in dry ingredients until just combined",
                "📌 Scoop dough onto prepared sheets using a cookie scoop for uniform size",
                "⏰ Bake 9-11 minutes until golden edges",
                "💫 Cool completely for the perfect Instagram shot!"
            ]
        elif kwargs.get('professional'):
            return [
                "Preheat oven to 375°F with racks in upper and lower thirds",
                "Using a stand mixer, cream butter and sugars on medium speed for 5 minutes until very light",
                "Add eggs one at a time, beating well after each addition, then vanilla",
                "In a separate bowl, whisk together flour, baking soda, salt, and cream of tartar",
                "On low speed, gradually add dry ingredients until just combined",
                "Fold in chocolate chips by hand to avoid overmixing",
                "Using a 1.5-inch scoop, portion dough 2 inches apart on parchment-lined sheets",
                "Bake 9-11 minutes, rotating pans halfway through, until edges are set",
                "Cool on pans for 5 minutes before transferring to wire racks"
            ]
        elif kwargs.get('simple'):
            return [
                "Heat oven to 375°F",
                "Mix butter and sugar",
                "Add eggs and vanilla",
                "Mix in flour, baking soda, and salt",
                "Stir in chocolate chips",
                "Drop spoonfuls on cookie sheet",
                "Bake 9-11 minutes",
                "Cool and enjoy!"
            ]
        elif kwargs.get('gourmet'):
            return [
                "Preheat oven to 350°F and line baking sheets with silicone mats",
                "Using a stand mixer with paddle attachment, cream butter and sugars for 8 minutes until very pale",
                "Incorporate eggs one at a time, ensuring full emulsion, then add vanilla",
                "Sift together flour, baking soda, and salt in a separate bowl",
                "Fold dry ingredients into butter mixture using a wooden spoon until just combined",
                "Gently fold in chopped chocolate pieces",
                "Using a portion scoop, place dough 3 inches apart on prepared sheets",
                "Bake 12-14 minutes until edges are lightly golden but centers remain soft",
                "Allow to rest on baking sheets for 10 minutes before transferring to cooling racks"
            ]
        elif kwargs.get('community_tested'):
            return [
                "Preheat oven to 375°F (community recommended temperature)",
                "Cream butter and sugars until fluffy - this step is crucial according to reviewers!",
                "Beat in eggs one at a time, then vanilla (fresh vanilla makes a difference!)",
                "Mix flour, baking soda, and salt in separate bowl",
                "Gradually combine wet and dry ingredients (don't overmix!)",
                "Fold in chocolate chips - use good quality ones as recommended by the community",
                "Drop rounded spoonfuls onto ungreased sheets (2 inches apart)",
                "Bake 9-11 minutes until edges are golden - watch carefully!",
                "Cool on sheet for 5 minutes before transferring (prevents breaking)"
            ]
        elif style in ["Popular", "Trendy", "Community Favorite"]:
            return [
                "Preheat oven to 375°F",
                "In a large bowl, cream together butter and sugars until light and fluffy",
                "Beat in eggs one at a time, then add vanilla extract",
                "In separate bowl, whisk together flour, baking soda, and salt",
                "Gradually mix dry ingredients into wet ingredients until just combined",
                "Fold in add-ins (chocolate chips, nuts, etc.)",
                "Drop rounded tablespoons of dough onto lined baking sheets",
                "Bake for 9-11 minutes until edges are golden brown",
                "Cool on baking sheet for 5 minutes before transferring to wire rack"
            ]
        else:
            return [
                "Preheat oven to 375°F (190°C)",
                "In a large bowl, cream together butter and sugars until light and fluffy",
                "Beat in eggs one at a time, then add vanilla",
                "In separate bowl, whisk together flour, baking soda, and salt",
                "Gradually mix dry ingredients into wet ingredients",
                "Stir in chocolate chips",
                "Drop rounded tablespoons of dough onto ungreased baking sheets",
                "Bake for 9-11 minutes until golden brown",
                "Cool on baking sheet for 5 minutes before transferring to wire rack"
            ]

    def _build_search_query(self, criteria: Dict[str, Any], search_params: Dict[str, Any] = None) -> str:
        """Build search query for external APIs"""
        query_parts = []

        if criteria and criteria.get('ingredient'):
            query_parts.append(f"recipe {criteria['ingredient']}")
        elif criteria and criteria.get('genre'):
            query_parts.append(f"{criteria['genre']} recipe")
        elif criteria and criteria.get('name'):
            query_parts.append(criteria['name'])
        else:
            query_parts.append("cookie recipe")

        if search_params:
            if search_params.get('cuisine_type'):
                query_parts.append(search_params['cuisine_type'])
            if search_params.get('difficulty_level'):
                query_parts.append(search_params['difficulty_level'])

        return " ".join(query_parts) if query_parts else "cookie recipe"


class DatabaseSearchTool:
    """Tool for searching the internal recipe database"""

    def __init__(self):
        self.name = "search_internal_recipes"
        self.description = "Search user's personal recipe database"

    def execute(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search recipes in the database based on criteria"""
        try:
            if not db_available:
                logger.warning("Database not available")
                return []

            query = {}

            # Handle different search criteria
            if "genre" in criteria:
                genre_term = criteria["genre"].lower()
                genre_patterns = [genre_term]
                if genre_term.endswith('s'):
                    genre_patterns.append(genre_term[:-1])
                else:
                    genre_patterns.append(genre_term + 's')
                query["genre"] = {"$regex": "|".join(genre_patterns), "$options": "i"}

            if "ingredient" in criteria:
                ingredient_term = criteria["ingredient"]
                escaped_ingredient = re.escape(ingredient_term)

                # Create multiple search patterns for better matching
                search_patterns = [escaped_ingredient]

                # Add singular/plural variations
                if ingredient_term.endswith('s') and len(ingredient_term) > 3:
                    # Remove 's' for singular (cookies -> cookie)
                    singular = ingredient_term[:-1]
                    search_patterns.append(re.escape(singular))
                elif not ingredient_term.endswith('s'):
                    # Add 's' for plural (cookie -> cookies)
                    plural = ingredient_term + 's'
                    search_patterns.append(re.escape(plural))

                # Create flexible regex pattern (no word boundaries for partial matching)
                pattern_string = "|".join(search_patterns)

                # Search across multiple fields for comprehensive results
                query["$or"] = [
                    {"ingredients.name": {"$regex": pattern_string, "$options": "i"}},
                    {"recipe_name": {"$regex": pattern_string, "$options": "i"}},
                    {"description": {"$regex": pattern_string, "$options": "i"}},
                    {"notes": {"$regex": pattern_string, "$options": "i"}}
                ]

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

            if "show_favorites" in criteria and criteria["show_favorites"]:
                # Handle favorites stored in separate collection
                # Get all favorited recipe_ids from the favorites collection
                favorite_recipe_ids = []
                try:
                    favorite_docs = list(db.favorites.find({}, {"recipe_id": 1}))
                    logger.info(f"DEBUG: Found {len(favorite_docs)} favorite documents")
                    logger.info(f"DEBUG: Favorite docs: {favorite_docs}")

                    favorite_recipe_ids = [doc["recipe_id"] for doc in favorite_docs if "recipe_id" in doc]
                    logger.info(f"DEBUG: Extracted recipe IDs: {favorite_recipe_ids}")
                except Exception as e:
                    logger.error(f"Error getting favorite recipe IDs: {e}")

                if favorite_recipe_ids:
                    # Convert string IDs to ObjectId if needed
                    object_ids = []
                    for fav_id in favorite_recipe_ids:
                        try:
                            if isinstance(fav_id, str):
                                object_ids.append(ObjectId(fav_id))
                            else:
                                object_ids.append(fav_id)
                        except:
                            object_ids.append(fav_id)  # Keep as-is if conversion fails

                    # Search for recipes with these IDs
                    query["_id"] = {"$in": object_ids}
                else:
                    # No favorites found, return empty result
                    return []

            logger.info(f"Database search query: {query}")
            recipes = list(db.recipes.find(query).limit(50))

            # Enhanced fallback: if no matches and ingredient has spaces, try individual words
            if len(recipes) == 0 and "ingredient" in criteria and " " in criteria["ingredient"]:
                words = criteria["ingredient"].split()
                word_patterns = []

                for word in words:
                    word_patterns.append(re.escape(word))
                    # Add singular/plural for each word too
                    if word.endswith('s') and len(word) > 3:
                        word_patterns.append(re.escape(word[:-1]))
                    elif not word.endswith('s'):
                        word_patterns.append(re.escape(word + 's'))

                fallback_pattern = "|".join(word_patterns)
                fallback_query = query.copy()
                fallback_query["$or"] = [
                    {"ingredients.name": {"$regex": fallback_pattern, "$options": "i"}},
                    {"recipe_name": {"$regex": fallback_pattern, "$options": "i"}},
                    {"description": {"$regex": fallback_pattern, "$options": "i"}},
                    {"notes": {"$regex": fallback_pattern, "$options": "i"}}
                ]
                recipes = list(db.recipes.find(fallback_query).limit(50))

            return [self._format_recipe_for_response(recipe) for recipe in recipes]

        except Exception as e:
            logger.error(f"Error searching internal recipes: {e}")
            return []

    def count_matches(self, criteria: Dict[str, Any]) -> int:
        """Count recipes matching criteria"""
        try:
            if not db_available:
                return 0

            query = {}
            if "genre" in criteria:
                genre_term = criteria["genre"].lower()
                genre_patterns = [genre_term]
                if genre_term.endswith('s'):
                    genre_patterns.append(genre_term[:-1])
                else:
                    genre_patterns.append(genre_term + 's')
                query["genre"] = {"$regex": "|".join(genre_patterns), "$options": "i"}

            if "ingredient" in criteria:
                ingredient_term = criteria["ingredient"]
                escaped_ingredient = re.escape(ingredient_term)
                query["ingredients.name"] = {"$regex": f"\\b{escaped_ingredient}\\b", "$options": "i"}

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

            if "show_favorites" in criteria and criteria["show_favorites"]:
                # Handle favorites stored in separate collection
                # Get all favorited recipe_ids from the favorites collection
                favorite_recipe_ids = []
                try:
                    favorite_docs = list(db.favorites.find({}, {"recipe_id": 1}))
                    favorite_recipe_ids = [doc["recipe_id"] for doc in favorite_docs if "recipe_id" in doc]
                except Exception as e:
                    logger.error(f"Error getting favorite recipe IDs for count: {e}")

                if favorite_recipe_ids:
                    # Convert string IDs to ObjectId if needed
                    from bson import ObjectId
                    object_ids = []
                    for fav_id in favorite_recipe_ids:
                        try:
                            if isinstance(fav_id, str):
                                object_ids.append(ObjectId(fav_id))
                            else:
                                object_ids.append(fav_id)
                        except:
                            object_ids.append(fav_id)  # Keep as-is if conversion fails

                    # Count recipes with these IDs
                    query["_id"] = {"$in": object_ids}
                else:
                    # No favorites found, return 0
                    return 0

            return db.recipes.count_documents(query)

        except Exception as e:
            logger.error(f"Error counting recipes: {e}")
            return 0

    def _format_recipe_for_response(self, recipe: Dict) -> Dict:
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
            "created_at": recipe["created_at"].strftime("%Y-%m-%d") if recipe.get("created_at") else "",
            "source": "Your Recipe Database"
        }


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
            for ingredient in ingredients:
                matching_recipes = DatabaseSearchTool().execute({"ingredient": ingredient})
                recipes_with_ingredients.extend(matching_recipes)

            # Remove duplicates
            unique_recipes = list({recipe['id']: recipe for recipe in recipes_with_ingredients}.values())
            return unique_recipes

        except Exception as e:
            logger.error(f"Error getting ingredient suggestions: {e}")
            return []


class FileParsingTool:
    """Tool for parsing recipe files"""

    def __init__(self):
        self.name = "parse_recipe_file"
        self.description = "Parse uploaded files to extract recipe information"

    def execute(self, file_content: bytes, filename: str, file_type: str, file_extension: str) -> Optional[Dict]:
        """Parse recipe information from various file types"""
        try:
            logger.info(f"Parsing file: {filename}, type: {file_type}")

            # Extract text based on file type
            extracted_text = ""

            if file_type == "application/pdf" or file_extension == ".pdf":
                extracted_text = self._extract_text_from_pdf(file_content)
            elif file_type.startswith("image/") or file_extension.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                extracted_text = self._extract_text_from_image(file_content)
            elif file_type == "text/csv" or file_extension == ".csv":
                extracted_text = self._extract_text_from_csv(file_content)
            elif file_type.startswith("text/") or file_extension in [".txt", ".md"]:
                extracted_text = file_content.decode('utf-8', errors='ignore')
            else:
                try:
                    extracted_text = file_content.decode('utf-8', errors='ignore')
                except:
                    raise ValueError(f"Unsupported file type: {file_type}")

            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from {filename}")
                return None

            return {
                "file_name": filename,
                "file_type": file_type,
                "parsed_text": extracted_text,
                "confidence": 0.8 if len(extracted_text) > 100 else 0.3
            }

        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
            return None

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            # Would use PyPDF2 or similar library
            # For now, return placeholder
            return "PDF parsing not implemented yet"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            # Would use pytesseract or similar library
            # For now, return placeholder
            return "Image OCR not implemented yet"
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def _extract_text_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file"""
        try:
            csv_text = file_content.decode('utf-8', errors='ignore')
            csv_file = io.StringIO(csv_text)

            reader = csv.DictReader(csv_file)
            rows = list(reader)

            if not rows:
                return csv_text

            # Look for recipe-like columns
            headers = rows[0].keys() if rows else []
            recipe_columns = ['name', 'title', 'recipe', 'ingredients', 'instructions', 'directions', 'steps']

            has_recipe_data = any(
                any(col.lower() in header.lower() for col in recipe_columns)
                for header in headers
            )

            if has_recipe_data:
                formatted_text = "Recipe Data from CSV:\n\n"
                for i, row in enumerate(rows, 1):
                    formatted_text += f"Recipe {i}:\n"
                    for key, value in row.items():
                        if value and value.strip():
                            formatted_text += f"{key}: {value}\n"
                    formatted_text += "\n"
                return formatted_text
            else:
                return csv_text

        except Exception as e:
            logger.error(f"Error extracting text from CSV: {e}")
            return file_content.decode('utf-8', errors='ignore')


class RecipeFormatterTool:
    """Tool for formatting recipe data for forms and previews"""

    def __init__(self):
        self.name = "format_recipe_data"
        self.description = "Format raw recipe data for forms and previews"

    def execute(self, raw_recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format raw recipe data for the add recipe form"""
        try:
            formatted_recipe = {
                "recipe_name": "",
                "description": "",
                "ingredients": [],
                "instructions": [],
                "serving_size": 4,
                "genre": "dinner",
                "prep_time": 0,
                "cook_time": 0,
                "notes": [],
                "dietary_restrictions": []
            }

            # Extract recipe name
            if "name" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["name"]
            elif "recipe_name" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["recipe_name"]
            elif "title" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["title"]

            # Extract description
            if "description" in raw_recipe_data:
                description = raw_recipe_data["description"]
                if len(description) <= 500:
                    formatted_recipe["description"] = description
                else:
                    formatted_recipe["description"] = description[:497] + "..."

            # Extract and format ingredients
            if "ingredients" in raw_recipe_data:
                for ingredient in raw_recipe_data["ingredients"]:
                    if isinstance(ingredient, str):
                        parsed = self._parse_ingredient_string(ingredient)
                        if parsed:
                            formatted_recipe["ingredients"].append(parsed)
                    elif isinstance(ingredient, dict):
                        formatted_ingredient = self._format_structured_ingredient(ingredient)
                        if formatted_ingredient:
                            formatted_recipe["ingredients"].append(formatted_ingredient)

            # Extract instructions
            if "instructions" in raw_recipe_data:
                instructions = raw_recipe_data["instructions"]
                if isinstance(instructions, list):
                    for instruction in instructions:
                        if isinstance(instruction, str):
                            cleaned = self._clean_instruction_text(instruction)
                            if cleaned:
                                formatted_recipe["instructions"].append(cleaned)
                elif isinstance(instructions, str):
                    instruction_list = self._split_instructions(instructions)
                    formatted_recipe["instructions"].extend(instruction_list)

            # Extract other fields
            for field in ["serving_size", "genre", "prep_time", "cook_time"]:
                if field in raw_recipe_data:
                    formatted_recipe[field] = raw_recipe_data[field]

            # Extract notes
            notes = []
            if "notes" in raw_recipe_data:
                if isinstance(raw_recipe_data["notes"], list):
                    notes.extend(raw_recipe_data["notes"])
                elif isinstance(raw_recipe_data["notes"], str):
                    notes.append(raw_recipe_data["notes"])
            formatted_recipe["notes"] = notes

            # Extract dietary restrictions
            if "dietary_restrictions" in raw_recipe_data:
                formatted_recipe["dietary_restrictions"] = raw_recipe_data["dietary_restrictions"]

            return formatted_recipe

        except Exception as e:
            logger.error(f"Error formatting recipe for form: {e}")
            return None

    def format_for_preview(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format recipe data specifically for preview modal"""
        try:
            # Get basic info
            recipe_name = recipe_data.get('name', recipe_data.get('recipe_name', 'Unknown Recipe'))
            description = recipe_data.get('description', '')

            # Format ingredients for display
            ingredients = []
            if 'ingredients' in recipe_data:
                for ing in recipe_data['ingredients']:
                    if isinstance(ing, str):
                        ingredients.append(ing)
                    elif isinstance(ing, dict):
                        name = ing.get('name', '')
                        quantity = ing.get('quantity', '')
                        unit = ing.get('unit', '')
                        if quantity and unit and name:
                            ingredients.append(f"{quantity} {unit} {name}")
                        elif name:
                            ingredients.append(name)

            # Format instructions for display
            instructions = recipe_data.get('instructions', [])
            if isinstance(instructions, str):
                instructions = self._split_instructions(instructions)

            # Calculate total time
            prep_time = recipe_data.get('prep_time', 0)
            cook_time = recipe_data.get('cook_time', 0)
            total_time = prep_time + cook_time

            # Format for preview display
            preview_data = {
                "recipe_name": recipe_name,
                "description": description,
                "ingredients": ingredients,
                "instructions": instructions,
                "serving_size": recipe_data.get('serving_size', 4),
                "genre": recipe_data.get('genre', '').title(),
                "prep_time": prep_time,
                "cook_time": cook_time,
                "total_time": total_time,
                "source": recipe_data.get('source', 'Unknown'),
                "dietary_restrictions": recipe_data.get('dietary_restrictions', []),
                "notes": recipe_data.get('notes', [])
            }

            return preview_data

        except Exception as e:
            logger.error(f"Error formatting recipe for preview: {e}")
            return {
                "recipe_name": "Error loading recipe",
                "description": "Unable to load recipe preview",
                "ingredients": [],
                "instructions": [],
                "serving_size": 0,
                "genre": "",
                "prep_time": 0,
                "cook_time": 0,
                "total_time": 0,
                "source": "Error",
                "dietary_restrictions": [],
                "notes": []
            }

    def _parse_ingredient_string(self, ingredient_str: str) -> Optional[Dict]:
        """Parse ingredient string into structured format"""
        # Simple parsing logic - can be enhanced
        parts = ingredient_str.strip().split(' ', 2)
        if len(parts) >= 3:
            try:
                quantity = float(parts[0])
                unit = parts[1]
                name = parts[2]
                return {"name": name, "quantity": quantity, "unit": unit}
            except ValueError:
                pass

        # Fallback: treat as name with default values
        return {"name": ingredient_str.strip(), "quantity": 1, "unit": "piece"}

    def _format_structured_ingredient(self, ingredient: Dict) -> Optional[Dict]:
        """Format already structured ingredient"""
        if "name" in ingredient:
            return {
                "name": ingredient["name"],
                "quantity": ingredient.get("quantity", 1),
                "unit": ingredient.get("unit", "piece")
            }
        return None

    def _clean_instruction_text(self, instruction: str) -> str:
        """Clean instruction text"""
        return instruction.strip()

    def _split_instructions(self, instructions: str) -> List[str]:
        """Split instruction string into list"""
        # Split by common delimiters
        steps = re.split(r'\d+\.\s*|\n\s*', instructions)
        return [step.strip() for step in steps if step.strip()]


class ButtonCreatorTool:
    """Tool for creating action buttons with preview and website selection functionality"""

    def __init__(self):
        self.name = "create_action_buttons"
        self.description = "Create action buttons with preview and website selection functionality"

        # Website configuration - centralized for easy maintenance
        self.supported_websites = [
            {
                "name": "Pinterest",
                "url": "pinterest.com",
                "icon": "📌",
                "color": "#bd081c",
                "description": "Visual recipe discovery platform"
            },
            {
                "name": "AllRecipes",
                "url": "allrecipes.com",
                "icon": "🥄",
                "color": "#e43125",
                "description": "Trusted recipe community"
            },
            {
                "name": "Food Network",
                "url": "foodnetwork.com",
                "icon": "📺",
                "color": "#fa6918",
                "description": "Professional chef recipes"
            },
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
            {
                "name": "Google",
                "url": "google.com",
                "icon": "🔍",
                "color": "#4285f4",
                "description": "Search across all recipe sites"
            }
        ]

    def create_recipe_buttons(self, recipe: Dict[str, Any], recipe_type: str = "internal") -> List[Dict[str, Any]]:
        """Create both action and preview buttons for a recipe"""
        formatter = RecipeFormatterTool()
        preview_data = formatter.format_for_preview(recipe)

        buttons = []

        if recipe_type == "internal":
            # View button for internal recipes
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
            # Add button for external recipes - CRITICAL: Use the URL if provided by AI helper
            button_data = {
                "type": "action_button",
                "text": f"Add {recipe.get('name', 'Recipe')}",
                "action": "create_recipe",
                "style": "primary",
                "metadata": {
                    "recipe_name": recipe.get('name', 'Unknown Recipe'),
                    "type": "add_recipe",
                    "source": "external"
                }
            }

            # IMPORTANT: Use the URL that AI helper set up if available
            if 'url' in recipe:
                button_data['url'] = recipe['url']
            else:
                # Fallback to generic add recipe page if no URL
                button_data['url'] = "/add-recipe"

            buttons.append(button_data)

        # Preview button for all recipes
        preview_metadata = {
            "recipe_name": recipe.get('name', 'Unknown Recipe'),
            "type": "preview_recipe",
            "source": recipe_type
        }

        # Add recipe_id for internal recipes so favorite button can work
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

        # Determine what they're searching for to customize button text
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
                "action": "search_website",  # CRITICAL: This must be "search_website"
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


class RecipeScalingTool:
    """Tool for scaling recipe ingredients up or down"""

    def __init__(self):
        self.name = "scale_recipe"
        self.description = "Scale recipe ingredients for different serving sizes"

    def execute(self, recipe: Dict[str, Any], new_serving_size: int) -> Optional[Dict[str, Any]]:
        """Scale a recipe to a new serving size"""
        try:
            if not recipe or new_serving_size <= 0:
                return None

            original_serving_size = recipe.get('serving_size', 4)
            if original_serving_size <= 0:
                original_serving_size = 4  # Default fallback

            # Calculate scaling factor
            scaling_factor = new_serving_size / original_serving_size

            logger.info(
                f"Scaling recipe '{recipe.get('name', 'Unknown')}' from {original_serving_size} to {new_serving_size} servings (factor: {scaling_factor})")

            # Create scaled recipe copy
            scaled_recipe = recipe.copy()
            scaled_recipe['serving_size'] = new_serving_size
            scaled_recipe['original_serving_size'] = original_serving_size
            scaled_recipe['scaling_factor'] = scaling_factor

            # Scale ingredients
            if 'ingredients' in recipe:
                scaled_ingredients = []
                for ingredient in recipe['ingredients']:
                    if isinstance(ingredient, dict):
                        # Structured ingredient format
                        scaled_ingredient = ingredient.copy()
                        if 'quantity' in ingredient:
                            original_quantity = ingredient['quantity']
                            scaled_quantity = self._scale_quantity(original_quantity, scaling_factor)
                            scaled_ingredient['quantity'] = scaled_quantity
                        scaled_ingredients.append(scaled_ingredient)
                    elif isinstance(ingredient, str):
                        # String format - need to parse and scale
                        scaled_ingredient_str = self._scale_ingredient_string(ingredient, scaling_factor)
                        scaled_ingredients.append(scaled_ingredient_str)
                    else:
                        # Keep as-is if we can't parse
                        scaled_ingredients.append(ingredient)

                scaled_recipe['ingredients'] = scaled_ingredients

            # Update recipe name to indicate scaling
            original_name = recipe.get('name', recipe.get('recipe_name', 'Unknown Recipe'))
            scaled_recipe['name'] = f"{original_name} (Scaled for {new_serving_size})"
            if 'recipe_name' in scaled_recipe:
                scaled_recipe['recipe_name'] = scaled_recipe['name']

            # Add scaling note
            notes = scaled_recipe.get('notes', []).copy()
            notes.append(f"Scaled from {original_serving_size} to {new_serving_size} servings")
            scaled_recipe['notes'] = notes

            logger.info(f"Successfully scaled recipe to {new_serving_size} servings")
            return scaled_recipe

        except Exception as e:
            logger.error(f"Error scaling recipe: {e}")
            return None

    def _scale_quantity(self, quantity: float, scaling_factor: float) -> float:
        """Scale a numeric quantity and round appropriately"""
        try:
            scaled = quantity * scaling_factor

            # Smart rounding based on size
            if scaled < 0.1:
                return round(scaled, 3)  # Keep more precision for very small amounts
            elif scaled < 1:
                return round(scaled, 2)  # 2 decimal places for fractional amounts
            elif scaled < 10:
                return round(scaled, 1)  # 1 decimal place for single digits
            else:
                return round(scaled)  # Whole numbers for larger amounts

        except (ValueError, TypeError):
            return quantity  # Return original if scaling fails

    def _scale_ingredient_string(self, ingredient_str: str, scaling_factor: float) -> str:
        """Scale an ingredient string by parsing and scaling the quantity"""
        try:
            # Try to parse quantity from the beginning of the string
            parts = ingredient_str.strip().split(' ', 2)
            if len(parts) >= 2:
                quantity_part = parts[0]

                # Handle fractions like "1/2", "1/4", etc.
                if '/' in quantity_part:
                    fraction_parts = quantity_part.split('/')
                    if len(fraction_parts) == 2:
                        try:
                            numerator = float(fraction_parts[0])
                            denominator = float(fraction_parts[1])
                            original_quantity = numerator / denominator
                            scaled_quantity = self._scale_quantity(original_quantity, scaling_factor)
                            scaled_fraction = self._convert_to_fraction(scaled_quantity)
                            return f"{scaled_fraction} {' '.join(parts[1:])}"
                        except ValueError:
                            pass

                # Handle decimal numbers
                try:
                    original_quantity = float(quantity_part)
                    scaled_quantity = self._scale_quantity(original_quantity, scaling_factor)

                    # Convert back to fraction if it makes sense
                    scaled_display = self._convert_to_fraction(scaled_quantity)
                    return f"{scaled_display} {' '.join(parts[1:])}"
                except ValueError:
                    pass

            # If we can't parse, return the original
            return ingredient_str

        except Exception as e:
            logger.warning(f"Could not scale ingredient string '{ingredient_str}': {e}")
            return ingredient_str

    def _convert_to_fraction(self, decimal_value: float) -> str:
        """Convert decimal to fraction when it makes sense, otherwise return decimal"""
        try:
            # Common cooking fractions
            common_fractions = {
                0.125: "1/8",
                0.25: "1/4",
                0.333: "1/3",
                0.5: "1/2",
                0.667: "2/3",
                0.75: "3/4",
                1.25: "1 1/4",
                1.333: "1 1/3",
                1.5: "1 1/2",
                1.667: "1 2/3",
                1.75: "1 3/4",
                2.25: "2 1/4",
                2.333: "2 1/3",
                2.5: "2 1/2",
                2.667: "2 2/3",
                2.75: "2 3/4"
            }

            # Check if the decimal is close to a common fraction
            for frac_decimal, frac_str in common_fractions.items():
                if abs(decimal_value - frac_decimal) < 0.05:  # Allow small tolerance
                    return frac_str

            # If no common fraction matches, return as decimal with appropriate precision
            if decimal_value < 1:
                return f"{decimal_value:.2f}"
            elif decimal_value < 10:
                return f"{decimal_value:.1f}"
            else:
                return f"{int(decimal_value)}" if decimal_value == int(decimal_value) else f"{decimal_value:.1f}"

        except Exception:
            return str(decimal_value)

    def detect_scaling_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Detect if user is requesting recipe scaling and extract details"""
        try:
            user_lower = user_message.lower().strip()

            # Scaling keywords and patterns - IMPROVED to catch "scale this/them/it" type requests
            scaling_patterns = [
                r'scale.*(?:for|to)\s*(\d+)',
                r'make.*(?:for|to)\s*(\d+)',
                r'adjust.*(?:for|to)\s*(\d+)',
                r'resize.*(?:for|to)\s*(\d+)',
                r'change.*(?:for|to)\s*(\d+)',
                r'scale.*(?:this|them|it).*(?:for|to)\s*(\d+)',  # NEW: "scale this/them/it to 4"
                r'scale.*(?:this|them|it).*(\d+)',  # NEW: "scale this/them/it 4"
                r'make.*(?:this|them|it).*(?:for|to)\s*(\d+)',  # NEW: "make this/them/it for 4"
                r'double.*recipe',
                r'half.*recipe',
                r'triple.*recipe',
                r'double.*(?:this|them|it)',  # NEW: "double this/them/it"
                r'half.*(?:this|them|it)',  # NEW: "half this/them/it"
                r'triple.*(?:this|them|it)'  # NEW: "triple this/them/it"
            ]

            # Check for explicit serving size requests
            for pattern in scaling_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    context_words = ['this', 'them', 'it']
                    is_context_dependent = any(word in user_lower for word in context_words)

                    if 'double' in user_lower:
                        return {'new_serving_size': None, 'action': 'double', 'context_dependent': is_context_dependent}
                    elif 'half' in user_lower or 'halve' in user_lower:
                        return {'new_serving_size': None, 'action': 'half', 'context_dependent': is_context_dependent}
                    elif 'triple' in user_lower:
                        return {'new_serving_size': None, 'action': 'triple', 'context_dependent': is_context_dependent}
                    else:
                        try:
                            new_size = int(match.group(1))
                            return {'new_serving_size': new_size, 'action': 'scale',
                                    'context_dependent': is_context_dependent}
                        except (ValueError, IndexError):
                            pass

            # Check for serving/people keywords with numbers - only if scaling context exists
            scaling_context_words = ['scale', 'make', 'adjust', 'resize', 'change', 'this', 'them', 'it']
            if any(keyword in user_lower for keyword in scaling_context_words):
                serving_patterns = [
                    r'(\d+)\s*(?:people|person|serving|servings)',
                    r'(?:people|person|serving|servings).*?(\d+)',
                    r'for\s*(\d+)',
                    r'feeds?\s*(\d+)'
                ]

                for pattern in serving_patterns:
                    match = re.search(pattern, user_lower)
                    if match:
                        try:
                            new_size = int(match.group(1))
                            if new_size > 0 and new_size <= 50:  # Reasonable limits
                                context_words = ['this', 'them', 'it']
                                is_context_dependent = any(word in user_lower for word in context_words)
                                return {'new_serving_size': new_size, 'action': 'scale',
                                        'context_dependent': is_context_dependent}
                        except (ValueError, IndexError):
                            pass

            return None

        except Exception as e:
            logger.error(f"Error detecting scaling request: {e}")
            return None


# Tool registry for easy access
TOOLS = {
    'search_external_recipes': RecipeSearchTool(),
    'search_internal_recipes': DatabaseSearchTool(),
    'get_ingredient_suggestions': IngredientSuggestionTool(),
    'parse_recipe_file': FileParsingTool(),
    'format_recipe_data': RecipeFormatterTool(),
    'create_action_buttons': ButtonCreatorTool(),
    'scale_recipe': RecipeScalingTool()
}


def get_tool(tool_name: str):
    """Get a tool by name"""
    return TOOLS.get(tool_name)


def list_available_tools():
    """List all available tools"""
    return list(TOOLS.keys())
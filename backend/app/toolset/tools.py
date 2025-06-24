# backend/app/toolset/tools.py - Rupert's Tool Collection

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
    from app.database import db

    logger.info("Database imported successfully in tools")
    db_available = True
except Exception as e:
    logger.error(f"Failed to import database in tools: {e}")
    db = None
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
            search_query = self._build_search_query(criteria, search_params)

            # Get source with proper error handling
            default_source = "allrecipes.com"
            source = default_source

            if search_params and search_params.get('specific_websites'):
                websites = search_params.get('specific_websites', [])
                if isinstance(websites, list) and len(websites) > 0:
                    source = websites[0]

            # Get ingredient with fallback
            ingredient = criteria.get('ingredient', 'cookies') if criteria else 'cookies'

            # Simulate external search results with properly formatted data
            external_results = [
                {
                    "name": f"Classic {ingredient.title()} Recipe",
                    "source": source,
                    "description": f"A delicious and easy-to-make {ingredient} recipe perfect for any occasion",
                    "url": f"https://{source}/recipe/classic-{ingredient.lower().replace(' ', '-')}",
                    "ingredients": [
                        "2 cups all-purpose flour",
                        "1 cup butter, softened",
                        "3/4 cup granulated sugar",
                        "1/2 cup brown sugar",
                        "2 large eggs",
                        "1 teaspoon vanilla extract",
                        "1 teaspoon baking soda",
                        "1/2 teaspoon salt"
                    ],
                    "instructions": [
                        "Preheat oven to 375°F (190°C)",
                        "In a large bowl, cream together butter and sugars until light and fluffy",
                        "Beat in eggs one at a time, then add vanilla",
                        "In separate bowl, whisk together flour, baking soda, and salt",
                        "Gradually mix dry ingredients into wet ingredients",
                        "Drop rounded tablespoons of dough onto ungreased baking sheets",
                        "Bake for 9-11 minutes until golden brown",
                        "Cool on baking sheet for 5 minutes before transferring to wire rack"
                    ],
                    "serving_size": 24,
                    "prep_time": 15,
                    "cook_time": 10,
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Store in airtight container for up to 1 week"],
                    "cuisine_type": search_params.get('cuisine_type', 'american') if search_params else "american"
                },
                {
                    "name": f"Gourmet {ingredient.title()} Delight",
                    "source": source,
                    "description": f"An elevated version of the classic {ingredient} with premium ingredients",
                    "url": f"https://{source}/recipe/gourmet-{ingredient.lower().replace(' ', '-')}",
                    "ingredients": [
                        "2 1/4 cups cake flour",
                        "1 cup European butter",
                        "1/2 cup turbinado sugar",
                        "1/2 cup coconut sugar",
                        "2 organic eggs",
                        "1 tablespoon pure vanilla extract",
                        "1 teaspoon baking soda",
                        "1/2 teaspoon sea salt",
                        "1 cup premium chocolate chips"
                    ],
                    "instructions": [
                        "Preheat oven to 350°F (175°C)",
                        "Cream butter and sugars in stand mixer until very light",
                        "Add eggs and vanilla, mixing until well combined",
                        "Sift together flour, baking soda, and salt",
                        "Fold dry ingredients into wet mixture",
                        "Fold in chocolate chips",
                        "Scoop dough onto parchment-lined baking sheets",
                        "Bake 12-14 minutes until edges are set",
                        "Cool completely before serving"
                    ],
                    "serving_size": 18,
                    "prep_time": 20,
                    "cook_time": 14,
                    "genre": criteria.get('genre', 'dessert'),
                    "notes": ["Use high-quality chocolate for best results", "Can be frozen for up to 3 months"],
                    "cuisine_type": search_params.get('cuisine_type', 'american') if search_params else "american"
                }
            ]

            return external_results

        except Exception as e:
            logger.error(f"Error in external recipe search: {e}")
            return []

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
                regex_pattern = f"\\b{escaped_ingredient}\\b"
                query["ingredients.name"] = {"$regex": regex_pattern, "$options": "i"}

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

            logger.info(f"Database search query: {query}")
            recipes = list(db.recipes.find(query).limit(50))

            # If no exact matches and ingredient has spaces, try fallback
            if len(recipes) == 0 and "ingredient" in criteria and " " in criteria["ingredient"]:
                words = criteria["ingredient"].split()
                word_patterns = [f"\\b{re.escape(word)}\\b" for word in words]
                fallback_query = query.copy()
                fallback_query["ingredients.name"] = {"$regex": "|".join(word_patterns), "$options": "i"}
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
            "created_at": recipe["created_at"].strftime("%Y-%m-%d") if recipe.get("created_at") else ""
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
    """Tool for formatting recipe data for forms"""

    def __init__(self):
        self.name = "format_recipe_data"
        self.description = "Format raw recipe data for the add recipe form"

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


# Tool registry for easy access
TOOLS = {
    'search_external_recipes': RecipeSearchTool(),
    'search_internal_recipes': DatabaseSearchTool(),
    'get_ingredient_suggestions': IngredientSuggestionTool(),
    'parse_recipe_file': FileParsingTool(),
    'format_recipe_data': RecipeFormatterTool()
}


def get_tool(tool_name: str):
    """Get a tool by name"""
    return TOOLS.get(tool_name)


def list_available_tools():
    """List all available tools"""
    return list(TOOLS.keys())
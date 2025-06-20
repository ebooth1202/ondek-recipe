# backend/app/utils/ai_helper.py - Complete version with file parsing capabilities

import os
from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import re
from datetime import datetime, timedelta
from ..database import db
from bson import ObjectId
import logging
import requests
from urllib.parse import quote_plus
import uuid
import asyncio
from fractions import Fraction
import PyPDF2
import pytesseract
from PIL import Image
import csv
import io
import magic
import tempfile

logger = logging.getLogger(__name__)

# Temporary storage for recipe data (in production, consider using Redis)
temp_recipe_storage = {}


class FileParsingResult:
    def __init__(self, file_name: str, file_type: str, parsed_text: str, recipe_data=None, confidence: float = 0.0):
        self.file_name = file_name
        self.file_type = file_type
        self.parsed_text = parsed_text
        self.recipe_data = recipe_data
        self.confidence = confidence


class AIHelper:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"

        # External search configuration
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.allowed_external_search = False

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key and self.client)

    def store_temp_recipe(self, recipe_data: Dict[str, Any]) -> str:
        """Store temporary recipe data and return a unique ID"""
        temp_id = str(uuid.uuid4())
        temp_recipe_storage[temp_id] = {
            "data": recipe_data,
            "timestamp": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=2)  # Expires in 2 hours
        }

        # Clean up expired entries
        self._cleanup_expired_temp_recipes()

        return temp_id

    def get_temp_recipe(self, temp_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve temporary recipe data by ID"""
        if temp_id in temp_recipe_storage:
            stored = temp_recipe_storage[temp_id]
            if datetime.now() < stored["expires_at"]:
                return stored["data"]
            else:
                # Remove expired entry
                del temp_recipe_storage[temp_id]
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

    # NEW FILE PARSING METHODS
    async def parse_recipe_file(self, file_content: bytes, filename: str, file_type: str, file_extension: str) -> \
    Optional[FileParsingResult]:
        """
        Parse recipe information from various file types
        """
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
                # Try to decode as text anyway
                try:
                    extracted_text = file_content.decode('utf-8', errors='ignore')
                except:
                    raise ValueError(f"Unsupported file type: {file_type}")

            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from {filename}")
                return None

            logger.info(f"Extracted {len(extracted_text)} characters from {filename}")

            # Use AI to parse the extracted text into recipe data
            recipe_data = await self.parse_recipe_from_text_advanced(
                extracted_text,
                source_info=f"Uploaded file: {filename}"
            )

            return FileParsingResult(
                file_name=filename,
                file_type=file_type,
                parsed_text=extracted_text,
                recipe_data=recipe_data,
                confidence=0.8 if recipe_data else 0.3
            )

        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
            return None

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(file_content))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def _extract_text_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file"""
        try:
            csv_text = file_content.decode('utf-8', errors='ignore')
            csv_file = io.StringIO(csv_text)

            # Try to detect if this is a recipe CSV
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
                # Format as structured text
                formatted_text = "Recipe Data from CSV:\n\n"
                for i, row in enumerate(rows, 1):
                    formatted_text += f"Recipe {i}:\n"
                    for key, value in row.items():
                        if value and value.strip():
                            formatted_text += f"{key}: {value}\n"
                    formatted_text += "\n"
                return formatted_text
            else:
                # Return raw CSV text
                return csv_text

        except Exception as e:
            logger.error(f"Error extracting text from CSV: {e}")
            return file_content.decode('utf-8', errors='ignore')

    async def parse_recipe_from_text_advanced(self, text_content: str, source_info: Optional[str] = None) -> Optional[
        Dict[str, Any]]:
        """
        Advanced recipe parsing from text using AI
        """
        try:
            if not self.is_configured():
                return None

            # Clean and prepare the text
            cleaned_text = self._clean_text_for_parsing(text_content)

            if len(cleaned_text) < 50:  # Too short to be a recipe
                logger.warning("Text too short to contain recipe information")
                return None

            # Create a comprehensive prompt for recipe extraction
            system_prompt = """You are a recipe extraction specialist. Your job is to analyze text and extract complete recipe information in a specific JSON format.

IMPORTANT: You must return ONLY valid JSON with no additional text or markdown formatting.

Extract the following information and return as JSON:
{
  "recipe_name": "string (required)",
  "description": "string (optional, brief description)",
  "ingredients": [
    {
      "name": "ingredient name",
      "quantity": number,
      "unit": "cup|cups|tablespoon|tablespoons|teaspoon|teaspoons|ounce|ounces|pound|pounds|gram|grams|kilogram|kilograms|liter|liters|milliliter|milliliters|piece|pieces|whole|stick|sticks|pinch|dash"
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

Rules:
1. Extract ALL ingredients with proper quantities and units
2. Break down instructions into clear, numbered steps
3. Infer reasonable serving size if not specified
4. Classify genre based on content
5. Extract timing information if available
6. Include any tips, notes, or variations
7. Identify dietary restrictions mentioned
8. If multiple recipes exist, extract the first/main one
9. Return ONLY the JSON object, no other text"""

            user_prompt = f"""Extract recipe information from this text:

Source: {source_info or 'User provided text'}

Text content:
{cleaned_text}

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

            # Clean up the response - remove any markdown formatting
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            try:
                recipe_data = json.loads(result_text)

                # Validate and format the extracted data
                formatted_recipe = self._validate_and_format_extracted_recipe(recipe_data)

                if formatted_recipe:
                    logger.info(f"Successfully extracted recipe: {formatted_recipe.get('recipe_name', 'Unknown')}")
                    return formatted_recipe
                else:
                    logger.warning("Recipe data validation failed")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"AI response was: {result_text}")
                return None

        except Exception as e:
            logger.error(f"Error in advanced recipe parsing: {e}")
            return None

    def _clean_text_for_parsing(self, text: str) -> str:
        """Clean and prepare text for recipe parsing"""
        try:
            # Remove excessive whitespace
            text = ' '.join(text.split())

            # Remove common OCR artifacts
            text = text.replace('|', 'I')  # Common OCR error
            text = text.replace('°', ' degrees ')

            # Normalize fractions
            text = text.replace('½', '1/2')
            text = text.replace('¼', '1/4')
            text = text.replace('¾', '3/4')
            text = text.replace('⅓', '1/3')
            text = text.replace('⅔', '2/3')

            # Remove excessive newlines but preserve structure
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

            return text
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text

    def _validate_and_format_extracted_recipe(self, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and format extracted recipe data"""
        try:
            # Check required fields
            if not recipe_data.get('recipe_name'):
                logger.warning("No recipe name found in extracted data")
                return None

            if not recipe_data.get('ingredients') or not recipe_data.get('instructions'):
                logger.warning("Missing ingredients or instructions in extracted data")
                return None

            # Format the recipe using existing format_recipe_for_form method
            formatted = self.format_recipe_for_form(recipe_data)

            if formatted:
                # Additional validation
                if len(formatted['ingredients']) == 0:
                    logger.warning("No valid ingredients found after formatting")
                    return None

                if len(formatted['instructions']) == 0:
                    logger.warning("No valid instructions found after formatting")
                    return None

            return formatted

        except Exception as e:
            logger.error(f"Error validating extracted recipe: {e}")
            return None

    def create_file_parsing_action_button(self, temp_id: str, filename: str) -> Dict[str, Any]:
        """Create action button for parsed file recipe"""
        return {
            "type": "action_button",
            "text": f"Add Recipe from {filename}",
            "action": "create_recipe_from_file",
            "url": f"/add-recipe?temp_id={temp_id}",
            "metadata": {
                "temp_id": temp_id,
                "source": filename,
                "type": "file_upload"
            }
        }

    async def generate_file_parsing_response(self, parsing_result: FileParsingResult,
                                             temp_id: Optional[str] = None) -> str:
        """Generate a user-friendly response for file parsing results"""
        try:
            if not parsing_result.recipe_data:
                return f"""I processed your file "{parsing_result.file_name}" but couldn't extract a complete recipe from it. 

Here's what I found:
{parsing_result.parsed_text[:300]}{'...' if len(parsing_result.parsed_text) > 300 else ''}

You can try:
- Uploading a clearer image if it was a photo
- Providing a file with more structured recipe information
- Manually entering the recipe information"""

            recipe_name = parsing_result.recipe_data.get('recipe_name', 'Unknown Recipe')
            ingredient_count = len(parsing_result.recipe_data.get('ingredients', []))
            instruction_count = len(parsing_result.recipe_data.get('instructions', []))

            response = f"""🎉 Great! I successfully extracted a recipe from your file "{parsing_result.file_name}"!

**Recipe Found:** {recipe_name}
- **Ingredients:** {ingredient_count} items
- **Instructions:** {instruction_count} steps
- **Serves:** {parsing_result.recipe_data.get('serving_size', 'Not specified')}
- **Category:** {parsing_result.recipe_data.get('genre', 'Not specified').title()}

The recipe data has been prepared and is ready to be added to your collection! Click the button below to review and save it to your recipe database."""

            if temp_id:
                button = self.create_file_parsing_action_button(temp_id, parsing_result.file_name)
                response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error generating file parsing response: {e}")
            return f"I processed your file but encountered an error generating the response. The recipe data may still be available."

    # EXISTING METHODS (updated and enhanced)
    def format_recipe_for_form(self, raw_recipe_data: Dict[str, Any]) -> Dict[str, Any]:
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
                if len(description) <= 500:  # Respect the field limit
                    formatted_recipe["description"] = description
                else:
                    formatted_recipe["description"] = description[:497] + "..."

            # Extract and format ingredients
            if "ingredients" in raw_recipe_data:
                for ingredient in raw_recipe_data["ingredients"]:
                    if isinstance(ingredient, str):
                        # Parse string ingredient
                        parsed = self._parse_ingredient_string(ingredient)
                        if parsed:
                            formatted_recipe["ingredients"].append(parsed)
                    elif isinstance(ingredient, dict):
                        # Already structured ingredient
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
                        elif isinstance(instruction, dict) and "text" in instruction:
                            cleaned = self._clean_instruction_text(instruction["text"])
                            if cleaned:
                                formatted_recipe["instructions"].append(cleaned)
                elif isinstance(instructions, str):
                    # Split by common delimiters
                    instruction_list = self._split_instructions(instructions)
                    formatted_recipe["instructions"].extend(instruction_list)

            # Extract serving size
            if "serving_size" in raw_recipe_data:
                try:
                    serving_size = int(raw_recipe_data["serving_size"])
                    if 1 <= serving_size <= 100:
                        formatted_recipe["serving_size"] = serving_size
                except (ValueError, TypeError):
                    pass
            elif "servings" in raw_recipe_data:
                try:
                    serving_size = int(raw_recipe_data["servings"])
                    if 1 <= serving_size <= 100:
                        formatted_recipe["serving_size"] = serving_size
                except (ValueError, TypeError):
                    pass

            # Extract genre/category
            if "genre" in raw_recipe_data:
                genre = self._map_genre(raw_recipe_data["genre"])
                if genre:
                    formatted_recipe["genre"] = genre
            elif "category" in raw_recipe_data:
                genre = self._map_genre(raw_recipe_data["category"])
                if genre:
                    formatted_recipe["genre"] = genre

            # Extract timing
            if "prep_time" in raw_recipe_data:
                prep_time = self._parse_time(raw_recipe_data["prep_time"])
                if prep_time is not None:
                    formatted_recipe["prep_time"] = prep_time

            if "cook_time" in raw_recipe_data:
                cook_time = self._parse_time(raw_recipe_data["cook_time"])
                if cook_time is not None:
                    formatted_recipe["cook_time"] = cook_time

            # Extract notes (exclude nutrition info)
            notes = []

            # Add any additional notes or tips
            if "notes" in raw_recipe_data:
                if isinstance(raw_recipe_data["notes"], list):
                    notes.extend(raw_recipe_data["notes"])
                elif isinstance(raw_recipe_data["notes"], str):
                    notes.append(raw_recipe_data["notes"])

            if "tips" in raw_recipe_data:
                if isinstance(raw_recipe_data["tips"], list):
                    notes.extend(raw_recipe_data["tips"])
                elif isinstance(raw_recipe_data["tips"], str):
                    notes.append(raw_recipe_data["tips"])

            if "additional_info" in raw_recipe_data:
                notes.append(raw_recipe_data["additional_info"])

            formatted_recipe["notes"] = notes

            # Extract dietary restrictions
            dietary_restrictions = []
            if "dietary_restrictions" in raw_recipe_data:
                dietary_restrictions = raw_recipe_data["dietary_restrictions"]
            elif "dietary_info" in raw_recipe_data:
                dietary_restrictions = raw_recipe_data["dietary_info"]
            elif "diet_tags" in raw_recipe_data:
                dietary_restrictions = raw_recipe_data["diet_tags"]

            # Filter and validate dietary restrictions
            valid_restrictions = ["gluten_free", "dairy_free", "egg_free", "vegetarian", "vegan", "keto", "paleo"]
            filtered_restrictions = []
            for restriction in dietary_restrictions:
                if isinstance(restriction, str):
                    normalized = restriction.lower().replace(" ", "_").replace("-", "_")
                    if normalized in valid_restrictions:
                        filtered_restrictions.append(normalized)

            formatted_recipe["dietary_restrictions"] = filtered_restrictions

            return formatted_recipe

        except Exception as e:
            logger.error(f"Error formatting recipe for form: {e}")
            return None

    def _parse_ingredient_string(self, ingredient_str: str) -> Optional[Dict[str, Any]]:
        """Parse a string ingredient into structured format"""
        try:
            # Clean the string
            ingredient_str = ingredient_str.strip().lstrip("-*•").strip()

            # Common patterns for ingredients
            patterns = [
                r"(\d+(?:\.\d+)?)\s*(\w+)\s+(.+)",  # "2 cups flour"
                r"(\d+(?:\.\d+)?)\s+(.+)",  # "2 eggs"
                r"(\d+)\s*/\s*(\d+)\s*(\w+)\s+(.+)",  # "1/2 cup milk"
            ]

            for pattern in patterns:
                match = re.match(pattern, ingredient_str)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:  # quantity, unit, name
                        quantity, unit, name = groups
                        return {
                            "name": name.strip(),
                            "quantity": float(quantity),
                            "unit": self._normalize_unit(unit)
                        }
                    elif len(groups) == 2:  # quantity, name (no unit)
                        quantity, name = groups
                        return {
                            "name": name.strip(),
                            "quantity": float(quantity),
                            "unit": "piece"
                        }
                    elif len(groups) == 4:  # fraction
                        num, denom, unit, name = groups
                        quantity = float(num) / float(denom)
                        return {
                            "name": name.strip(),
                            "quantity": quantity,
                            "unit": self._normalize_unit(unit)
                        }

            # If no pattern matches, assume it's just a name with quantity 1
            return {
                "name": ingredient_str,
                "quantity": 1.0,
                "unit": "piece"
            }

        except Exception as e:
            logger.warning(f"Could not parse ingredient: {ingredient_str}, error: {e}")
            return None

    def _format_structured_ingredient(self, ingredient_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format a structured ingredient dictionary"""
        try:
            formatted = {
                "name": "",
                "quantity": 1.0,
                "unit": "piece"
            }

            # Extract name
            if "name" in ingredient_dict:
                formatted["name"] = ingredient_dict["name"]
            elif "ingredient" in ingredient_dict:
                formatted["name"] = ingredient_dict["ingredient"]
            else:
                return None

            # Extract quantity
            if "quantity" in ingredient_dict:
                try:
                    formatted["quantity"] = float(ingredient_dict["quantity"])
                except (ValueError, TypeError):
                    formatted["quantity"] = 1.0
            elif "amount" in ingredient_dict:
                try:
                    formatted["quantity"] = float(ingredient_dict["amount"])
                except (ValueError, TypeError):
                    formatted["quantity"] = 1.0

            # Extract unit
            if "unit" in ingredient_dict:
                formatted["unit"] = self._normalize_unit(ingredient_dict["unit"])
            elif "measurement" in ingredient_dict:
                formatted["unit"] = self._normalize_unit(ingredient_dict["measurement"])

            return formatted

        except Exception as e:
            logger.warning(f"Could not format structured ingredient: {ingredient_dict}, error: {e}")
            return None

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit names to match the MeasuringUnit enum"""
        unit = unit.lower().strip()

        unit_mapping = {
            "c": "cup", "cup": "cup", "cups": "cups",
            "tbsp": "tablespoon", "tablespoon": "tablespoon", "tablespoons": "tablespoons",
            "tsp": "teaspoon", "teaspoon": "teaspoon", "teaspoons": "teaspoons",
            "oz": "ounce", "ounce": "ounce", "ounces": "ounces",
            "lb": "pound", "pound": "pound", "pounds": "pounds",
            "g": "gram", "gram": "gram", "grams": "grams",
            "kg": "kilogram", "kilogram": "kilogram", "kilograms": "kilograms",
            "l": "liter", "liter": "liter", "liters": "liters",
            "ml": "milliliter", "milliliter": "milliliter", "milliliters": "milliliters",
            "piece": "piece", "pieces": "pieces",
            "whole": "whole", "stick": "stick", "sticks": "sticks",
            "pinch": "pinch", "dash": "dash"
        }

        return unit_mapping.get(unit, "piece")

    def _clean_instruction_text(self, instruction: str) -> str:
        """Clean instruction text"""
        # Remove step numbers and bullets
        instruction = re.sub(r"^\d+\.\s*", "", instruction)
        instruction = re.sub(r"^[-*•]\s*", "", instruction)
        instruction = instruction.strip()

        # Remove nutrition information
        nutrition_keywords = ["calories", "protein", "carbs", "fat", "sodium", "sugar", "fiber"]
        if any(keyword in instruction.lower() for keyword in nutrition_keywords):
            return ""

        return instruction

    def _split_instructions(self, instructions_text: str) -> List[str]:
        """Split instruction text into individual steps"""
        # Split by common delimiters
        steps = re.split(r"\d+\.|(?:\n|^)[-*•]|\n\n", instructions_text)

        cleaned_steps = []
        for step in steps:
            cleaned = self._clean_instruction_text(step)
            if cleaned and len(cleaned) > 10:  # Ignore very short steps
                cleaned_steps.append(cleaned)

        return cleaned_steps

    def _map_genre(self, category: str) -> Optional[str]:
        """Map category to valid genre"""
        category = category.lower()

        genre_mapping = {
            "breakfast": "breakfast",
            "lunch": "lunch",
            "dinner": "dinner",
            "snack": "snack", "snacks": "snack",
            "dessert": "dessert", "desserts": "dessert",
            "appetizer": "appetizer", "appetizers": "appetizer", "starter": "appetizer",
            "main": "dinner", "main course": "dinner", "entree": "dinner",
            "side": "snack", "side dish": "snack"
        }

        return genre_mapping.get(category)

    def _parse_time(self, time_str: str) -> Optional[int]:
        """Parse time string to minutes"""
        if isinstance(time_str, int):
            return time_str

        if isinstance(time_str, str):
            time_str = time_str.lower()

            # Extract numbers
            minutes = 0

            # Look for hours
            hour_match = re.search(r"(\d+)\s*(?:hour|hr|h)", time_str)
            if hour_match:
                minutes += int(hour_match.group(1)) * 60

            # Look for minutes
            min_match = re.search(r"(\d+)\s*(?:minute|min|m)", time_str)
            if min_match:
                minutes += int(min_match.group(1))

            # If no specific unit, assume it's minutes
            if minutes == 0:
                number_match = re.search(r"(\d+)", time_str)
                if number_match:
                    minutes = int(number_match.group(1))

            return minutes if 0 <= minutes <= 1440 else None

        return None

    def should_show_add_recipe_button(self, user_message: str, ai_response: str) -> bool:
        """Determine if we should show an 'Add Recipe' button"""
        add_recipe_keywords = [
            "add recipe", "create recipe", "new recipe", "save recipe",
            "how to add", "help me create", "want to add", "need to create"
        ]

        recipe_content_indicators = [
            "recipe", "ingredients", "instructions", "cooking", "baking"
        ]

        user_lower = user_message.lower()
        response_lower = ai_response.lower()

        # Direct request to add/create recipe
        if any(keyword in user_lower for keyword in add_recipe_keywords):
            return True

        # AI provided recipe content
        if any(indicator in response_lower for indicator in recipe_content_indicators):
            if "ingredients:" in response_lower or "instructions:" in response_lower:
                return True

        return False

    def create_recipe_action_button(self, recipe_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create action button data for recipe creation"""
        button_data = {
            "type": "action_button",
            "text": "Add Recipe",
            "action": "create_recipe"
        }

        if recipe_data:
            # Store the recipe data temporarily
            temp_id = self.store_temp_recipe(recipe_data)
            button_data["url"] = f"/add-recipe?temp_id={temp_id}"
            button_data["text"] = "Add This Recipe"
        else:
            button_data["url"] = "/add-recipe"

        return button_data

    async def chat_about_recipes(self, user_message: str,
                                 conversation_history: Optional[List[Dict]] = None) -> str:
        """Enhanced main chat function with recipe creation support"""
        if not self.is_configured():
            return "AI features are currently unavailable. Please contact the administrator to configure the OpenAI API key."

        try:
            # Step 1: Check for recipe creation intent
            creation_intent = self._detect_recipe_creation_intent(user_message)

            # Step 2: Always check internal database first
            search_criteria = self.extract_search_intent(user_message)

            # Search internal database
            internal_recipes = []
            recipe_count = 0

            if search_criteria:
                internal_recipes = self.search_recipes_by_criteria(search_criteria)
                recipe_count = self.count_recipes_by_criteria(search_criteria)
            else:
                # For general queries, get a sample
                internal_recipes = self.get_recipes_data(limit=10)
                recipe_count = len(internal_recipes)

            # Step 3: Handle different scenarios
            if creation_intent == "help_create":
                # User wants help creating a recipe
                return await self._generate_creation_help_response(user_message, conversation_history)

            elif internal_recipes and recipe_count > 0:
                # We found recipes in the database
                response = await self._generate_internal_response(user_message, internal_recipes,
                                                                  conversation_history, search_criteria)

                # Check if we should add an "Add Recipe" button
                if self.should_show_add_recipe_button(user_message, response):
                    button = self.create_recipe_action_button()
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

                return response

            elif self.detect_external_search_request(user_message):
                # User has given permission for external search
                search_params = self.extract_search_parameters(user_message)
                external_recipes = await self.search_external_recipes(search_criteria, search_params)

                return await self._generate_external_response(user_message, external_recipes,
                                                              search_criteria, search_params,
                                                              conversation_history)

            else:
                # Step 4: Ask for permission to search externally
                response = self._generate_permission_request(search_criteria, user_message)

                # Add "Add Recipe" button for creation help
                if creation_intent or self.should_show_add_recipe_button(user_message, response):
                    button = self.create_recipe_action_button()
                    response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

                return response

        except Exception as e:
            logger.error(f"Error in chat_about_recipes: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."

    def _detect_recipe_creation_intent(self, user_message: str) -> Optional[str]:
        """Detect if user wants help creating a recipe"""
        creation_keywords = [
            "help me create", "help me add", "how to create", "how to add",
            "want to create", "want to add", "need to create", "need to add",
            "help creating", "help adding", "create a recipe", "add a recipe"
        ]

        user_lower = user_message.lower()
        if any(keyword in user_lower for keyword in creation_keywords):
            return "help_create"

        return None

    async def _generate_creation_help_response(self, user_message: str,
                                               conversation_history: Optional[List[Dict]]) -> str:
        """Generate response for recipe creation help"""
        try:
            system_message = """You are Ralph, a helpful cooking assistant for the Ondek Recipe app. The user is asking for help creating or adding a new recipe. 

Provide helpful guidance about recipe creation, including:
- Tips for organizing ingredients and measurements
- Advice on writing clear instructions
- Suggestions for categorizing recipes
- General cooking tips for recipe development

Be encouraging and offer to help them get started with the recipe creation process."""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-4:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=600,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Add action button
            button = self.create_recipe_action_button()
            ai_response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return ai_response

        except Exception as e:
            logger.error(f"Error generating creation help response: {e}")
            button = self.create_recipe_action_button()
            return f"I'd be happy to help you create a new recipe! Click the button below to get started with the recipe creation form.\n\n[ACTION_BUTTON:{json.dumps(button)}]"

    async def _generate_external_response(self, user_message: str, external_recipes: List[Dict],
                                          search_criteria: Dict[str, Any], search_params: Dict[str, Any],
                                          conversation_history: Optional[List[Dict]]) -> str:
        """Enhanced external response with recipe action buttons"""
        try:
            if not external_recipes:
                response = "I searched the internet as requested, but couldn't find recipes matching your criteria. Would you like to try different search terms or check different websites?"
                button = self.create_recipe_action_button()
                response += f"\n\nOr you can create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            # Build context for external results
            external_context = f"\n\nI searched the internet and found these recipes:\n"
            for i, recipe in enumerate(external_recipes[:5], 1):
                external_context += f"\n{i}. **{recipe['name']}** (from {recipe['source']})\n"
                external_context += f"   - {recipe['description']}\n"
                if recipe.get('url'):
                    external_context += f"   - URL: {recipe['url']}\n"

            search_info = ""
            if search_params:
                if search_params.get('specific_websites'):
                    search_info += f"Searched on: {', '.join(search_params['specific_websites'])}\n"
                if search_params.get('cuisine_type'):
                    search_info += f"Cuisine focus: {search_params['cuisine_type']}\n"

            system_message = f"""You are Ralph, a helpful cooking assistant. The user asked you to search the internet for recipes since nothing was found in their personal database.

External search results: Found {len(external_recipes)} recipes from the internet.
{search_info}

{external_context}

Guidelines:
- Present the external recipes you found
- Mention that these are from the internet, not their personal database
- Ask if they'd like full details for any recipe
- Offer to help them save promising recipes to their database
- Be helpful in explaining the differences between their saved recipes and internet finds"""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-4:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Add action buttons for external recipes
            if external_recipes:
                # Create buttons for top recipes
                for i, recipe in enumerate(external_recipes[:2]):  # Limit to top 2 recipes
                    formatted_recipe = self.format_recipe_for_form(recipe)
                    if formatted_recipe:
                        button = self.create_recipe_action_button(formatted_recipe)
                        ai_response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return ai_response

        except Exception as e:
            logger.error(f"Error generating external response: {e}")
            return "I found some recipes online, but encountered an error presenting them. Please try again."

    # Keep all existing methods...
    # (Previous methods remain unchanged)

    def get_recipes_data(self, limit: int = 50) -> List[Dict]:
        """Retrieve recipes from database for AI context"""
        try:
            recipes = list(db.recipes.find().limit(limit))
            processed_recipes = []

            for recipe in recipes:
                processed_recipe = {
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
                processed_recipes.append(processed_recipe)

            return processed_recipes
        except Exception as e:
            logger.error(f"Error retrieving recipes: {e}")
            return []

    def search_recipes_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Search recipes based on specific criteria"""
        try:
            query = {}

            # Handle different search criteria
            if "genre" in criteria:
                query["genre"] = {"$regex": criteria["genre"], "$options": "i"}

            if "ingredient" in criteria:
                query["ingredients.name"] = {"$regex": criteria["ingredient"], "$options": "i"}

            if "name" in criteria:
                query["recipe_name"] = {"$regex": criteria["name"], "$options": "i"}

            if "max_time" in criteria:
                # Search by total time
                query["$expr"] = {
                    "$lte": [
                        {"$add": [{"$ifNull": ["$prep_time", 0]}, {"$ifNull": ["$cook_time", 0]}]},
                        criteria["max_time"]
                    ]
                }

            if "dietary_restrictions" in criteria:
                query["dietary_restrictions"] = {"$in": criteria["dietary_restrictions"]}

            recipes = list(db.recipes.find(query).limit(20))
            return [self._format_recipe_for_ai(recipe) for recipe in recipes]

        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []

    def count_recipes_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """Count recipes matching criteria without retrieving them"""
        try:
            query = {}

            if "genre" in criteria:
                query["genre"] = {"$regex": criteria["genre"], "$options": "i"}
            if "ingredient" in criteria:
                query["ingredients.name"] = {"$regex": criteria["ingredient"], "$options": "i"}
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

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict]:
        """Get specific recipe by ID"""
        try:
            if not ObjectId.is_valid(recipe_id):
                return None

            recipe = db.recipes.find_one({"_id": ObjectId(recipe_id)})
            if recipe:
                return self._format_recipe_for_ai(recipe)
            return None
        except Exception as e:
            logger.error(f"Error getting recipe by ID: {e}")
            return None

    def _format_recipe_for_ai(self, recipe: Dict) -> Dict:
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

    def extract_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Extract search criteria from user message using AI"""
        if not self.is_configured():
            return {}

        try:
            prompt = f"""
            Analyze this user message about recipes and extract search criteria as JSON:
            User message: "{user_message}"

            Extract any of these criteria if mentioned:
            - genre: breakfast, lunch, dinner, snack, dessert, appetizer
            - ingredient: any ingredient name mentioned
            - name: recipe name if specifically mentioned
            - max_time: maximum cooking time in minutes if mentioned
            - dietary_restrictions: gluten_free, dairy_free, egg_free

            Return only valid JSON like:
            {{"genre": "dinner", "ingredient": "chicken", "max_time": 30}}

            If no criteria found, return: {{}}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI search criteria: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return {}

    def detect_external_search_request(self, user_message: str) -> bool:
        """Detect if user is requesting external search or giving permission"""
        external_keywords = [
            "search the internet", "look online", "find on web", "search web",
            "yes, search", "go ahead", "please search", "look it up",
            "from the internet", "online recipes", "web search"
        ]

        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in external_keywords)

    def extract_search_parameters(self, user_message: str) -> Dict[str, Any]:
        """Extract specific search parameters from user message"""
        if not self.is_configured():
            return {}

        try:
            prompt = f"""
            Extract search parameters from this user message:
            "{user_message}"

            Look for:
            - specific_websites: any websites mentioned (e.g., "allrecipes.com", "food.com")
            - cuisine_type: specific cuisine mentioned (e.g., "italian", "asian", "mexican")
            - difficulty_level: cooking skill level (e.g., "easy", "beginner", "advanced")
            - meal_type: specific meal types (e.g., "quick meals", "one-pot", "healthy")
            - additional_constraints: any other specific requirements

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
                logger.warning(f"Could not parse search parameters: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error extracting search parameters: {e}")
            return {}

    async def search_external_recipes(self, criteria: Dict[str, Any],
                                      search_params: Dict[str, Any] = None) -> List[Dict]:
        """Search for recipes from external sources with better error handling"""
        try:
            # This is a placeholder for external recipe search
            # You would implement actual API calls to recipe websites here

            search_query = self._build_external_search_query(criteria, search_params)

            # Get source with proper error handling
            default_source = "allrecipes.com"
            source = default_source

            if search_params and search_params.get('specific_websites'):
                websites = search_params.get('specific_websites', [])
                if isinstance(websites, list) and len(websites) > 0:
                    source = websites[0]
                else:
                    source = default_source

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

    def _build_external_search_query(self, criteria: Dict[str, Any],
                                     search_params: Dict[str, Any] = None) -> str:
        """Build search query for external APIs"""
        query_parts = []

        if criteria and criteria.get('ingredient'):
            query_parts.append(f"recipe {criteria['ingredient']}")
        elif criteria and criteria.get('genre'):
            query_parts.append(f"{criteria['genre']} recipe")
        elif criteria and criteria.get('name'):
            query_parts.append(criteria['name'])
        else:
            query_parts.append("cookie recipe")  # Default fallback

        if search_params:
            if search_params.get('cuisine_type'):
                query_parts.append(search_params['cuisine_type'])
            if search_params.get('difficulty_level'):
                query_parts.append(search_params['difficulty_level'])

        return " ".join(query_parts) if query_parts else "cookie recipe"

    async def _generate_internal_response(self, user_message: str, recipes: List[Dict],
                                          conversation_history: Optional[List[Dict]],
                                          search_criteria: Dict[str, Any]) -> str:
        """Generate response based on internal database recipes"""
        try:
            # Build context for AI
            recipe_context = f"\n\nI found {len(recipes)} recipe(s) in your database:\n"
            for i, recipe in enumerate(recipes[:10], 1):
                recipe_context += f"\n{i}. **{recipe['name']}** ({recipe['genre']})\n"
                recipe_context += f"   - Serves: {recipe['serving_size']}\n"
                recipe_context += f"   - Total time: {recipe['total_time']} minutes\n"
                recipe_context += f"   - Key ingredients: {', '.join(recipe['ingredients'][:3])}...\n"
                if recipe['dietary_restrictions']:
                    recipe_context += f"   - Dietary: {', '.join(recipe['dietary_restrictions'])}\n"
                recipe_context += f"   - Created by: {recipe['created_by']}\n"

            system_message = f"""You are Ralph, a helpful cooking assistant for the Ondek Recipe app. You have access to the user's personal recipe database and should provide helpful information based on what's available.

IMPORTANT: You are currently working with recipes from the user's personal database only. These are recipes they have saved or created.

Current results: Found {len(recipes)} recipes matching their request.

{recipe_context}

Guidelines:
- Be friendly and enthusiastic about the recipes found in their database
- Provide specific recommendations from their collection
- Include practical cooking tips
- If they want more options, offer to search the internet for additional recipes
- Always prioritize their saved recipes first"""

            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-6:])

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating internal response: {e}")
            return "I found recipes in your database, but encountered an error formatting the response."

    def _generate_permission_request(self, search_criteria: Dict[str, Any], user_message: str) -> str:
        """Generate a request for permission to search externally"""
        criteria_text = ""
        if search_criteria:
            criteria_parts = []
            if search_criteria.get('ingredient'):
                criteria_parts.append(f"ingredient '{search_criteria['ingredient']}'")
            if search_criteria.get('genre'):
                criteria_parts.append(f"genre '{search_criteria['genre']}'")
            if search_criteria.get('name'):
                criteria_parts.append(f"recipe name '{search_criteria['name']}'")
            if search_criteria.get('max_time'):
                criteria_parts.append(f"cooking time under {search_criteria['max_time']} minutes")
            if search_criteria.get('dietary_restrictions'):
                criteria_parts.append(f"dietary restrictions: {', '.join(search_criteria['dietary_restrictions'])}")

            if criteria_parts:
                criteria_text = f" matching {' and '.join(criteria_parts)}"

        return f"""I've searched your personal recipe database but couldn't find anything{criteria_text} that matches what you're looking for.

Would you like me to search the internet to find some recipes that match your request? If so, I can help you find options and you can decide if you want to save any of them to your database.

You can also specify:
- Particular websites you'd like me to focus on (like AllRecipes, Food Network, etc.)
- Specific cuisine types or cooking styles
- Difficulty level preferences
- Any other search parameters

Just let me know if you'd like me to proceed with an internet search and any specific preferences you have!"""

    # Keep existing legacy methods for backward compatibility
    def get_recipe_suggestions_by_ingredients(self, ingredients: List[str]) -> str:
        """Get recipe suggestions based on available ingredients"""
        if not self.is_configured():
            return "AI features require OpenAI API key configuration."

        try:
            # Search for recipes containing any of the ingredients
            recipes_with_ingredients = []
            for ingredient in ingredients:
                matching_recipes = self.search_recipes_by_criteria({"ingredient": ingredient})
                recipes_with_ingredients.extend(matching_recipes)

            # Remove duplicates
            unique_recipes = {recipe['id']: recipe for recipe in recipes_with_ingredients}.values()

            if not unique_recipes:
                response = f"""I couldn't find any recipes in your database that use {', '.join(ingredients)}.

Would you like me to search the internet for recipes using these ingredients? I can look for:
- Recipes from specific cooking websites
- Particular cuisine styles
- Easy vs. advanced cooking levels
- Quick meal options

Just let me know if you'd like me to search online and any preferences you have!"""

                button = self.create_recipe_action_button()
                response += f"\n\nOr create your own recipe:\n[ACTION_BUTTON:{json.dumps(button)}]"
                return response

            # Format response
            recipe_list = ""
            for recipe in list(unique_recipes)[:5]:  # Limit to 5 suggestions
                recipe_list += f"\n• **{recipe['name']}** - {recipe['genre']} recipe for {recipe['serving_size']} people"
                recipe_list += f"\n  Total time: {recipe['total_time']} minutes"

            response = f"Great! I found some recipes in your database that use {', '.join(ingredients)}:\n{recipe_list}"
            response += f"\n\nWould you like me to provide the full recipe details for any of these, or would you like me to search the internet for additional options?"

            # Add action button
            button = self.create_recipe_action_button()
            response += f"\n\n[ACTION_BUTTON:{json.dumps(button)}]"

            return response

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {e}")
            return "Sorry, I couldn't retrieve recipe suggestions at the moment."


# Global AI helper instance
ai_helper = AIHelper()
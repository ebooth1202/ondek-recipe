from .base_imports import *


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

            if "name" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["name"]
            elif "recipe_name" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["recipe_name"]
            elif "title" in raw_recipe_data:
                formatted_recipe["recipe_name"] = raw_recipe_data["title"]

            if "description" in raw_recipe_data:
                description = raw_recipe_data["description"]
                if len(description) <= 500:
                    formatted_recipe["description"] = description
                else:
                    formatted_recipe["description"] = description[:497] + "..."

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

            for field in ["serving_size", "genre", "prep_time", "cook_time"]:
                if field in raw_recipe_data:
                    formatted_recipe[field] = raw_recipe_data[field]

            notes = []
            if "notes" in raw_recipe_data:
                if isinstance(raw_recipe_data["notes"], list):
                    notes.extend(raw_recipe_data["notes"])
                elif isinstance(raw_recipe_data["notes"], str):
                    notes.append(raw_recipe_data["notes"])
            formatted_recipe["notes"] = notes

            if "dietary_restrictions" in raw_recipe_data:
                formatted_recipe["dietary_restrictions"] = raw_recipe_data["dietary_restrictions"]

            return formatted_recipe

        except Exception as e:
            logger.error(f"Error formatting recipe for form: {e}")
            return None

    def format_for_preview(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format recipe data specifically for preview modal"""
        try:
            recipe_name = recipe_data.get('name', recipe_data.get('recipe_name', 'Unknown Recipe'))
            description = recipe_data.get('description', '')

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

            instructions = recipe_data.get('instructions', [])
            if isinstance(instructions, str):
                instructions = self._split_instructions(instructions)

            prep_time = recipe_data.get('prep_time', 0)
            cook_time = recipe_data.get('cook_time', 0)
            total_time = prep_time + cook_time

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
        parts = ingredient_str.strip().split(' ', 2)
        if len(parts) >= 3:
            try:
                quantity = float(parts[0])
                unit = parts[1]
                name = parts[2]
                return {"name": name, "quantity": quantity, "unit": unit}
            except ValueError:
                pass

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
        steps = re.split(r'\d+\.\s*|\n\s*', instructions)
        return [step.strip() for step in steps if step.strip()]
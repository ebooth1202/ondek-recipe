from .base_imports import *


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
                original_serving_size = 4

            scaling_factor = new_serving_size / original_serving_size

            logger.info(
                f"Scaling recipe '{recipe.get('name', 'Unknown')}' from {original_serving_size} to {new_serving_size} servings (factor: {scaling_factor})")

            scaled_recipe = recipe.copy()
            scaled_recipe['serving_size'] = new_serving_size
            scaled_recipe['original_serving_size'] = original_serving_size
            scaled_recipe['scaling_factor'] = scaling_factor

            if 'ingredients' in recipe:
                scaled_ingredients = []
                for ingredient in recipe['ingredients']:
                    if isinstance(ingredient, dict):
                        scaled_ingredient = ingredient.copy()
                        if 'quantity' in ingredient:
                            original_quantity = ingredient['quantity']
                            scaled_quantity = self._scale_quantity(original_quantity, scaling_factor)
                            scaled_ingredient['quantity'] = scaled_quantity
                        scaled_ingredients.append(scaled_ingredient)
                    elif isinstance(ingredient, str):
                        scaled_ingredient_str = self._scale_ingredient_string(ingredient, scaling_factor)
                        scaled_ingredients.append(scaled_ingredient_str)
                    else:
                        scaled_ingredients.append(ingredient)

                scaled_recipe['ingredients'] = scaled_ingredients

            original_name = recipe.get('name', recipe.get('recipe_name', 'Unknown Recipe'))
            scaled_recipe['name'] = f"{original_name} (Scaled for {new_serving_size})"
            if 'recipe_name' in scaled_recipe:
                scaled_recipe['recipe_name'] = scaled_recipe['name']

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

            if scaled < 0.1:
                return round(scaled, 3)
            elif scaled < 1:
                return round(scaled, 2)
            elif scaled < 10:
                return round(scaled, 1)
            else:
                return round(scaled)

        except (ValueError, TypeError):
            return quantity

    def _scale_ingredient_string(self, ingredient_str: str, scaling_factor: float) -> str:
        """Scale an ingredient string by parsing and scaling the quantity"""
        try:
            parts = ingredient_str.strip().split(' ', 2)
            if len(parts) >= 2:
                quantity_part = parts[0]

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

                try:
                    original_quantity = float(quantity_part)
                    scaled_quantity = self._scale_quantity(original_quantity, scaling_factor)
                    scaled_display = self._convert_to_fraction(scaled_quantity)
                    return f"{scaled_display} {' '.join(parts[1:])}"
                except ValueError:
                    pass

            return ingredient_str

        except Exception as e:
            logger.warning(f"Could not scale ingredient string '{ingredient_str}': {e}")
            return ingredient_str

    def _convert_to_fraction(self, decimal_value: float) -> str:
        """Convert decimal to fraction when it makes sense, otherwise return decimal"""
        try:
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

            for frac_decimal, frac_str in common_fractions.items():
                if abs(decimal_value - frac_decimal) < 0.05:
                    return frac_str

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

            scaling_patterns = [
                r'scale.*(?:for|to)\s*(\d+)',
                r'make.*(?:for|to)\s*(\d+)',
                r'adjust.*(?:for|to)\s*(\d+)',
                r'resize.*(?:for|to)\s*(\d+)',
                r'change.*(?:for|to)\s*(\d+)',
                r'scale.*(?:this|them|it).*(?:for|to)\s*(\d+)',
                r'scale.*(?:this|them|it).*(\d+)',
                r'make.*(?:this|them|it).*(?:for|to)\s*(\d+)',
                r'double.*recipe',
                r'half.*recipe',
                r'triple.*recipe',
                r'double.*(?:this|them|it)',
                r'half.*(?:this|them|it)',
                r'triple.*(?:this|them|it)'
            ]

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
                            if new_size > 0 and new_size <= 50:
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
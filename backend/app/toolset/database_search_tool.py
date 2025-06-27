from .base_imports import *


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

                search_patterns = [escaped_ingredient]

                if ingredient_term.endswith('s') and len(ingredient_term) > 3:
                    singular = ingredient_term[:-1]
                    search_patterns.append(re.escape(singular))
                elif not ingredient_term.endswith('s'):
                    plural = ingredient_term + 's'
                    search_patterns.append(re.escape(plural))

                pattern_string = "|".join(search_patterns)

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
                    object_ids = []
                    for fav_id in favorite_recipe_ids:
                        try:
                            if isinstance(fav_id, str):
                                object_ids.append(ObjectId(fav_id))
                            else:
                                object_ids.append(fav_id)
                        except:
                            object_ids.append(fav_id)

                    query["_id"] = {"$in": object_ids}
                else:
                    return []

            logger.info(f"Database search query: {query}")
            recipes = list(db.recipes.find(query).limit(50))

            if len(recipes) == 0 and "ingredient" in criteria and " " in criteria["ingredient"]:
                words = criteria["ingredient"].split()
                word_patterns = []

                for word in words:
                    word_patterns.append(re.escape(word))
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
                favorite_recipe_ids = []
                try:
                    favorite_docs = list(db.favorites.find({}, {"recipe_id": 1}))
                    favorite_recipe_ids = [doc["recipe_id"] for doc in favorite_docs if "recipe_id" in doc]
                except Exception as e:
                    logger.error(f"Error getting favorite recipe IDs for count: {e}")

                if favorite_recipe_ids:
                    object_ids = []
                    for fav_id in favorite_recipe_ids:
                        try:
                            if isinstance(fav_id, str):
                                object_ids.append(ObjectId(fav_id))
                            else:
                                object_ids.append(fav_id)
                        except:
                            object_ids.append(fav_id)

                    query["_id"] = {"$in": object_ids}
                else:
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
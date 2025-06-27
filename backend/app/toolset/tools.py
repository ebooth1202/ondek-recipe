# backend/app/toolset/tools.py - Complete corrected version with proper syntax

import os
import logging
import json
import re
import io
import tempfile
import csv
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import requests
from urllib.parse import quote_plus, urlparse

# Set up logger FIRST
logger = logging.getLogger(__name__)

# Note: AI helper will be imported lazily to avoid circular imports
AI_HELPER_AVAILABLE = True  # Assume available until proven otherwise

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup4 not available - will use basic text extraction")

# Try to import database with error handling
try:
    try:
        from ..database import db

        logger.info("Database imported successfully from app.database")
    except ImportError:
        try:
            from app.database import db

            logger.info("Database imported successfully from app.database")
        except ImportError:
            try:
                from database import db

                logger.info("Database imported successfully using absolute import")
            except ImportError:
                import sys

                current_dir = os.path.dirname(os.path.abspath(__file__))

                potential_paths = [
                    os.path.join(current_dir, '..'),
                    os.path.join(current_dir, '..', '..'),
                    os.path.join(current_dir, '..', '..', '..'),
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


    # Creating a mock database for development/fallback
    class MockRecipeCollection:
        @staticmethod
        def find(query=None, *args, **kwargs):
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
        favorites = MockRecipeCollection()


    db = MockDatabase()
    db_available = False


class RecipeSearchTool:
    """Tool for searching external recipe sources"""

    def __init__(self):
        self.name = "search_external_recipes"
        self.description = "Search the internet for recipes from various cooking websites"

    def execute(self, criteria: Dict[str, Any], search_params: Dict[str, Any] = None) -> List[Dict]:
        """Search for recipes from external sources"""
        try:
            logger.info(f"RecipeSearchTool.execute called with criteria: {criteria}")

            ingredient = criteria.get('ingredient', 'chocolate chip cookies') if criteria else 'chocolate chip cookies'
            logger.info(f"Searching for ingredient: {ingredient}")

            selected_website = None
            if search_params and search_params.get('specific_websites'):
                websites = search_params.get('specific_websites', [])
                if isinstance(websites, list) and len(websites) > 0:
                    selected_website = websites[0]
                    logger.info(f"Specific website requested: {selected_website}")

            if selected_website:
                return self._search_website_for_recipes(ingredient, selected_website, criteria)
            else:
                return self._search_multiple_sites(ingredient, criteria)

        except Exception as e:
            logger.error(f"Error in external recipe search: {e}")
            return self._generate_fallback_recipe(criteria.get('ingredient', 'recipe'))

    def _search_website_for_recipes(self, ingredient: str, website: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Search a specific website for recipes"""
        try:
            logger.info(f"Searching {website} for recipes about: {ingredient}")

            search_urls = self._build_search_urls(ingredient, website)
            all_recipes = []
            max_recipes = 4

            for search_url in search_urls:
                if len(all_recipes) >= max_recipes:
                    break

                logger.info(f"Trying to access URL: {search_url}")
                search_page_content = self._fetch_webpage_content(search_url)

                if not search_page_content:
                    logger.warning(f"Failed to get content from {search_url}")
                    continue

                logger.info(f"Successfully got {len(search_page_content)} characters from {search_url}")

                # Check if we got a valid page (be more specific about error detection)
                content_lower = search_page_content.lower()
                if (("page not found" in content_lower or
                     "404 error" in content_lower or
                     "not found" in content_lower[:1000]) and  # Only check first 1000 chars
                        "recipe" not in content_lower[:5000]):  # If no recipe mentions in first 5000 chars
                    logger.warning(f"Got error page from {search_url}")
                    continue

                # Try to extract recipe URLs even if we're not 100% sure
                recipe_urls = self._extract_recipe_urls_from_search(search_page_content, website)
                logger.info(f"Extracted {len(recipe_urls)} recipe URLs from search results")

                # Log some sample URLs for debugging
                if recipe_urls:
                    logger.info(f"Sample recipe URLs: {recipe_urls[:3]}")
                else:
                    # Debug: Let's see what kind of content we got
                    logger.warning(f"No recipe URLs found. Page title area: {search_page_content[:500]}")
                    # Look for any links at all
                    if BS4_AVAILABLE:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(search_page_content, 'html.parser')
                        all_links = soup.find_all('a', href=True)
                        logger.info(f"Found {len(all_links)} total links on page")
                        sample_links = [link.get('href') for link in all_links[:10]]
                        logger.info(f"Sample links: {sample_links}")

                for recipe_url in recipe_urls[:3]:
                    if len(all_recipes) >= max_recipes:
                        break

                    logger.info(f"Attempting to scrape recipe from: {recipe_url}")
                    recipe_data = self._scrape_and_parse_recipe(recipe_url, ingredient)
                    if recipe_data:
                        all_recipes.append(recipe_data)
                        logger.info(f"Successfully parsed recipe: {recipe_data.get('name', 'Unknown')}")
                    else:
                        logger.warning(f"Failed to parse recipe from: {recipe_url}")

            if all_recipes:
                logger.info(f"Found {len(all_recipes)} real recipes from {website}")
                return all_recipes
            else:
                logger.warning(f"Could not parse any real recipes from {website}, using fallback")
                return self._generate_fallback_recipes_for_site(ingredient, website, criteria)

        except Exception as e:
            logger.error(f"Error searching {website}: {e}")
            return self._generate_fallback_recipes_for_site(ingredient, website, criteria)

    def _search_multiple_sites(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Search multiple sites for recipes"""
        try:
            popular_sites = ['allrecipes.com', 'foodnetwork.com', 'food.com']
            all_recipes = []
            max_recipes = 3

            for site in popular_sites:
                if len(all_recipes) >= max_recipes:
                    break

                site_recipes = self._search_website_for_recipes(ingredient, site, criteria)
                if site_recipes and site_recipes[0].get('source') != 'fallback':
                    all_recipes.extend(site_recipes[:1])

            return all_recipes if all_recipes else self._generate_fallback_recipes_for_ingredient(ingredient, criteria)

        except Exception as e:
            logger.error(f"Error in multi-site search: {e}")
            return self._generate_fallback_recipes_for_ingredient(ingredient, criteria)

    def _build_search_urls(self, ingredient: str, website: str) -> List[str]:
        """Build search URLs for different recipe websites"""
        search_urls = []
        clean_ingredient = ingredient.replace(' ', '%20')

        if 'allrecipes.com' in website:
            # Updated AllRecipes search URL format
            search_urls.append(f"https://www.allrecipes.com/search?q={clean_ingredient}")
        elif 'foodnetwork.com' in website:
            # Updated Food Network search URL format
            search_urls.append(f"https://www.foodnetwork.com/search/{clean_ingredient}")
        elif 'food.com' in website:
            search_urls.append(f"https://www.food.com/search/{clean_ingredient}")
        elif 'epicurious.com' in website:
            search_urls.append(f"https://www.epicurious.com/search?q={clean_ingredient}")
        elif 'pinterest.com' in website:
            search_urls.append(f"https://www.pinterest.com/search/pins/?q={clean_ingredient}%20recipe")
        else:
            # Generic fallback
            search_urls.append(f"https://{website}/search?q={clean_ingredient}+recipe")

        return search_urls

    def _extract_recipe_urls_from_search(self, html_content: str, website: str) -> List[str]:
        """Extract recipe URLs from search results page"""
        try:
            recipe_urls = []

            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                links = soup.find_all('a', href=True)

                # Website-specific URL extraction patterns
                if 'allrecipes.com' in website:
                    for link in links:
                        href = link.get('href', '')
                        # AllRecipes recipe URLs follow pattern: /recipe/[id]/recipe-name/
                        if '/recipe/' in href and href.count('/') >= 3:
                            if href.startswith('http'):
                                recipe_urls.append(href)
                            elif href.startswith('/'):
                                recipe_urls.append(f"https://www.allrecipes.com{href}")
                elif 'foodnetwork.com' in website:
                    for link in links:
                        href = link.get('href', '')
                        if '/recipes/' in href:
                            if href.startswith('http'):
                                recipe_urls.append(href)
                            elif href.startswith('/'):
                                recipe_urls.append(f"https://www.foodnetwork.com{href}")
                else:
                    # Generic extraction for other sites
                    for link in links:
                        href = link.get('href', '')
                        if '/recipe' in href.lower():
                            if href.startswith('http'):
                                recipe_urls.append(href)
                            elif href.startswith('/'):
                                recipe_urls.append(f"https://{website}{href}")
            else:
                # Fallback regex extraction
                if 'allrecipes.com' in website:
                    pattern = r'https?://(?:www\.)?allrecipes\.com/recipe/\d+/[^"\s<>]+'
                else:
                    pattern = rf'https?://{re.escape(website)}/[^"\s<>]*recipe[^"\s<>]*'

                matches = re.findall(pattern, html_content)
                recipe_urls.extend(matches)

            # Remove duplicates and filter valid URLs
            unique_urls = []
            seen = set()
            for url in recipe_urls:
                if url not in seen and len(url) > 20:  # Basic URL validation
                    seen.add(url)
                    unique_urls.append(url)

            # Limit results
            unique_urls = unique_urls[:10]
            logger.info(f"Extracted {len(unique_urls)} unique recipe URLs from {website}")
            return unique_urls

        except Exception as e:
            logger.error(f"Error extracting recipe URLs: {e}")
            return []

    def _fetch_webpage_content(self, url: str) -> Optional[str]:
        """Fetch webpage content with proper headers and retry logic"""
        try:
            # Rotate through different User-Agent strings to avoid blocking
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]

            import random

            for attempt in range(3):  # Try up to 3 times
                try:
                    headers = {
                        'User-Agent': random.choice(user_agents),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0',
                    }

                    # Add a small delay between attempts to avoid rate limiting
                    if attempt > 0:
                        import time
                        time.sleep(1)

                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True,
                        verify=True
                    )

                    if response.status_code == 200:
                        logger.info(f"Successfully fetched content from {url} (attempt {attempt + 1})")
                        return response.text
                    elif response.status_code == 403:
                        logger.warning(f"Access forbidden (403) for {url} - trying different User-Agent")
                        continue
                    elif response.status_code == 404:
                        logger.warning(f"Page not found (404) for {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status_code} for {url} (attempt {attempt + 1})")

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                    continue

            logger.error(f"All attempts failed for {url}")
            return None

        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {e}")
            return None

    def _scrape_and_parse_recipe(self, url: str, ingredient: str) -> Optional[Dict]:
        """Scrape a recipe URL and parse it"""
        try:
            logger.info(f"Scraping recipe from: {url}")

            page_content = self._fetch_webpage_content(url)
            if not page_content:
                return None

            structured_data = self._extract_structured_recipe_data(page_content)
            if structured_data:
                structured_data['url'] = url
                structured_data['source'] = self._extract_domain_name(url)
                return structured_data

            # Try AI parsing if available (lazy import to avoid circular dependency)
            try:
                from ..utils.ai_helper import ai_helper

                if ai_helper and ai_helper.is_configured():
                    clean_text = self._extract_clean_recipe_text(page_content)

                    if clean_text and len(clean_text) > 100:
                        try:
                            response = ai_helper.client.chat.completions.create(
                                model=ai_helper.model,
                                messages=[
                                    {"role": "system", "content": """Extract recipe information from webpage content and return as JSON.
Extract these fields (return null if recipe not found):
{
  "name": "recipe title",
  "description": "brief description", 
  "ingredients": [{"name": "ingredient", "quantity": number, "unit": "cup|tablespoon|etc"}],
  "instructions": ["step 1", "step 2", ...],
  "serving_size": number,
  "prep_time": minutes_as_number,
  "cook_time": minutes_as_number,
  "genre": "breakfast|lunch|dinner|snack|dessert|appetizer",
  "notes": ["tip 1", "tip 2", ...],
  "dietary_restrictions": ["gluten_free", "dairy_free", "egg_free"]
}
Return ONLY the JSON object."""},
                                    {"role": "user", "content": f"Extract recipe from: {clean_text[:4000]}"}
                                ],
                                max_tokens=1200,
                                temperature=0.0
                            )

                            result_text = response.choices[0].message.content.strip()
                            if result_text.startswith("```json"):
                                result_text = result_text[7:-3]
                            elif result_text.startswith("```"):
                                result_text = result_text[3:-3]

                            parsed_recipe = json.loads(result_text)

                            if parsed_recipe and parsed_recipe.get('name'):
                                parsed_recipe['url'] = url
                                parsed_recipe['source'] = self._extract_domain_name(url)
                                return parsed_recipe

                        except (json.JSONDecodeError, KeyError) as e:
                            logger.error(f"Error parsing AI response: {e}")

            except ImportError:
                logger.warning("AI Helper not available for recipe parsing")

            # Fallback to basic recipe creation
            return self._create_basic_recipe_from_page(page_content, url, ingredient)

        except Exception as e:
            logger.error(f"Error scraping recipe from {url}: {e}")
            return None

    def _extract_structured_recipe_data(self, html_content: str) -> Optional[Dict]:
        """Extract recipe data from JSON-LD structured data"""
        try:
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                json_scripts = soup.find_all('script', type='application/ld+json')

                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            data = data[0] if data else {}

                        if data.get('@type') == 'Recipe':
                            return self._parse_recipe_schema(data)

                        if 'graph' in data:
                            for item in data['graph']:
                                if item.get('@type') == 'Recipe':
                                    return self._parse_recipe_schema(item)

                    except (json.JSONDecodeError, KeyError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return None

    def _parse_recipe_schema(self, schema_data: Dict) -> Optional[Dict]:
        """Parse Recipe schema data into our format"""
        try:
            recipe = {
                'name': schema_data.get('name', ''),
                'description': schema_data.get('description', ''),
                'ingredients': [],
                'instructions': [],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': [],
                'dietary_restrictions': []
            }

            recipe_ingredients = schema_data.get('recipeIngredient', [])
            if isinstance(recipe_ingredients, list):
                for ing_text in recipe_ingredients:
                    parsed_ing = self._parse_ingredient_text(str(ing_text))
                    if parsed_ing:
                        recipe['ingredients'].append(parsed_ing)

            instructions = schema_data.get('recipeInstructions', [])
            if isinstance(instructions, list):
                for inst in instructions:
                    if isinstance(inst, str):
                        recipe['instructions'].append(inst)
                    elif isinstance(inst, dict):
                        text = inst.get('text', inst.get('name', ''))
                        if text:
                            recipe['instructions'].append(text)

            prep_time = schema_data.get('prepTime', '')
            cook_time = schema_data.get('cookTime', '')
            recipe['prep_time'] = self._parse_iso_duration(prep_time)
            recipe['cook_time'] = self._parse_iso_duration(cook_time)

            recipe_yield = schema_data.get('recipeYield', schema_data.get('yield', ''))
            if recipe_yield:
                try:
                    match = re.search(r'\d+', str(recipe_yield))
                    if match:
                        recipe['serving_size'] = int(match.group())
                except:
                    pass

            if recipe['name'] and len(recipe['ingredients']) > 0 and len(recipe['instructions']) > 0:
                return recipe

            return None

        except Exception as e:
            logger.error(f"Error parsing recipe schema: {e}")
            return None

    def _extract_clean_recipe_text(self, html_content: str) -> str:
        """Extract clean text content focusing on recipe-relevant sections"""
        try:
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')

                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'ad']):
                    element.decompose()

                recipe_containers = soup.find_all(['div', 'section', 'article'],
                                                  class_=re.compile(r'recipe|ingredient|instruction|direction', re.I))

                if recipe_containers:
                    recipe_text = ' '.join([container.get_text() for container in recipe_containers])
                else:
                    main_content = soup.find(['main', 'article', 'div'],
                                             class_=re.compile(r'content|main|recipe', re.I))
                    if main_content:
                        recipe_text = main_content.get_text()
                    else:
                        recipe_text = soup.get_text()

                recipe_text = re.sub(r'\s+', ' ', recipe_text).strip()
                return recipe_text

            else:
                text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text

        except Exception as e:
            logger.error(f"Error extracting clean text: {e}")
            return ""

    def _create_basic_recipe_from_page(self, html_content: str, url: str, ingredient: str) -> Dict:
        """Create a basic recipe when structured data isn't available"""
        try:
            title = "Recipe"
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    title = re.sub(r'\s*\|\s*.*$', '', title)
                    title = re.sub(r'\s*-\s*.*$', '', title)

            return {
                'name': title,
                'description': f'Recipe found on {self._extract_domain_name(url)}',
                'ingredients': [
                    {'name': f'{ingredient} (see website for details)', 'quantity': 1, 'unit': 'recipe'}
                ],
                'instructions': [
                    f'Visit the original recipe at {url} for complete instructions'
                ],
                'serving_size': 4,
                'prep_time': 30,
                'cook_time': 30,
                'genre': 'dinner',
                'notes': [f'Original recipe from {self._extract_domain_name(url)}'],
                'dietary_restrictions': []
            }

        except Exception as e:
            logger.error(f"Error creating basic recipe: {e}")
            return self._generate_fallback_recipe(ingredient)[0]

    def _parse_ingredient_text(self, text: str) -> Optional[Dict]:
        """Parse ingredient text into quantity, unit, name"""
        try:
            pattern = r'^(\d+(?:\.\d+)?(?:/\d+)?)\s*(\w+)?\s+(.+)$'
            match = re.match(pattern, text.strip())

            if match:
                quantity_str, unit, name = match.groups()

                try:
                    if '/' in quantity_str:
                        parts = quantity_str.split('/')
                        quantity = float(parts[0]) / float(parts[1])
                    else:
                        quantity = float(quantity_str)
                except:
                    quantity = 1.0

                if not unit:
                    unit = 'piece'

                return {
                    'name': name.strip(),
                    'quantity': quantity,
                    'unit': unit.lower()
                }
            else:
                return {
                    'name': text.strip(),
                    'quantity': 1,
                    'unit': 'piece'
                }

        except Exception as e:
            logger.error(f"Error parsing ingredient text '{text}': {e}")
            return None

    def _parse_iso_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration or text duration to minutes"""
        try:
            if not duration_str:
                return 0

            duration_str = str(duration_str).upper()

            if duration_str.startswith('PT'):
                total_minutes = 0
                hours_match = re.search(r'(\d+)H', duration_str)
                if hours_match:
                    total_minutes += int(hours_match.group(1)) * 60
                minutes_match = re.search(r'(\d+)M', duration_str)
                if minutes_match:
                    total_minutes += int(minutes_match.group(1))
                return total_minutes

            total_minutes = 0
            hours_match = re.search(r'(\d+)\s*(?:hour|hr)', duration_str, re.IGNORECASE)
            if hours_match:
                total_minutes += int(hours_match.group(1)) * 60
            minutes_match = re.search(r'(\d+)\s*(?:minute|min)', duration_str, re.IGNORECASE)
            if minutes_match:
                total_minutes += int(minutes_match.group(1))
            return total_minutes

        except Exception as e:
            logger.error(f"Error parsing duration '{duration_str}': {e}")
            return 0

    def _extract_domain_name(self, url: str) -> str:
        """Extract clean domain name from URL"""
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return 'external'

    def _generate_fallback_recipe(self, ingredient: str) -> List[Dict]:
        """Generate a single fallback recipe when everything fails"""
        return [{
            "name": f"Classic {ingredient.title()} Recipe",
            "source": "fallback",
            "description": f"A reliable recipe for {ingredient} when search encounters issues.",
            "url": "https://example.com/fallback-recipe",
            "ingredients": [
                {"name": "main ingredient", "quantity": 1, "unit": "cup"},
                {"name": "supporting ingredients", "quantity": 2, "unit": "tablespoons"}
            ],
            "instructions": [
                "Combine ingredients according to your preferred method",
                "Cook as desired until done"
            ],
            "serving_size": 4,
            "prep_time": 15,
            "cook_time": 20,
            "genre": "dinner",
            "notes": ["Fallback recipe - please try searching again"],
            "dietary_restrictions": [],
            "cuisine_type": "general"
        }]

    def _generate_fallback_recipes_for_site(self, ingredient: str, website: str, criteria: Dict[str, Any]) -> List[
        Dict]:
        """Generate fallback recipes when site-specific search fails"""
        website_name = website.replace('.com', '').title()

        return [{
            "name": f"{website_name} Style {ingredient.title()}",
            "source": website,
            "description": f"A {ingredient} recipe in the style of {website_name}. (Unable to fetch live data)",
            "url": f"https://{website}/search?q={ingredient.replace(' ', '+')}",
            "ingredients": [
                {"name": ingredient.split()[0] if ingredient != 'recipe' else 'main ingredient', "quantity": 2,
                 "unit": "cups"},
                {"name": "additional ingredients", "quantity": 1, "unit": "cup"}
            ],
            "instructions": [
                f"Follow {website_name}'s typical preparation method",
                "Cook according to your preference"
            ],
            "serving_size": criteria.get('serving_size', 4),
            "prep_time": 15,
            "cook_time": 25,
            "genre": criteria.get('genre', 'dinner'),
            "notes": [f"Please visit {website} directly for the most current recipes"],
            "dietary_restrictions": [],
            "cuisine_type": "general"
        }]

    def test_search_url(self, ingredient: str, website: str) -> Dict[str, Any]:
        """Test function to debug search URLs"""
        try:
            search_urls = self._build_search_urls(ingredient, website)
            results = {}

            for i, url in enumerate(search_urls):
                logger.info(f"Testing URL {i + 1}: {url}")
                content = self._fetch_webpage_content(url)

                results[f"url_{i + 1}"] = {
                    "url": url,
                    "success": content is not None,
                    "content_length": len(content) if content else 0,
                    "has_recipe_links": False
                }

                if content:
                    # Quick check for recipe-related content
                    content_lower = content.lower()
                    recipe_indicators = ['recipe', 'ingredient', 'instruction', 'cooking', 'baking']
                    results[f"url_{i + 1}"]["has_recipe_content"] = any(
                        word in content_lower for word in recipe_indicators)

                    # Try to extract some URLs
                    recipe_urls = self._extract_recipe_urls_from_search(content, website)
                    results[f"url_{i + 1}"]["recipe_urls_found"] = len(recipe_urls)
                    results[f"url_{i + 1}"]["sample_urls"] = recipe_urls[:3]

            return results

        except Exception as e:
            return {"error": str(e)}
        """Generate fallback recipes for multi-site search failures"""
        return [{
            "name": f"Popular {ingredient.title()} Recipe",
            "source": "multiple sites",
            "description": f"A well-loved {ingredient} recipe from across the web.",
            "url": f"https://www.google.com/search?q={ingredient.replace(' ', '+')}+recipe",
            "ingredients": [
                {"name": ingredient if ingredient != 'recipe' else 'main ingredient', "quantity": 1, "unit": "cup"},
                {"name": "complementary ingredients", "quantity": 2, "unit": "tablespoons"}
            ],
            "instructions": [
                "Prepare ingredients as needed",
                "Combine and cook according to standard methods"
            ],
            "serving_size": criteria.get('serving_size', 4),
            "prep_time": 20,
            "cook_time": 25,
            "genre": criteria.get('genre', 'dinner'),
            "notes": ["Recipe data temporarily unavailable - please try again"],
            "dietary_restrictions": [],
            "cuisine_type": "popular"
        }]

    def test_search_url(self, ingredient: str, website: str) -> Dict[str, Any]:
        """Test function to debug search URLs"""
        try:
            search_urls = self._build_search_urls(ingredient, website)
            results = {}

            for i, url in enumerate(search_urls):
                logger.info(f"Testing URL {i + 1}: {url}")
                content = self._fetch_webpage_content(url)

                results[f"url_{i + 1}"] = {
                    "url": url,
                    "success": content is not None,
                    "content_length": len(content) if content else 0,
                    "has_recipe_links": False
                }

                if content:
                    # Quick check for recipe-related content
                    content_lower = content.lower()
                    recipe_indicators = ['recipe', 'ingredient', 'instruction', 'cooking', 'baking']
                    results[f"url_{i + 1}"]["has_recipe_content"] = any(
                        word in content_lower for word in recipe_indicators)

                    # Try to extract some URLs
                    recipe_urls = self._extract_recipe_urls_from_search(content, website)
                    results[f"url_{i + 1}"]["recipe_urls_found"] = len(recipe_urls)
                    results[f"url_{i + 1}"]["sample_urls"] = recipe_urls[:3]

            return results

        except Exception as e:
            return {"error": str(e)}


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
            "source": "Your Recipe Database"}


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
            return "PDF parsing not implemented yet"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
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


class CookingTechniqueExplainerTool:
    """Tool for explaining cooking techniques and terms using ChatGPT with Rupert's personality"""

    def __init__(self):
        self.name = "explain_cooking_technique"
        self.description = "Explain cooking techniques and culinary terms with Rupert's goofy personality"

    def detect_technique_question(self, user_message: str) -> Optional[str]:
        """Detect if user is asking about a cooking technique or term"""
        user_lower = user_message.lower().strip()

        question_indicators = [
            'what is', 'what does', 'how do i', 'how do you', 'how to', 'explain', 'define',
            'meaning of', 'technique', 'method', 'term', '?'
        ]

        has_question_pattern = any(indicator in user_lower for indicator in question_indicators)

        if not has_question_pattern:
            return None

        technique_map = {
            'sauté': ['saute', 'sautee', 'sautte', 'sauttee', 'sautteing', 'sauteing', 'sautéing'],
            'sautéing': ['sauteing', 'sautteing', 'sauteeing', 'sautting'],
            'braise': ['braising', 'braze', 'brazing'],
            'braising': ['brasing', 'brazing'],
            'julienne': ['julianne', 'julian', 'juliennes'],
            'dice': ['dicing', 'diced'],
            'chop': ['chopping', 'chopped'],
            'mince': ['mincing', 'minced'],
            'blanch': ['blanching', 'blanched'],
            'poach': ['poaching', 'poached'],
            'roast': ['roasting', 'roasted'],
            'grill': ['grilling', 'grilled'],
            'steam': ['steaming', 'steamed'],
            'fry': ['frying', 'fried'],
            'bake': ['baking', 'baked'],
            'broil': ['broiling', 'broiled'],
            'confit': ['confits', 'confiting'],
            'emulsify': ['emulsification', 'emulsifying'],
            'deglaze': ['deglazing', 'deglazed'],
            'roux': ['rouxs'],
            'mise en place': ['mise', 'mise-en-place', 'miseinplace'],
            'reduction': ['reduce', 'reducing'],
            'caramelize': ['caramelizing', 'caramelized', 'carmelize', 'carmelizing'],
            'sear': ['searing', 'seared'],
            'simmer': ['simmering', 'simmered'],
            'fold': ['folding', 'folded'],
            'whip': ['whipping', 'whipped'],
            'knead': ['kneading', 'kneaded'],
            'proof': ['proofing', 'proofed', 'prove', 'proving'],
            'tempering': ['temper', 'tempered'],
            'flambé': ['flambe', 'flaming', 'flame'],
            'sous vide': ['sousvide', 'sous-vide'],
            'marinade': ['marinating', 'marinated', 'marinate']
        }

        for base_technique, variations in technique_map.items():
            all_terms = [base_technique] + variations
            for term in all_terms:
                if term in user_lower:
                    logger.info(
                        f"Detected technique '{base_technique}' from term '{term}' in message: '{user_message}'")
                    return base_technique

        cooking_actions = [
            'cook', 'cooking', 'prepare', 'preparing', 'cut', 'cutting', 'heat', 'heating',
            'mix', 'mixing', 'stir', 'stirring', 'season', 'seasoning', 'salt', 'pepper'
        ]

        for action in cooking_actions:
            if action in user_lower and len(user_lower.split()) <= 6:
                logger.info(f"Detected cooking action '{action}' in question: '{user_message}'")
                return action

        return None

    async def execute(self, technique_term: str, user_message: str, openai_client) -> Optional[str]:
        """Generate explanation for cooking technique using ChatGPT"""
        try:
            if not openai_client:
                return None

            system_prompt = f"""You are Rupert, a jovial, warm, and delightfully goofy cooking assistant AI for the Ondek Recipe app.

The user is asking about the cooking technique/term: "{technique_term}"

Your job is to explain this cooking technique in Rupert's signature style:
- Be educational but fun and engaging
- Use goofy analogies and metaphors (food-related when possible)
- Show enthusiasm and warmth
- Include practical tips that are actually helpful
- Use emojis sparingly but effectively
- Keep it informative but not overwhelming
- Make cooking feel approachable and fun

Structure your response like this:
1. A fun, goofy explanation of what the technique is
2. Why it's useful or when to use it
3. A couple of practical tips
4. Maybe mention what dishes use this technique

Keep Rupert's personality: jovial, warm, goofy, encouraging, and passionate about making cooking accessible!"""

            user_prompt = f"""The user asked: "{user_message}"

They want to know about the cooking technique/term: "{technique_term}"

Explain this cooking technique with your signature Rupert personality - be educational, fun, and goofy!"""

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating technique explanation: {e}")
            return None


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

            if 'url' in recipe:
                button_data['url'] = recipe['url']
            else:
                button_data['url'] = "/add-recipe"

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
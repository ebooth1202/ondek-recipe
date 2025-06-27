from .base_imports import *


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

    def _generate_fallback_recipes_for_site(self, ingredient: str, website: str, criteria: Dict[str, Any]) -> List[Dict]:
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

    def _generate_fallback_recipes_for_ingredient(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
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
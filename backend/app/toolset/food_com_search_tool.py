from .base_imports import *
from .recipe_cache import recipe_cache


class FoodComSearchTool:
    """Specialized tool for searching Food.com"""

    def __init__(self):
        self.name = "food_com_search"
        self.description = "Search Food.com for recipes"
        self.website = "food.com"

    def search_recipes(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Search Food.com for recipes with enhanced error handling"""
        try:
            logger.info(f"Searching Food.com for recipes about: {ingredient}")

            search_urls = self._build_search_urls(ingredient)
            all_recipes = []
            max_recipes = 3

            import time
            start_time = time.time()
            timeout_seconds = 30

            for search_url in search_urls:
                if len(all_recipes) >= max_recipes:
                    break

                if time.time() - start_time > timeout_seconds:
                    logger.warning(f"Search timeout reached for Food.com")
                    break

                logger.info(f"Trying to access Food.com URL: {search_url}")

                try:
                    search_page_content = self._fetch_webpage_content(search_url)
                except Exception as fetch_error:
                    logger.error(f"Error fetching Food.com {search_url}: {fetch_error}")
                    continue

                if not search_page_content:
                    logger.warning(f"Failed to get content from Food.com {search_url}")
                    continue

                logger.info(f"Successfully got {len(search_page_content)} characters from Food.com {search_url}")

                # Check if we got a valid page
                content_lower = search_page_content.lower()
                if (("page not found" in content_lower or
                     "404 error" in content_lower or
                     "not found" in content_lower[:1000]) and
                        "recipe" not in content_lower[:5000]):
                    logger.warning(f"Got error page from Food.com {search_url}")
                    continue

                try:
                    recipe_urls = self._extract_recipe_urls_from_search(search_page_content)
                except Exception as extract_error:
                    logger.error(f"Error extracting recipe URLs from Food.com {search_url}: {extract_error}")
                    continue

                logger.info(f"Extracted {len(recipe_urls)} recipe URLs from Food.com search results")

                if recipe_urls:
                    logger.info(f"Sample Food.com recipe URLs: {recipe_urls[:3]}")
                else:
                    logger.warning(f"No Food.com recipe URLs found. Page title area: {search_page_content[:500]}")

                recipe_process_start = time.time()
                recipes_processed = 0

                for recipe_url in recipe_urls[:2]:
                    if len(all_recipes) >= max_recipes:
                        break

                    if time.time() - recipe_process_start > 8 * (recipes_processed + 1):
                        logger.warning(f"Food.com recipe processing timeout for {recipe_url}")
                        break

                    if time.time() - start_time > timeout_seconds:
                        logger.warning(f"Food.com overall timeout reached, stopping recipe processing")
                        break

                    logger.info(f"Attempting to scrape Food.com recipe from: {recipe_url}")

                    try:
                        recipe_data = self._scrape_and_parse_recipe(recipe_url, ingredient)
                        recipes_processed += 1

                        if recipe_data and isinstance(recipe_data, dict):
                            all_recipes.append(recipe_data)
                            logger.info(f"Successfully parsed Food.com recipe: {recipe_data.get('name', 'Unknown')}")
                        else:
                            logger.warning(f"Failed to parse Food.com recipe from: {recipe_url}")
                    except Exception as recipe_error:
                        logger.error(f"Error processing Food.com recipe {recipe_url}: {recipe_error}")
                        recipes_processed += 1
                        continue

            total_time = time.time() - start_time
            logger.info(f"Food.com search completed in {total_time:.2f} seconds, found {len(all_recipes)} recipes")

            if all_recipes:
                logger.info(f"Found {len(all_recipes)} real recipes from Food.com")
                return all_recipes
            else:
                logger.warning(f"Could not parse any real recipes from Food.com, using fallback")
                fallback_recipes = self._generate_fallback_recipes(ingredient, criteria)
                return fallback_recipes if fallback_recipes else []

        except Exception as e:
            logger.error(f"Error searching Food.com: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                fallback_recipes = self._generate_fallback_recipes(ingredient, criteria)
                return fallback_recipes if fallback_recipes else []
            except:
                return []

    def _build_search_urls(self, ingredient: str) -> List[str]:
        """Build Food.com search URLs - testing with known recipes"""

        # For testing: Try some known Food.com recipe URLs that match the ingredient
        test_urls = []

        if 'caramel' in ingredient.lower():
            test_urls = [
                "https://www.food.com/recipe/caramel-cookies-95014",
                "https://www.food.com/recipe/soft-caramel-cookies-274455"
            ]
        elif 'chocolate' in ingredient.lower():
            test_urls = [
                "https://www.food.com/recipe/chocolate-chip-cookies-17254",
                "https://www.food.com/recipe/best-chocolate-chip-cookies-125911"
            ]
        else:
            # Fallback to popular cookies for testing
            test_urls = [
                "https://www.food.com/recipe/chocolate-chip-cookies-17254",
                "https://www.food.com/recipe/sugar-cookies-25773"
            ]

        logger.info(f"Testing Food.com with direct recipe URLs for '{ingredient}': {test_urls}")
        return test_urls

    def _extract_recipe_urls_from_search(self, html_content: str) -> List[str]:
        """Extract recipe URLs from Food.com search results page"""
        try:
            recipe_urls = []

            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link.get('href', '')

                    # FIXED: More specific Food.com recipe URL patterns
                    # Food.com recipes typically look like:
                    # /recipe/12345/recipe-name or /recipe/recipe-name-12345
                    if ('/recipe/' in href and
                            href.count('/') >= 3 and  # At least /recipe/something/something
                            # Exclude navigation/category pages
                            not any(exclude in href for exclude in [
                                '/recipe/all/', '/recipe/search', '/recipe/browse',
                                '/recipe/category', '/recipe/collection', '/recipe/popular',
                                '/recipe/recent', '/recipe/trending'
                            ]) and
                            # Must have either numbers or hyphenated name (actual recipes)
                            (re.search(r'/recipe/\d+', href) or re.search(r'/recipe/[\w-]+\d+', href) or
                             re.search(r'/recipe/[a-z-]+-\d+', href))):

                        if href.startswith('http'):
                            recipe_urls.append(href)
                        elif href.startswith('/'):
                            recipe_urls.append(f"https://www.food.com{href}")

            # Remove duplicates and filter valid URLs
            unique_urls = []
            seen = set()
            for url in recipe_urls:
                url = url.split('?')[0].split('#')[0]  # Remove query params and fragments
                if (url not in seen and len(url) > 20 and
                        not url.endswith(('.css', '.js', '.png', '.jpg')) and
                        # Double-check it's a real recipe URL
                        '/recipe/' in url and url.count('/') >= 4):
                    seen.add(url)
                    unique_urls.append(url)

            unique_urls = unique_urls[:10]
            logger.info(f"Extracted {len(unique_urls)} unique Food.com recipe URLs")

            # Debug: Log the URLs we found
            if unique_urls:
                logger.info(f"Food.com recipe URLs found: {unique_urls[:3]}")
            else:
                logger.warning("No valid Food.com recipe URLs found - checking page structure")
                # Debug: Let's see what URLs we DID find
                all_recipe_links = [link.get('href') for link in soup.find_all('a', href=True)
                                    if '/recipe/' in link.get('href', '')][:5]
                logger.info(f"All /recipe/ links found: {all_recipe_links}")

            return unique_urls

        except Exception as e:
            logger.error(f"Error extracting Food.com recipe URLs: {e}")
            return []

    def _fetch_webpage_content(self, url: str) -> Optional[str]:
        """Fetch webpage content avoiding compression issues"""
        try:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]

            import random

            for attempt in range(2):
                try:
                    # FIXED: Remove Accept-Encoding to avoid compression
                    headers = {
                        'User-Agent': random.choice(user_agents),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                        # REMOVED: 'Accept-Encoding': 'gzip, deflate, br'
                    }

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
                        content = response.text

                        # Quick validation
                        if len(content) > 100 and (
                                '<html' in content.lower() or '<title' in content.lower() or 'recipe' in content.lower()):
                            logger.info(f"Successfully fetched readable HTML from Food.com {url}")
                            return content[:150000]  # Limit size
                        else:
                            logger.warning(f"Food.com content still garbled: {content[:50]}")
                            continue

                    elif response.status_code == 403:
                        logger.warning(f"Food.com blocked request (403) for {url}")
                        continue
                    else:
                        logger.warning(f"Food.com HTTP {response.status_code} for {url}")

                except Exception as e:
                    logger.warning(f"Food.com request error (attempt {attempt + 1}): {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error fetching Food.com webpage {url}: {e}")
            return None

    def _scrape_and_parse_recipe(self, url: str, ingredient: str) -> Optional[Dict]:
        """Scrape a Food.com URL and parse it with specialized Food.com handling"""
        try:
            logger.info(f"Scraping Food.com recipe from: {url}")

            # Check cache first
            cached_recipe = recipe_cache.get(url)
            if cached_recipe:
                logger.info(f"Retrieved Food.com recipe from cache: {cached_recipe.get('name', 'Unknown')}")
                return cached_recipe

            page_content = self._fetch_webpage_content(url)
            if not page_content:
                return None

            # PRIORITY 1: Try structured data extraction (JSON-LD) with Food.com focus
            structured_data = self._extract_structured_recipe_data(page_content, url)
            if structured_data:
                logger.info(f"Successfully extracted Food.com structured data from {url}")
                structured_data['url'] = url
                structured_data['source'] = 'food.com'
                structured_data['extraction_method'] = 'structured_data'
                recipe_cache.set(url, structured_data)
                return structured_data

            # PRIORITY 2: Try enhanced HTML parsing
            enhanced_data = self._extract_recipe_with_enhanced_parsing(page_content, url, ingredient)
            if enhanced_data:
                logger.info(f"Successfully extracted Food.com recipe with enhanced parsing from {url}")
                enhanced_data['extraction_method'] = 'enhanced_parsing'
                recipe_cache.set(url, enhanced_data)
                return enhanced_data

            # PRIORITY 3: AI parsing as last resort
            ai_parsed_data = self._try_ai_parsing_with_limits(page_content, url, ingredient)
            if ai_parsed_data:
                logger.info(f"Successfully extracted Food.com recipe with AI from {url}")
                ai_parsed_data['extraction_method'] = 'ai_parsing'
                recipe_cache.set(url, ai_parsed_data)
                return ai_parsed_data

            # FALLBACK: Basic recipe creation
            logger.warning(f"All Food.com parsing methods failed for {url}, creating basic recipe")
            fallback_recipe = self._create_basic_recipe_from_page(page_content, url, ingredient)
            return fallback_recipe

        except Exception as e:
            logger.error(f"Error scraping Food.com recipe from {url}: {e}")
            return None

    def _extract_structured_recipe_data(self, html_content: str, url: str = "") -> Optional[Dict]:
        """Extract recipe data from JSON-LD structured data with Food.com-specific debugging"""
        try:
            if not BS4_AVAILABLE:
                logger.debug("BeautifulSoup not available for Food.com structured data extraction")
                return None

            soup = BeautifulSoup(html_content, 'html.parser')

            # Look for JSON-LD scripts
            json_scripts = []
            json_scripts.extend(soup.find_all('script', type='application/ld+json'))
            json_scripts.extend(soup.find_all('script', type='application/json+ld'))
            json_scripts.extend(soup.find_all('script', {'type': re.compile(r'ld\+json', re.I)}))

            # Also check for scripts that might not have proper type but contain recipe data
            all_scripts = soup.find_all('script')
            for script in all_scripts:
                if script.string and ('"@type"' in script.string and
                                      ('"Recipe"' in script.string or '"recipe"' in script.string)):
                    if script not in json_scripts:
                        json_scripts.append(script)

            logger.info(f"Found {len(json_scripts)} potential JSON-LD scripts for Food.com {url}")

            for i, script in enumerate(json_scripts):
                try:
                    if not script.string:
                        logger.debug(f"Food.com Script {i}: No content")
                        continue

                    json_str = script.string.strip()

                    # Clean up JSON string more aggressively
                    if json_str.startswith('<!--'):
                        json_str = json_str[4:]
                    if json_str.endswith('-->'):
                        json_str = json_str[:-3]

                    json_str = json_str.strip()

                    # Fix common JSON issues
                    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                    json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')

                    if not json_str or not (json_str.startswith('{') or json_str.startswith('[')):
                        logger.debug(f"Food.com Script {i}: Invalid JSON format")
                        continue

                    try:
                        data = json.loads(json_str)
                        logger.info(f"Food.com Script {i}: Successfully parsed JSON")
                    except json.JSONDecodeError as e:
                        logger.debug(f"Food.com Script {i}: JSON parse error: {e}")
                        continue

                    # Enhanced recipe search
                    recipe_data = self._find_recipe_in_data_enhanced(data, url)

                    if recipe_data:
                        logger.info(f"Food.com Script {i}: Found recipe data with keys: {list(recipe_data.keys())}")

                        # Debug key fields for Food.com
                        logger.info(f"Food.com recipe name: {recipe_data.get('name', 'NOT_FOUND')}")
                        logger.info(f"Food.com ingredients count: {len(recipe_data.get('recipeIngredient', []))}")
                        logger.info(f"Food.com instructions count: {len(recipe_data.get('recipeInstructions', []))}")

                        parsed = self._parse_recipe_schema(recipe_data)
                        if parsed:
                            logger.info(f"Food.com Script {i}: Successfully extracted and parsed recipe from JSON-LD")
                            return parsed
                        else:
                            logger.warning(f"Food.com Script {i}: Recipe data found but parsing failed")

                except Exception as e:
                    logger.warning(f"Food.com Script {i}: Unexpected error: {e}")
                    continue

            # If JSON-LD fails, try microdata
            logger.debug("Food.com JSON-LD extraction failed, trying microdata")
            return self._extract_microdata_recipe(soup)

        except Exception as e:
            logger.error(f"Error extracting Food.com structured data: {e}")
            return None

    def _find_recipe_in_data_enhanced(self, data, url="", depth=0) -> Optional[Dict]:
        """Enhanced recursive search for Recipe objects with Food.com-specific debugging"""
        if depth > 5:  # Prevent infinite recursion
            logger.debug(f"Food.com max recursion depth reached at level {depth}")
            return None

        debug_prefix = "  " * depth
        logger.debug(f"{debug_prefix}Food.com searching at depth {depth}, type: {type(data).__name__}")

        if isinstance(data, dict):
            # Check @type field with case-insensitive matching
            type_field = data.get('@type', '')
            if isinstance(type_field, str):
                if type_field.lower() in ['recipe', 'Recipe']:
                    logger.info(f"{debug_prefix}Found Food.com Recipe object with @type: {type_field}")
                    return data
            elif isinstance(type_field, list):
                for t in type_field:
                    if isinstance(t, str) and t.lower() in ['recipe', 'Recipe']:
                        logger.info(f"{debug_prefix}Found Food.com Recipe object in @type array: {t}")
                        return data

            # Check common nested locations first
            priority_keys = ['mainEntity', 'mainEntityOfPage', '@graph', 'itemListElement', 'about']
            for key in priority_keys:
                if key in data:
                    logger.debug(f"{debug_prefix}Checking Food.com priority key: {key}")
                    result = self._find_recipe_in_data_enhanced(data[key], url, depth + 1)
                    if result:
                        logger.info(f"{debug_prefix}Found Food.com Recipe in priority key: {key}")
                        return result

            # Check for Recipe-like content indicators
            recipe_indicators = ['recipeIngredient', 'recipeInstructions', 'recipeName', 'cookTime', 'prepTime']
            has_recipe_content = any(key in data for key in recipe_indicators)

            if has_recipe_content and not data.get('@type'):
                logger.info(
                    f"{debug_prefix}Found Food.com object with recipe content but no @type, treating as Recipe")
                return data

            # Deep search in all remaining values
            for key, value in data.items():
                if key not in priority_keys:  # Skip already checked priority keys
                    logger.debug(f"{debug_prefix}Checking Food.com key: {key}")
                    result = self._find_recipe_in_data_enhanced(value, url, depth + 1)
                    if result:
                        logger.info(f"{debug_prefix}Found Food.com Recipe in key: {key}")
                        return result

        elif isinstance(data, list):
            logger.debug(f"{debug_prefix}Searching Food.com list with {len(data)} items")
            for i, item in enumerate(data):
                logger.debug(f"{debug_prefix}Checking Food.com list item {i}")
                result = self._find_recipe_in_data_enhanced(item, url, depth + 1)
                if result:
                    logger.info(f"{debug_prefix}Found Food.com Recipe in list item {i}")
                    return result

        logger.debug(f"{debug_prefix}No Food.com Recipe found at this level")
        return None

    def _parse_recipe_schema(self, schema_data: Dict) -> Optional[Dict]:
        """Parse Recipe schema data with enhanced Food.com support and better error handling"""
        try:
            recipe = {
                'name': '',
                'description': '',
                'ingredients': [],
                'instructions': [],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': [],
                'dietary_restrictions': []
            }

            # Extract name with multiple fallbacks
            name_candidates = [
                schema_data.get('name', ''),
                schema_data.get('headline', ''),
                schema_data.get('title', ''),
                schema_data.get('recipeName', '')
            ]

            for name_candidate in name_candidates:
                name = self._extract_text_value(name_candidate)
                if name and len(name.strip()) > 2:
                    recipe['name'] = name.strip()
                    break

            logger.debug(f"Extracted Food.com recipe name: '{recipe['name']}'")

            # Extract description with multiple fallbacks
            desc_candidates = [
                schema_data.get('description', ''),
                schema_data.get('summary', ''),
                schema_data.get('recipeDescription', '')
            ]

            for desc_candidate in desc_candidates:
                desc = self._extract_text_value(desc_candidate)
                if desc and len(desc.strip()) > 5:
                    recipe['description'] = desc.strip()
                    break

            # Extract ingredients with enhanced handling
            ingredient_candidates = [
                schema_data.get('recipeIngredient', []),
                schema_data.get('ingredients', []),
                schema_data.get('ingredient', [])
            ]

            for ingredients_data in ingredient_candidates:
                if not ingredients_data:
                    continue

                if isinstance(ingredients_data, list) and len(ingredients_data) > 0:
                    logger.debug(f"Processing {len(ingredients_data)} Food.com ingredients")

                    for i, ing_item in enumerate(ingredients_data):
                        ing_text = self._extract_text_value(ing_item)
                        if ing_text and len(ing_text.strip()) > 1:
                            parsed_ing = self._parse_ingredient_text(ing_text.strip())
                            if parsed_ing:
                                recipe['ingredients'].append(parsed_ing)

                    if recipe['ingredients']:  # Found valid ingredients, stop searching
                        break

            logger.debug(f"Total Food.com ingredients extracted: {len(recipe['ingredients'])}")

            # Extract instructions with enhanced handling
            instruction_candidates = [
                schema_data.get('recipeInstructions', []),
                schema_data.get('instructions', []),
                schema_data.get('instruction', []),
                schema_data.get('recipeDirection', []),
                schema_data.get('directions', [])
            ]

            for instructions_data in instruction_candidates:
                if not instructions_data:
                    continue

                if isinstance(instructions_data, list) and len(instructions_data) > 0:
                    logger.debug(f"Processing {len(instructions_data)} Food.com instructions")

                    for i, inst_item in enumerate(instructions_data):
                        inst_text = self._extract_instruction_text(inst_item)
                        if inst_text and len(inst_text.strip()) > 5:
                            cleaned_text = re.sub(r'^\d+\.\s*', '', inst_text.strip())
                            recipe['instructions'].append(cleaned_text)

                    if recipe['instructions']:  # Found valid instructions, stop searching
                        break

            logger.debug(f"Total Food.com instructions extracted: {len(recipe['instructions'])}")

            # Validate recipe
            has_name = bool(recipe['name'] and len(recipe['name']) > 2)
            has_ingredients = len(recipe['ingredients']) >= 1
            has_instructions = len(recipe['instructions']) >= 1

            logger.info(f"Food.com recipe validation:")
            logger.info(f"  Name: {has_name} ('{recipe['name']}')")
            logger.info(f"  Ingredients: {has_ingredients} ({len(recipe['ingredients'])} found)")
            logger.info(f"  Instructions: {has_instructions} ({len(recipe['instructions'])} found)")

            if has_name and has_ingredients and has_instructions:
                logger.info(f"Successfully parsed Food.com recipe: {recipe['name']}")
                return recipe
            else:
                logger.warning("Incomplete Food.com recipe data - rejecting")
                return None

        except Exception as e:
            logger.error(f"Error parsing Food.com recipe schema: {e}")
            return None

    def _extract_text_value(self, value) -> str:
        """Extract text from various JSON-LD value formats"""
        try:
            if value is None:
                return ''
            elif isinstance(value, str):
                return value.strip()
            elif isinstance(value, dict):
                text_candidates = [
                    value.get('@value', ''),
                    value.get('text', ''),
                    value.get('#text', ''),
                    value.get('name', ''),
                    value.get('value', '')
                ]

                for candidate in text_candidates:
                    if candidate and isinstance(candidate, str):
                        return candidate.strip()

                return str(value).strip()

            elif isinstance(value, list) and len(value) > 0:
                for item in value:
                    result = self._extract_text_value(item)
                    if result:
                        return result
                return ''
            else:
                return str(value).strip() if value else ''
        except Exception as e:
            logger.debug(f"Error extracting text value from {type(value)}: {e}")
            return ''

    def _extract_instruction_text(self, inst_item) -> str:
        """Extract instruction text from HowToStep or other formats"""
        try:
            if inst_item is None:
                return ''
            elif isinstance(inst_item, str):
                return inst_item.strip()
            elif isinstance(inst_item, dict):
                text_candidates = [
                    inst_item.get('text', ''),
                    inst_item.get('name', ''),
                    inst_item.get('@value', ''),
                    inst_item.get('description', ''),
                    inst_item.get('#text', ''),
                    inst_item.get('instruction', ''),
                    inst_item.get('step', ''),
                    inst_item.get('direction', '')
                ]

                for candidate in text_candidates:
                    if candidate and isinstance(candidate, str):
                        return candidate.strip()

                return str(inst_item).strip()
            else:
                return str(inst_item).strip() if inst_item else ''
        except Exception as e:
            logger.debug(f"Error extracting instruction text from {type(inst_item)}: {e}")
            return ''

    def _extract_recipe_with_enhanced_parsing(self, html_content: str, url: str, ingredient: str) -> Optional[Dict]:
        """Enhanced HTML parsing to extract Food.com recipe data without AI"""
        try:
            if not BS4_AVAILABLE:
                return None

            soup = BeautifulSoup(html_content, 'html.parser')

            # Look for common recipe container patterns
            recipe_containers = soup.find_all(['div', 'section', 'article'],
                                              class_=re.compile(r'recipe|Recipe|RECIPE', re.I))

            if not recipe_containers:
                recipe_containers = soup.find_all(['div', 'section', 'article'],
                                                  attrs={'itemtype': re.compile(r'Recipe', re.I)})

            if not recipe_containers:
                return None

            recipe_data = {
                'name': '',
                'description': '',
                'ingredients': [],
                'instructions': [],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': [],
                'dietary_restrictions': [],
                'url': url,
                'source': 'food.com'
            }

            # Extract title
            title_selectors = [
                'h1.recipe-title', 'h1[itemprop="name"]', 'h1.recipe-name',
                '.recipe-title', '.recipe-name', 'h1', 'title'
            ]

            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    recipe_data['name'] = title_elem.get_text().strip()
                    break

            # Extract ingredients
            ingredient_selectors = [
                '[itemprop="recipeIngredient"]',
                '.recipe-ingredient', '.ingredient', '.ingredients li',
                'ul.ingredients li', '.ingredient-list li'
            ]

            for selector in ingredient_selectors:
                ingredients = soup.select(selector)
                if ingredients:
                    for ing in ingredients:
                        ingredient_text = ing.get_text().strip()
                        if ingredient_text and len(ingredient_text) > 2:
                            parsed_ing = self._parse_ingredient_text(ingredient_text)
                            if parsed_ing:
                                recipe_data['ingredients'].append(parsed_ing)
                    if recipe_data['ingredients']:
                        break

            # Extract instructions
            instruction_selectors = [
                '[itemprop="recipeInstructions"]',
                '.recipe-instruction', '.instruction', '.instructions li',
                'ol.instructions li', '.instruction-list li', '.directions li'
            ]

            for selector in instruction_selectors:
                instructions = soup.select(selector)
                if instructions:
                    for inst in instructions:
                        instruction_text = inst.get_text().strip()
                        if instruction_text and len(instruction_text) > 5:
                            recipe_data['instructions'].append(instruction_text)
                    if recipe_data['instructions']:
                        break

            # Only return if we got meaningful data
            if (recipe_data['name'] and
                    len(recipe_data['ingredients']) >= 2 and
                    len(recipe_data['instructions']) >= 1):
                return recipe_data

            return None

        except Exception as e:
            logger.error(f"Error in Food.com enhanced parsing: {e}")
            return None

    def _extract_microdata_recipe(self, soup) -> Optional[Dict]:
        """Extract Food.com recipe data from microdata attributes"""
        try:
            recipe_containers = soup.find_all(attrs={'itemtype': re.compile(r'Recipe', re.I)})

            if not recipe_containers:
                return None

            container = recipe_containers[0]

            recipe = {
                'name': '',
                'description': '',
                'ingredients': [],
                'instructions': [],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': [],
                'dietary_restrictions': []
            }

            # Extract name
            name_elem = container.find(attrs={'itemprop': 'name'})
            if name_elem:
                recipe['name'] = name_elem.get_text().strip()

            # Extract description
            desc_elem = container.find(attrs={'itemprop': 'description'})
            if desc_elem:
                recipe['description'] = desc_elem.get_text().strip()

            # Extract ingredients
            ingredient_elems = container.find_all(attrs={'itemprop': 'recipeIngredient'})
            for ing_elem in ingredient_elems:
                ingredient_text = ing_elem.get_text().strip()
                if ingredient_text:
                    parsed_ing = self._parse_ingredient_text(ingredient_text)
                    if parsed_ing:
                        recipe['ingredients'].append(parsed_ing)

            # Extract instructions
            instruction_elems = container.find_all(attrs={'itemprop': 'recipeInstructions'})
            for inst_elem in instruction_elems:
                instruction_text = inst_elem.get_text().strip()
                if instruction_text:
                    recipe['instructions'].append(instruction_text)

            # Only return if we got meaningful data
            if (recipe['name'] and
                    len(recipe['ingredients']) >= 2 and
                    len(recipe['instructions']) >= 1):
                logger.info("Successfully extracted Food.com recipe from microdata")
                return recipe

            return None

        except Exception as e:
            logger.error(f"Error extracting Food.com microdata: {e}")
            return None

    def _try_ai_parsing_with_limits(self, page_content: str, url: str, ingredient: str) -> Optional[Dict]:
        """Try AI parsing with strict limits - LAST RESORT ONLY for Food.com"""
        try:
            import time
            start_time = time.time()

            logger.warning(f"Falling back to AI parsing for Food.com {url} - structured data extraction failed!")

            from ..utils.ai_helper import ai_helper

            if not ai_helper or not ai_helper.is_configured():
                logger.info("AI helper not configured, skipping Food.com AI parsing")
                return None

            clean_text = self._extract_clean_recipe_text(page_content)
            if not clean_text or len(clean_text) < 100:
                logger.debug("Insufficient clean text for Food.com AI parsing")
                return None

            max_ai_content = 2500
            if len(clean_text) > max_ai_content:
                clean_text = clean_text[:max_ai_content] + "..."

            if time.time() - start_time > 3:
                logger.warning(f"Skipping AI parsing for Food.com {url} due to timeout")
                return None

            try:
                response = ai_helper.client.chat.completions.create(
                    model=ai_helper.model,
                    messages=[
                        {"role": "system", "content": """Extract recipe information from Food.com webpage content and return as JSON.
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
                        {"role": "user", "content": f"Extract Food.com recipe from: {clean_text}"}
                    ],
                    max_tokens=600,
                    temperature=0.0,
                    timeout=8
                )

                result_text = response.choices[0].message.content.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]

                parsed_recipe = json.loads(result_text)

                if parsed_recipe and parsed_recipe.get('name'):
                    parsed_recipe['url'] = url
                    parsed_recipe['source'] = 'food.com'
                    logger.info(f"Food.com AI parsing successful for {url}: {parsed_recipe.get('name')}")
                    return parsed_recipe

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing Food.com AI response for {url}: {e}")
            except Exception as e:
                logger.warning(f"Food.com AI parsing timeout or error for {url}: {e}")

            return None

        except ImportError:
            logger.info("AI Helper not available for Food.com recipe parsing")
            return None
        except Exception as e:
            logger.error(f"Error in Food.com AI parsing attempt: {e}")
            return None

    def _extract_clean_recipe_text(self, html_content: str) -> str:
        """Extract clean text content focusing on Food.com recipe-relevant sections"""
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
            logger.error(f"Error extracting clean text from Food.com: {e}")
            return ""

    def _create_basic_recipe_from_page(self, html_content: str, url: str, ingredient: str) -> Dict:
        """Create a basic Food.com recipe when structured data isn't available"""
        try:
            title = "Food.com Recipe"
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    title = re.sub(r'\s*\|\s*.*$', '', title)
                    title = re.sub(r'\s*-\s*.*$', '', title)

            genre = 'dinner'
            if any(word in title.lower() for word in ['cookie', 'cake', 'dessert', 'sweet']):
                genre = 'dessert'
            elif any(word in title.lower() for word in ['breakfast', 'pancake', 'cereal']):
                genre = 'breakfast'
            elif any(word in title.lower() for word in ['lunch', 'sandwich', 'salad']):
                genre = 'lunch'

            return {
                'name': title if title != "Food.com Recipe" else f"Food.com {ingredient.title()} Recipe",
                'description': f'Recipe found on Food.com. Visit the original page for complete details.',
                'ingredients': [
                    {'name': f'{ingredient} (see original Food.com recipe for details)', 'quantity': 1,
                     'unit': 'recipe'}
                ],
                'instructions': [
                    f'This Food.com recipe requires visiting the original page at {url} for complete instructions.',
                    'The structured data could not be extracted automatically from Food.com.'
                ],
                'serving_size': 4,
                'prep_time': 15,
                'cook_time': 30,
                'genre': genre,
                'notes': [f'Original recipe from Food.com', 'Automatic extraction failed - manual review needed'],
                'dietary_restrictions': [],
                'url': url,
                'source': 'food.com',
                'extraction_method': 'basic_fallback'
            }

        except Exception as e:
            logger.error(f"Error creating basic Food.com recipe: {e}")
            return {
                'name': f"Food.com {ingredient.title()} Recipe",
                'description': 'Food.com recipe extraction failed',
                'ingredients': [{'name': ingredient, 'quantity': 1, 'unit': 'recipe'}],
                'instructions': [f'Visit {url} for the complete Food.com recipe'],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': ['Food.com extraction failed'],
                'dietary_restrictions': [],
                'url': url,
                'source': 'food.com',
                'extraction_method': 'minimal_fallback'
            }

    def _parse_ingredient_text(self, text: str) -> Optional[Dict]:
        """Parse Food.com ingredient text into quantity, unit, name"""
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
            logger.error(f"Error parsing Food.com ingredient text '{text}': {e}")
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
            logger.error(f"Error parsing Food.com duration '{duration_str}': {e}")
            return 0

    def _generate_fallback_recipes(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Generate fallback recipes when Food.com search fails"""
        return [{
            "name": f"Food.com Style {ingredient.title()}",
            "source": "food.com",
            "description": f"A {ingredient} recipe in the style of Food.com. (Unable to fetch live data)",
            "url": f"https://www.food.com/search?q={ingredient.replace(' ', '+')}",
            "ingredients": [
                {"name": ingredient.split()[0] if ingredient != 'recipe' else 'main ingredient', "quantity": 2,
                 "unit": "cups"},
                {"name": "additional ingredients", "quantity": 1, "unit": "cup"}
            ],
            "instructions": [
                f"Follow Food.com's typical preparation method",
                "Cook according to your preference"
            ],
            "serving_size": criteria.get('serving_size', 4),
            "prep_time": 15,
            "cook_time": 25,
            "genre": criteria.get('genre', 'dinner'),
            "notes": [f"Please visit Food.com directly for the most current recipes"],
            "dietary_restrictions": [],
            "cuisine_type": "general"
        }]


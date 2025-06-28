from .base_imports import *
from .recipe_cache import recipe_cache


class AllRecipesComSearchTool:
    """Specialized tool for searching AllRecipes.com"""

    def __init__(self):
        self.name = "allrecipes_search"
        self.description = "Search AllRecipes.com for recipes"
        self.website = "allrecipes.com"

    def search_recipes(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Search AllRecipes.com for recipes with enhanced error handling"""
        try:
            logger.info(f"Searching AllRecipes.com for recipes about: {ingredient}")

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
                    logger.warning(f"Search timeout reached for AllRecipes.com")
                    break

                logger.info(f"Trying to access AllRecipes URL: {search_url}")

                try:
                    search_page_content = self._fetch_webpage_content(search_url)
                except Exception as fetch_error:
                    logger.error(f"Error fetching AllRecipes {search_url}: {fetch_error}")
                    continue

                if not search_page_content:
                    logger.warning(f"Failed to get content from AllRecipes {search_url}")
                    continue

                logger.info(f"Successfully got {len(search_page_content)} characters from AllRecipes {search_url}")

                # Check if we got a valid page
                content_lower = search_page_content.lower()
                if (("page not found" in content_lower or
                     "404 error" in content_lower or
                     "not found" in content_lower[:1000]) and
                        "recipe" not in content_lower[:5000]):
                    logger.warning(f"Got error page from AllRecipes {search_url}")
                    continue

                try:
                    recipe_urls = self._extract_recipe_urls_from_search(search_page_content)
                except Exception as extract_error:
                    logger.error(f"Error extracting recipe URLs from AllRecipes {search_url}: {extract_error}")
                    continue

                logger.info(f"Extracted {len(recipe_urls)} recipe URLs from AllRecipes search results")

                if recipe_urls:
                    logger.info(f"Sample AllRecipes recipe URLs: {recipe_urls[:3]}")
                else:
                    logger.warning(f"No AllRecipes recipe URLs found. Page title area: {search_page_content[:500]}")

                recipe_process_start = time.time()
                recipes_processed = 0

                for recipe_url in recipe_urls[:2]:
                    if len(all_recipes) >= max_recipes:
                        break

                    if time.time() - recipe_process_start > 8 * (recipes_processed + 1):
                        logger.warning(f"AllRecipes recipe processing timeout for {recipe_url}")
                        break

                    if time.time() - start_time > timeout_seconds:
                        logger.warning(f"AllRecipes overall timeout reached, stopping recipe processing")
                        break

                    logger.info(f"Attempting to scrape AllRecipes recipe from: {recipe_url}")

                    try:
                        recipe_data = self._scrape_and_parse_recipe(recipe_url, ingredient)
                        recipes_processed += 1

                        if recipe_data and isinstance(recipe_data, dict):
                            all_recipes.append(recipe_data)
                            logger.info(f"Successfully parsed AllRecipes recipe: {recipe_data.get('name', 'Unknown')}")
                        else:
                            logger.warning(f"Failed to parse AllRecipes recipe from: {recipe_url}")
                    except Exception as recipe_error:
                        logger.error(f"Error processing AllRecipes recipe {recipe_url}: {recipe_error}")
                        recipes_processed += 1
                        continue

            total_time = time.time() - start_time
            logger.info(f"AllRecipes search completed in {total_time:.2f} seconds, found {len(all_recipes)} recipes")

            if all_recipes:
                logger.info(f"Found {len(all_recipes)} real recipes from AllRecipes.com")
                return all_recipes
            else:
                logger.warning(f"Could not parse any real recipes from AllRecipes.com, using fallback")
                fallback_recipes = self._generate_fallback_recipes(ingredient, criteria)
                return fallback_recipes if fallback_recipes else []

        except Exception as e:
            logger.error(f"Error searching AllRecipes.com: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                fallback_recipes = self._generate_fallback_recipes(ingredient, criteria)
                return fallback_recipes if fallback_recipes else []
            except:
                return []

    def _build_search_urls(self, ingredient: str) -> List[str]:
        """Build AllRecipes.com search URLs"""
        search_urls = []
        import urllib.parse
        encoded_ingredient = urllib.parse.quote_plus(ingredient)

        search_urls.append(f"https://www.allrecipes.com/search?q={encoded_ingredient}")
        return search_urls

    def _extract_recipe_urls_from_search(self, html_content: str) -> List[str]:
        """Extract recipe URLs from AllRecipes.com search results page"""
        try:
            recipe_urls = []

            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link.get('href', '')
                    if '/recipe/' in href and href.count('/') >= 3:
                        if href.startswith('http'):
                            recipe_urls.append(href)
                        elif href.startswith('/'):
                            recipe_urls.append(f"https://www.allrecipes.com{href}")

            # Remove duplicates and filter valid URLs
            unique_urls = []
            seen = set()
            for url in recipe_urls:
                url = url.split('?')[0].split('#')[0]  # Remove query params and fragments
                if (url not in seen and len(url) > 20 and
                        not url.endswith(('.css', '.js', '.png', '.jpg'))):
                    seen.add(url)
                    unique_urls.append(url)

            unique_urls = unique_urls[:10]
            logger.info(f"Extracted {len(unique_urls)} unique AllRecipes recipe URLs")
            return unique_urls

        except Exception as e:
            logger.error(f"Error extracting AllRecipes recipe URLs: {e}")
            return []

    def _fetch_webpage_content(self, url: str) -> Optional[str]:
        """Fetch webpage content with optimized size limits and timeout controls"""
        try:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
            ]

            import random

            for attempt in range(2):
                try:
                    headers = {
                        'User-Agent': random.choice(user_agents),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'max-age=0',
                    }

                    if attempt > 0:
                        import time
                        time.sleep(0.5)

                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=15,
                        allow_redirects=True,
                        verify=True,
                        stream=True
                    )

                    response.raw.decode_content = True

                    if response.status_code == 200:
                        content = ""
                        max_size = 300000
                        current_size = 0

                        try:
                            encoding = response.encoding or 'utf-8'
                            if encoding.lower() in ['iso-8859-1', 'ascii'] and 'charset=' not in response.headers.get(
                                    'content-type', '').lower():
                                encoding = 'utf-8'

                            for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                                if chunk:
                                    try:
                                        chunk_str = chunk.decode(encoding, errors='ignore')
                                        chunk_size = len(chunk_str.encode('utf-8'))

                                        if current_size + chunk_size > max_size:
                                            logger.info(
                                                f"Content size limit reached for AllRecipes {url}, truncating at {current_size} bytes")
                                            break

                                        content += chunk_str
                                        current_size += chunk_size
                                    except UnicodeDecodeError:
                                        try:
                                            chunk_str = chunk.decode('utf-8', errors='ignore')
                                            content += chunk_str
                                            current_size += len(chunk_str.encode('utf-8'))
                                        except:
                                            continue

                        except Exception as e:
                            logger.warning(f"Error reading content chunks from AllRecipes {url}: {e}")
                            try:
                                full_text = response.text
                                if len(full_text.encode('utf-8')) <= max_size:
                                    content = full_text
                                else:
                                    content = full_text[:max_size // 2]
                                    logger.info(f"AllRecipes content truncated to ~{max_size // 2} chars for {url}")
                            except Exception as e2:
                                logger.error(f"Failed to read AllRecipes response text: {e2}")
                                return None
                        finally:
                            response.close()

                        logger.info(
                            f"Successfully fetched {len(content)} chars from AllRecipes {url} (attempt {attempt + 1})")
                        return content

                    elif response.status_code == 403:
                        logger.warning(f"Access forbidden (403) for AllRecipes {url} - trying different User-Agent")
                        response.close()
                        continue
                    elif response.status_code == 404:
                        logger.warning(f"AllRecipes page not found (404) for {url}")
                        response.close()
                        return None
                    else:
                        logger.warning(f"AllRecipes HTTP {response.status_code} for {url} (attempt {attempt + 1})")
                        response.close()

                except requests.exceptions.Timeout as e:
                    logger.warning(f"Timeout for AllRecipes {url} (attempt {attempt + 1}): {e}")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"AllRecipes request failed for {url} (attempt {attempt + 1}): {e}")
                    continue

            logger.error(f"All attempts failed for AllRecipes {url}")
            return None

        except Exception as e:
            logger.error(f"Error fetching AllRecipes webpage {url}: {e}")
            return None

    def _scrape_and_parse_recipe(self, url: str, ingredient: str) -> Optional[Dict]:
        """Scrape an AllRecipes URL and parse it with specialized AllRecipes handling"""
        try:
            logger.info(f"Scraping AllRecipes recipe from: {url}")

            # Check cache first
            cached_recipe = recipe_cache.get(url)
            if cached_recipe:
                logger.info(f"Retrieved AllRecipes recipe from cache: {cached_recipe.get('name', 'Unknown')}")
                return cached_recipe

            page_content = self._fetch_webpage_content(url)
            if not page_content:
                return None

            # PRIORITY 1: Try structured data extraction (JSON-LD) with AllRecipes focus
            structured_data = self._extract_structured_recipe_data(page_content, url)
            if structured_data:
                logger.info(f"Successfully extracted AllRecipes structured data from {url}")
                structured_data['url'] = url
                structured_data['source'] = 'allrecipes.com'
                structured_data['extraction_method'] = 'structured_data'
                recipe_cache.set(url, structured_data)
                return structured_data

            # PRIORITY 2: Try enhanced HTML parsing
            enhanced_data = self._extract_recipe_with_enhanced_parsing(page_content, url, ingredient)
            if enhanced_data:
                logger.info(f"Successfully extracted AllRecipes recipe with enhanced parsing from {url}")
                enhanced_data['extraction_method'] = 'enhanced_parsing'
                recipe_cache.set(url, enhanced_data)
                return enhanced_data

            # PRIORITY 3: AI parsing as last resort
            ai_parsed_data = self._try_ai_parsing_with_limits(page_content, url, ingredient)
            if ai_parsed_data:
                logger.info(f"Successfully extracted AllRecipes recipe with AI from {url}")
                ai_parsed_data['extraction_method'] = 'ai_parsing'
                recipe_cache.set(url, ai_parsed_data)
                return ai_parsed_data

            # FALLBACK: Basic recipe creation
            logger.warning(f"All AllRecipes parsing methods failed for {url}, creating basic recipe")
            fallback_recipe = self._create_basic_recipe_from_page(page_content, url, ingredient)
            return fallback_recipe

        except Exception as e:
            logger.error(f"Error scraping AllRecipes recipe from {url}: {e}")
            return None

    def _extract_structured_recipe_data(self, html_content: str, url: str = "") -> Optional[Dict]:
        """Extract recipe data from JSON-LD structured data with AllRecipes-specific debugging"""
        try:
            if not BS4_AVAILABLE:
                logger.debug("BeautifulSoup not available for AllRecipes structured data extraction")
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

            logger.info(f"Found {len(json_scripts)} potential JSON-LD scripts for AllRecipes {url}")

            for i, script in enumerate(json_scripts):
                try:
                    if not script.string:
                        logger.debug(f"AllRecipes Script {i}: No content")
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
                        logger.debug(f"AllRecipes Script {i}: Invalid JSON format")
                        continue

                    try:
                        data = json.loads(json_str)
                        logger.info(f"AllRecipes Script {i}: Successfully parsed JSON")
                    except json.JSONDecodeError as e:
                        logger.debug(f"AllRecipes Script {i}: JSON parse error: {e}")
                        continue

                    # Comprehensive debugging for AllRecipes
                    logger.info(f"AllRecipes Script {i} analysis:")
                    logger.info(f"  Type: {type(data).__name__}")
                    if isinstance(data, dict):
                        logger.info(f"  Root keys: {list(data.keys())}")
                        logger.info(f"  @type: {data.get('@type', 'MISSING')}")
                        logger.info(f"  @context: {data.get('@context', 'MISSING')}")
                    elif isinstance(data, list):
                        logger.info(f"  Array length: {len(data)}")
                        if data and isinstance(data[0], dict):
                            logger.info(f"  First item keys: {list(data[0].keys())}")
                            logger.info(f"  First item @type: {data[0].get('@type', 'MISSING')}")

                    # Enhanced recipe search
                    recipe_data = self._find_recipe_in_data_enhanced(data, url)

                    if recipe_data:
                        logger.info(f"AllRecipes Script {i}: Found recipe data with keys: {list(recipe_data.keys())}")

                        # Debug key fields for AllRecipes
                        logger.info(f"AllRecipes recipe name: {recipe_data.get('name', 'NOT_FOUND')}")
                        logger.info(f"AllRecipes ingredients count: {len(recipe_data.get('recipeIngredient', []))}")
                        logger.info(f"AllRecipes instructions count: {len(recipe_data.get('recipeInstructions', []))}")

                        parsed = self._parse_recipe_schema(recipe_data)
                        if parsed:
                            logger.info(f"AllRecipes Script {i}: Successfully extracted and parsed recipe from JSON-LD")
                            return parsed
                        else:
                            logger.warning(f"AllRecipes Script {i}: Recipe data found but parsing failed")
                            # Log why parsing failed
                            logger.info(f"AllRecipes parsing failure details:")
                            logger.info(f"  Raw recipe data keys: {list(recipe_data.keys())}")
                            logger.info(f"  Name field: {recipe_data.get('name', 'MISSING')}")
                            logger.info(f"  Ingredients field: {recipe_data.get('recipeIngredient', 'MISSING')}")
                            logger.info(f"  Instructions field: {recipe_data.get('recipeInstructions', 'MISSING')}")

                except Exception as e:
                    logger.warning(f"AllRecipes Script {i}: Unexpected error: {e}")
                    continue

            # If JSON-LD fails, try microdata
            logger.debug("AllRecipes JSON-LD extraction failed, trying microdata")
            return self._extract_microdata_recipe(soup)

        except Exception as e:
            logger.error(f"Error extracting AllRecipes structured data: {e}")
            return None

    def _find_recipe_in_data_enhanced(self, data, url="", depth=0) -> Optional[Dict]:
        """Enhanced recursive search for Recipe objects with AllRecipes-specific debugging"""
        if depth > 5:  # Prevent infinite recursion
            logger.debug(f"AllRecipes max recursion depth reached at level {depth}")
            return None

        debug_prefix = "  " * depth
        logger.debug(f"{debug_prefix}AllRecipes searching at depth {depth}, type: {type(data).__name__}")

        if isinstance(data, dict):
            # Check @type field with case-insensitive matching
            type_field = data.get('@type', '')
            if isinstance(type_field, str):
                if type_field.lower() in ['recipe', 'Recipe']:
                    logger.info(f"{debug_prefix}Found AllRecipes Recipe object with @type: {type_field}")
                    return data
            elif isinstance(type_field, list):
                for t in type_field:
                    if isinstance(t, str) and t.lower() in ['recipe', 'Recipe']:
                        logger.info(f"{debug_prefix}Found AllRecipes Recipe object in @type array: {t}")
                        return data

            # Log structure for AllRecipes debugging
            if depth == 0:
                logger.info(f"{debug_prefix}AllRecipes root structure:")
                logger.info(f"{debug_prefix}  Keys: {list(data.keys())}")
                logger.info(f"{debug_prefix}  @type: {data.get('@type', 'MISSING')}")
                logger.info(f"{debug_prefix}  @context: {data.get('@context', 'MISSING')}")

            # Check common nested locations first
            priority_keys = ['mainEntity', 'mainEntityOfPage', '@graph', 'itemListElement', 'about']
            for key in priority_keys:
                if key in data:
                    logger.debug(f"{debug_prefix}Checking AllRecipes priority key: {key}")
                    result = self._find_recipe_in_data_enhanced(data[key], url, depth + 1)
                    if result:
                        logger.info(f"{debug_prefix}Found AllRecipes Recipe in priority key: {key}")
                        return result

            # Check for Recipe-like content indicators
            recipe_indicators = ['recipeIngredient', 'recipeInstructions', 'recipeName', 'cookTime', 'prepTime']
            has_recipe_content = any(key in data for key in recipe_indicators)

            if has_recipe_content and not data.get('@type'):
                logger.info(
                    f"{debug_prefix}Found AllRecipes object with recipe content but no @type, treating as Recipe")
                logger.info(
                    f"{debug_prefix}  Recipe indicators found: {[key for key in recipe_indicators if key in data]}")
                return data

            # Deep search in all remaining values
            for key, value in data.items():
                if key not in priority_keys:  # Skip already checked priority keys
                    logger.debug(f"{debug_prefix}Checking AllRecipes key: {key}")
                    result = self._find_recipe_in_data_enhanced(value, url, depth + 1)
                    if result:
                        logger.info(f"{debug_prefix}Found AllRecipes Recipe in key: {key}")
                        return result

        elif isinstance(data, list):
            logger.debug(f"{debug_prefix}Searching AllRecipes list with {len(data)} items")
            for i, item in enumerate(data):
                logger.debug(f"{debug_prefix}Checking AllRecipes list item {i}")
                result = self._find_recipe_in_data_enhanced(item, url, depth + 1)
                if result:
                    logger.info(f"{debug_prefix}Found AllRecipes Recipe in list item {i}")
                    return result

        logger.debug(f"{debug_prefix}No AllRecipes Recipe found at this level")
        return None

    def _parse_recipe_schema(self, schema_data: Dict) -> Optional[Dict]:
        """Parse Recipe schema data with enhanced AllRecipes support and better error handling"""
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

            logger.debug(f"Extracted AllRecipes recipe name: '{recipe['name']}'")

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

                # Handle different ingredient formats
                if isinstance(ingredients_data, dict):
                    ingredients_data = ingredients_data.get('ingredients', [])

                if isinstance(ingredients_data, list) and len(ingredients_data) > 0:
                    logger.debug(f"Processing {len(ingredients_data)} AllRecipes ingredients")

                    for i, ing_item in enumerate(ingredients_data):
                        ing_text = self._extract_text_value(ing_item)
                        if ing_text and len(ing_text.strip()) > 1:
                            parsed_ing = self._parse_ingredient_text(ing_text.strip())
                            if parsed_ing:
                                recipe['ingredients'].append(parsed_ing)

                    if recipe['ingredients']:  # Found valid ingredients, stop searching
                        break

            logger.debug(f"Total AllRecipes ingredients extracted: {len(recipe['ingredients'])}")

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

                # Handle different instruction formats
                if isinstance(instructions_data, dict):
                    instructions_data = instructions_data.get('instructions', [])

                if isinstance(instructions_data, list) and len(instructions_data) > 0:
                    logger.debug(f"Processing {len(instructions_data)} AllRecipes instructions")

                    for i, inst_item in enumerate(instructions_data):
                        inst_text = self._extract_instruction_text(inst_item)
                        if inst_text and len(inst_text.strip()) > 5:
                            cleaned_text = re.sub(r'^\d+\.\s*', '', inst_text.strip())
                            recipe['instructions'].append(cleaned_text)

                    if recipe['instructions']:  # Found valid instructions, stop searching
                        break

                elif isinstance(instructions_data, str) and len(instructions_data.strip()) > 5:
                    recipe['instructions'].append(instructions_data.strip())
                    break

            logger.debug(f"Total AllRecipes instructions extracted: {len(recipe['instructions'])}")

            # Extract times with multiple candidates
            time_candidates = [
                ('prepTime', 'preparationTime', 'prep_time'),
                ('cookTime', 'cookingTime', 'cook_time'),
                ('totalTime', '', 'total_time')  # Fixed: added empty string as second element
            ]

            for primary, secondary, result_key in time_candidates:
                time_value = schema_data.get(primary, '') or schema_data.get(secondary, '')
                if time_value:
                    if result_key == 'prep_time':
                        recipe['prep_time'] = self._parse_iso_duration(time_value)
                    elif result_key == 'cook_time':
                        recipe['cook_time'] = self._parse_iso_duration(time_value)
                    elif result_key == 'total_time' and not recipe['prep_time'] and not recipe['cook_time']:
                        # Split total time if individual times aren't available
                        total_minutes = self._parse_iso_duration(time_value)
                        recipe['prep_time'] = max(1, total_minutes // 3)
                        recipe['cook_time'] = max(1, (total_minutes * 2) // 3)

            # Extract yield/serving size with multiple candidates
            yield_candidates = [
                schema_data.get('recipeYield'),
                schema_data.get('yield'),
                schema_data.get('servings'),
                schema_data.get('numberOfServings'),
                schema_data.get('serves')
            ]

            for recipe_yield in yield_candidates:
                if recipe_yield:
                    serving_size = self._extract_serving_size(recipe_yield)
                    if serving_size:
                        recipe['serving_size'] = serving_size
                        break

            # Extract category/genre with multiple candidates
            category_candidates = [
                schema_data.get('recipeCategory'),
                schema_data.get('category'),
                schema_data.get('cuisine'),
                schema_data.get('recipeCuisine'),
                schema_data.get('courseType')
            ]

            for category in category_candidates:
                if category:
                    recipe['genre'] = self._determine_genre(category)
                    break

            # Validate recipe with detailed logging
            has_name = bool(recipe['name'] and len(recipe['name']) > 2)
            has_ingredients = len(recipe['ingredients']) >= 1
            has_instructions = len(recipe['instructions']) >= 1

            logger.info(f"AllRecipes recipe validation:")
            logger.info(f"  Name: {has_name} ('{recipe['name']}')")
            logger.info(f"  Ingredients: {has_ingredients} ({len(recipe['ingredients'])} found)")
            logger.info(f"  Instructions: {has_instructions} ({len(recipe['instructions'])} found)")

            if has_name and has_ingredients and has_instructions:
                logger.info(f"Successfully parsed AllRecipes recipe: {recipe['name']}")
                return recipe
            else:
                logger.warning("Incomplete AllRecipes recipe data - rejecting")
                logger.info(f"Missing fields:")
                if not has_name:
                    logger.info(f"  - Name (found: '{recipe['name']}')")
                if not has_ingredients:
                    logger.info(f"  - Ingredients (found: {len(recipe['ingredients'])})")
                if not has_instructions:
                    logger.info(f"  - Instructions (found: {len(recipe['instructions'])})")
                return None

        except Exception as e:
            logger.error(f"Error parsing AllRecipes recipe schema: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _extract_text_value(self, value) -> str:
        """Extract text from various JSON-LD value formats with enhanced error handling"""
        try:
            if value is None:
                return ''
            elif isinstance(value, str):
                return value.strip()
            elif isinstance(value, dict):
                # Try multiple common text fields
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

                # If no text fields found, convert dict to string as fallback
                return str(value).strip()

            elif isinstance(value, list) and len(value) > 0:
                # Recursively extract from first non-empty item
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
        """Extract instruction text from HowToStep or other formats with enhanced error handling"""
        try:
            if inst_item is None:
                return ''
            elif isinstance(inst_item, str):
                return inst_item.strip()
            elif isinstance(inst_item, dict):
                # Try multiple common instruction text fields
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

                # Convert to string as fallback
                return str(inst_item).strip()
            else:
                return str(inst_item).strip() if inst_item else ''
        except Exception as e:
            logger.debug(f"Error extracting instruction text from {type(inst_item)}: {e}")
            return ''

    def _extract_serving_size(self, recipe_yield) -> Optional[int]:
        """Extract serving size from various formats"""
        try:
            if isinstance(recipe_yield, (list, tuple)) and len(recipe_yield) > 0:
                recipe_yield = recipe_yield[0]

            if isinstance(recipe_yield, str):
                match = re.search(r'\d+', recipe_yield)
                if match:
                    serving_size = int(match.group())
                    if 1 <= serving_size <= 50:
                        return serving_size
            elif isinstance(recipe_yield, (int, float)):
                serving_size = int(recipe_yield)
                if 1 <= serving_size <= 50:
                    return serving_size
        except:
            pass
        return None

    def _determine_genre(self, category) -> str:
        """Determine recipe genre from category"""
        if isinstance(category, list) and len(category) > 0:
            category = category[0]

        category_str = str(category).lower()

        if 'dessert' in category_str or 'sweet' in category_str:
            return 'dessert'
        elif 'breakfast' in category_str:
            return 'breakfast'
        elif 'lunch' in category_str:
            return 'lunch'
        elif any(word in category_str for word in ['dinner', 'main', 'entree', 'supper']):
            return 'dinner'
        elif 'snack' in category_str:
            return 'snack'
        elif 'appetizer' in category_str or 'starter' in category_str:
            return 'appetizer'
        else:
            return 'dinner'

    def _extract_recipe_with_enhanced_parsing(self, html_content: str, url: str, ingredient: str) -> Optional[Dict]:
        """Enhanced HTML parsing to extract AllRecipes recipe data without AI"""
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
                'source': 'allrecipes.com'
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
            logger.error(f"Error in AllRecipes enhanced parsing: {e}")
            return None

    def _extract_microdata_recipe(self, soup) -> Optional[Dict]:
        """Extract AllRecipes recipe data from microdata attributes"""
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

            # Extract times
            prep_elem = container.find(attrs={'itemprop': 'prepTime'})
            if prep_elem:
                prep_time = prep_elem.get('datetime') or prep_elem.get_text()
                recipe['prep_time'] = self._parse_iso_duration(prep_time)

            cook_elem = container.find(attrs={'itemprop': 'cookTime'})
            if cook_elem:
                cook_time = cook_elem.get('datetime') or cook_elem.get_text()
                recipe['cook_time'] = self._parse_iso_duration(cook_time)

            # Extract yield/serving size
            yield_elem = container.find(attrs={'itemprop': re.compile(r'recipeYield|yield', re.I)})
            if yield_elem:
                yield_text = yield_elem.get_text().strip()
                serving_size = self._extract_serving_size(yield_text)
                if serving_size:
                    recipe['serving_size'] = serving_size

            # Only return if we got meaningful data
            if (recipe['name'] and
                    len(recipe['ingredients']) >= 2 and
                    len(recipe['instructions']) >= 1):
                logger.info("Successfully extracted AllRecipes recipe from microdata")
                return recipe

            return None

        except Exception as e:
            logger.error(f"Error extracting AllRecipes microdata: {e}")
            return None

    def _try_ai_parsing_with_limits(self, page_content: str, url: str, ingredient: str) -> Optional[Dict]:
        """Try AI parsing with strict limits - LAST RESORT ONLY for AllRecipes"""
        try:
            import time
            start_time = time.time()

            logger.warning(f"Falling back to AI parsing for AllRecipes {url} - structured data extraction failed!")

            from ..utils.ai_helper import ai_helper

            if not ai_helper or not ai_helper.is_configured():
                logger.info("AI helper not configured, skipping AllRecipes AI parsing")
                return None

            clean_text = self._extract_clean_recipe_text(page_content)
            if not clean_text or len(clean_text) < 100:
                logger.debug("Insufficient clean text for AllRecipes AI parsing")
                return None

            max_ai_content = 2500
            if len(clean_text) > max_ai_content:
                clean_text = clean_text[:max_ai_content] + "..."

            if time.time() - start_time > 3:
                logger.warning(f"Skipping AI parsing for AllRecipes {url} due to timeout")
                return None

            try:
                response = ai_helper.client.chat.completions.create(
                    model=ai_helper.model,
                    messages=[
                        {"role": "system", "content": """Extract recipe information from AllRecipes webpage content and return as JSON.
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
                        {"role": "user", "content": f"Extract AllRecipes recipe from: {clean_text}"}
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
                    parsed_recipe['source'] = 'allrecipes.com'
                    logger.info(f"AllRecipes AI parsing successful for {url}: {parsed_recipe.get('name')}")
                    return parsed_recipe

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing AllRecipes AI response for {url}: {e}")
            except Exception as e:
                logger.warning(f"AllRecipes AI parsing timeout or error for {url}: {e}")

            return None

        except ImportError:
            logger.info("AI Helper not available for AllRecipes recipe parsing")
            return None
        except Exception as e:
            logger.error(f"Error in AllRecipes AI parsing attempt: {e}")
            return None

    def _extract_clean_recipe_text(self, html_content: str) -> str:
        """Extract clean text content focusing on AllRecipes recipe-relevant sections"""
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
            logger.error(f"Error extracting clean text from AllRecipes: {e}")
            return ""

    def _create_basic_recipe_from_page(self, html_content: str, url: str, ingredient: str) -> Dict:
        """Create a basic AllRecipes recipe when structured data isn't available"""
        try:
            title = "AllRecipes Recipe"
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
                'name': title if title != "AllRecipes Recipe" else f"AllRecipes {ingredient.title()} Recipe",
                'description': f'Recipe found on AllRecipes.com. Visit the original page for complete details.',
                'ingredients': [
                    {'name': f'{ingredient} (see original AllRecipes recipe for details)', 'quantity': 1,
                     'unit': 'recipe'}
                ],
                'instructions': [
                    f'This AllRecipes recipe requires visiting the original page at {url} for complete instructions.',
                    'The structured data could not be extracted automatically from AllRecipes.'
                ],
                'serving_size': 4,
                'prep_time': 15,
                'cook_time': 30,
                'genre': genre,
                'notes': [f'Original recipe from AllRecipes.com', 'Automatic extraction failed - manual review needed'],
                'dietary_restrictions': [],
                'url': url,
                'source': 'allrecipes.com',
                'extraction_method': 'basic_fallback'
            }

        except Exception as e:
            logger.error(f"Error creating basic AllRecipes recipe: {e}")
            return {
                'name': f"AllRecipes {ingredient.title()} Recipe",
                'description': 'AllRecipes recipe extraction failed',
                'ingredients': [{'name': ingredient, 'quantity': 1, 'unit': 'recipe'}],
                'instructions': [f'Visit {url} for the complete AllRecipes recipe'],
                'serving_size': 4,
                'prep_time': 0,
                'cook_time': 0,
                'genre': 'dinner',
                'notes': ['AllRecipes extraction failed'],
                'dietary_restrictions': [],
                'url': url,
                'source': 'allrecipes.com',
                'extraction_method': 'minimal_fallback'
            }

    def _parse_ingredient_text(self, text: str) -> Optional[Dict]:
        """Parse AllRecipes ingredient text into quantity, unit, name"""
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
            logger.error(f"Error parsing AllRecipes ingredient text '{text}': {e}")
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
            logger.error(f"Error parsing AllRecipes duration '{duration_str}': {e}")
            return 0

    def _generate_fallback_recipes(self, ingredient: str, criteria: Dict[str, Any]) -> List[Dict]:
        """Generate fallback recipes when AllRecipes search fails"""
        return [{
            "name": f"AllRecipes Style {ingredient.title()}",
            "source": "allrecipes.com",
            "description": f"A {ingredient} recipe in the style of AllRecipes.com. (Unable to fetch live data)",
            "url": f"https://www.allrecipes.com/search?q={ingredient.replace(' ', '+')}",
            "ingredients": [
                {"name": ingredient.split()[0] if ingredient != 'recipe' else 'main ingredient', "quantity": 2,
                 "unit": "cups"},
                {"name": "additional ingredients", "quantity": 1, "unit": "cup"}
            ],
            "instructions": [
                f"Follow AllRecipes' typical preparation method",
                "Cook according to your preference"
            ],
            "serving_size": criteria.get('serving_size', 4),
            "prep_time": 15,
            "cook_time": 25,
            "genre": criteria.get('genre', 'dinner'),
            "notes": [f"Please visit AllRecipes.com directly for the most current recipes"],
            "dietary_restrictions": [],
            "cuisine_type": "general"
        }]

    def debug_json_ld_extraction(self, url: str) -> Dict[str, Any]:
        """Debug function to inspect JSON-LD data from a specific AllRecipes URL"""
        try:
            page_content = self._fetch_webpage_content(url)
            if not page_content:
                return {"error": "Could not fetch AllRecipes page content"}

            if not BS4_AVAILABLE:
                return {"error": "BeautifulSoup not available"}

            soup = BeautifulSoup(page_content, 'html.parser')
            json_scripts = soup.find_all('script', type='application/ld+json')

            debug_info = {
                "url": url,
                "site": "allrecipes.com",
                "total_scripts": len(json_scripts),
                "scripts": []
            }

            for i, script in enumerate(json_scripts):
                script_info = {
                    "index": i,
                    "has_content": bool(script.string),
                    "content_length": len(script.string) if script.string else 0,
                    "content_preview": script.string[:500] if script.string else None,
                    "parse_success": False,
                    "parse_error": None,
                    "structure": None
                }

                if script.string:
                    try:
                        data = json.loads(script.string)
                        script_info["parse_success"] = True
                        script_info["structure"] = {
                            "type": str(type(data).__name__),
                            "keys": list(data.keys()) if isinstance(data, dict) else None,
                            "length": len(data) if isinstance(data, list) else None,
                            "has_recipe": self._find_recipe_in_data_enhanced(data) is not None
                        }
                    except Exception as e:
                        script_info["parse_error"] = str(e)

                debug_info["scripts"].append(script_info)

            return debug_info

        except Exception as e:
            return {"error": str(e)}
# backend/app/toolset/recipe_cache.py

import json
import hashlib
import time
from typing import Optional, Dict, Any
from .base_imports import logger


class RecipeCache:
    """Simple in-memory cache for recipe data with TTL"""

    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl_seconds = ttl_hours * 3600

    def _generate_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached recipe data for a URL"""
        try:
            cache_key = self._generate_cache_key(url)

            if cache_key not in self.cache:
                return None

            cached_item = self.cache[cache_key]
            current_time = time.time()

            # Check if cached item has expired
            if current_time - cached_item['timestamp'] > self.ttl_seconds:
                del self.cache[cache_key]
                logger.debug(f"Cache expired for {url}")
                return None

            logger.debug(f"Cache hit for {url}")
            return cached_item['data']

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, url: str, recipe_data: Dict[str, Any]) -> None:
        """Cache recipe data for a URL"""
        try:
            cache_key = self._generate_cache_key(url)

            self.cache[cache_key] = {
                'data': recipe_data,
                'timestamp': time.time(),
                'url': url  # Store for debugging
            }

            logger.debug(f"Cached recipe data for {url}")

            # Cleanup old entries periodically
            self._cleanup_expired()

        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        try:
            current_time = time.time()
            expired_keys = []

            for key, item in self.cache.items():
                if current_time - item['timestamp'] > self.ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Recipe cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0

        for item in self.cache.values():
            if current_time - item['timestamp'] <= self.ttl_seconds:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_size_mb': len(json.dumps(self.cache)) / (1024 * 1024)
        }


# Global cache instance
recipe_cache = RecipeCache(ttl_hours=24)
"""LRU (Least Recently Used) cache implementation for optimisation.

This module provides a thread-safe LRU cache with configurable size limits.
Used for caching translation results and OCR outputs to avoid redundant processing.
"""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import threading
import typing as t
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================

T = t.TypeVar("T")


@dataclass
class CacheEntry(t.Generic[T]):
    """Represents a single cache entry with metadata.

    Args:
        value: The cached value.
        created_at: When the entry was created.
        access_count: Number of times this entry has been accessed.
    """

    value: T
    created_at: datetime
    access_count: int = 0


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================
class LRUCache(t.Generic[T]):
    """Thread-safe LRU cache with size limits and statistics.

    This cache automatically evicts the least recently used items when
    the maximum size is reached. All operations are thread-safe.

    Example:
        >>> cache = LRUCache[str](max_size=100)
        >>> cache.put("key1", "value1")
        >>> result = cache.get("key1")
        >>> cache.clear()
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialise the LRU cache.

        Args:
            max_size: Maximum number of items to store in the cache.
        """
        if max_size <= 0:
            msg = "max_size must be positive"
            raise ValueError(msg)

        self._max_size = max_size
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> T | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found, None otherwise.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry = self._cache[key]
            entry.access_count += 1
            self._hits += 1

            return entry.value

    def put(self, key: str, value: T) -> None:
        """Add or update a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        with self._lock:
            if key in self._cache:
                # Update existing entry
                self._cache.move_to_end(key)
                self._cache[key].value = value
                self._cache[key].access_count += 1
            else:
                # Add new entry
                if len(self._cache) >= self._max_size:
                    # Remove least recently used item
                    self._cache.popitem(last=False)

                self._cache[key] = CacheEntry(
                    value=value,
                    created_at=datetime.now(),
                    access_count=0,
                )
                self._cache.move_to_end(key)

    def contains(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        with self._lock:
            return key in self._cache

    def remove(self, key: str) -> bool:
        """Remove a key from the cache.

        Args:
            key: The cache key to remove.

        Returns:
            True if the key was removed, False if it didn't exist.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all items from the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def size(self) -> int:
        """Get the current number of items in the cache.

        Returns:
            Number of items currently cached.
        """
        with self._lock:
            return len(self._cache)

    def hit_rate(self) -> float:
        """Calculate the cache hit rate.

        Returns:
            Hit rate as a percentage (0.0 to 100.0).
        """
        with self._lock:
            total = self._hits + self._misses
            if total == 0:
                return 0.0
            return (self._hits / total) * 100.0

    def stats(self) -> dict[str, t.Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics.
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self.hit_rate(),
            }


# =============================================================================
# 4. PRIVATE HELPERS & UTILITIES
# =============================================================================
def create_translation_cache(max_size: int = 5000) -> LRUCache[str]:
    """Create an LRU cache optimised for translation results.

    Args:
        max_size: Maximum number of translations to cache.

    Returns:
        Configured LRU cache for translations.
    """
    return LRUCache[str](max_size=max_size)


def create_ocr_cache(max_size: int = 1000) -> LRUCache[list[str]]:
    """Create an LRU cache optimised for OCR results.

    Args:
        max_size: Maximum number of OCR results to cache.

    Returns:
        Configured LRU cache for OCR results.
    """
    return LRUCache[list[str]](max_size=max_size)

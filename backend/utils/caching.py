"""Reusable cache management utilities."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import typing as t
from typing import Generic, TypeVar

# Project/local
from ..cache.lru_cache import LRUCache

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================
T = TypeVar("T")


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class CacheMixin(Generic[T]):
    """Mixin providing standard cache operations.

    Classes inheriting from this mixin should define:
        - self._cache: LRUCache[T] | None

    This mixin provides:
        - clear_cache()
        - get_cache_stats()
    """

    _cache: LRUCache[T] | None

    def clear_cache(self) -> None:
        """Clear the cache.

        This method clears all cached entries if caching is enabled.
        """
        if hasattr(self, "_cache") and self._cache is not None:
            self._cache.clear()

    def get_cache_stats(self) -> dict[str, t.Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including hits, misses, and size.
            If caching is disabled, returns {"enabled": False}.
        """
        if hasattr(self, "_cache") and self._cache is not None:
            return self._cache.stats()
        return {"enabled": False}

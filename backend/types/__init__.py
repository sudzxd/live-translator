"""Shared type definitions and protocols."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import typing as t
from typing import Protocol, runtime_checkable


# =============================================================================
# 2. PROTOCOLS
# =============================================================================
@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialised to dictionaries.

    Classes implementing this protocol must provide a to_dict() method
    that converts the object to a dictionary representation suitable for
    JSON serialisation.
    """

    def to_dict(self) -> dict[str, t.Any]:
        """Convert object to dictionary representation.

        Returns:
            Dictionary representation of the object.
        """
        ...


@runtime_checkable
class Hashable(Protocol):
    """Protocol for objects that can generate cache keys.

    Classes implementing this protocol must provide a cache_key() method
    that generates a unique string identifier for caching purposes.
    """

    def cache_key(self) -> str:
        """Generate a cache key for this object.

        Returns:
            Unique string identifier for caching.
        """
        ...


# =============================================================================
# 3. TYPE ALIASES
# =============================================================================

# Bounding box as list of [x, y] coordinate pairs
BoundingBox = list[list[float]]

# Language code (ISO 639-1 two-letter code)
LanguageCode = str

# Cache key (typically a hash string)
CacheKey = str

# RGB image data as nested list
ImageData = list[list[list[int]]]

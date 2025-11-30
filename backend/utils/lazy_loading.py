"""Lazy loading utilities for deferred resource initialisation."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
from collections.abc import Callable
from typing import Generic, TypeVar

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================
T = TypeVar("T")


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class LazyLoader(Generic[T]):
    """Defer resource initialisation until first access.

    This class wraps a resource that is expensive to create and defers
    its initialisation until the first time it's accessed.

    Example:
        >>> def load_model():
        ...     return ExpensiveModel()
        >>> loader = LazyLoader(load_model)
        >>> model = loader.get()  # Initialised only on first call
    """

    def __init__(self, loader_func: Callable[[], T]) -> None:
        """Initialise the lazy loader.

        Args:
            loader_func: Function that creates the resource when called.
        """
        self._value: T | None = None
        self._loader = loader_func
        self._loaded = False

    def get(self) -> T:
        """Get the lazily loaded value.

        The loader function is called only once, on the first invocation
        of this method. Subsequent calls return the cached value.

        Returns:
            The loaded resource.
        """
        if not self._loaded:
            self._value = self._loader()
            self._loaded = True
        return self._value  # type: ignore[return-value]

    def is_loaded(self) -> bool:
        """Check if the resource has been loaded.

        Returns:
            True if the resource has been initialised, False otherwise.
        """
        return self._loaded

    def reset(self) -> None:
        """Reset the lazy loader.

        This clears the cached value and allows the resource to be
        re-initialised on the next call to get().
        """
        self._value = None
        self._loaded = False


def ensure_initialised(instance: T | None, initialiser: Callable[[], T]) -> T:
    """Simple lazy initialisation helper.

    If instance is None, calls initialiser to create it. Otherwise returns
    the existing instance.

    Args:
        instance: Existing instance or None.
        initialiser: Function to create the instance if needed.

    Returns:
        The instance (either existing or newly created).

    Example:
        >>> model = None
        >>> model = ensure_initialised(model, lambda: load_model())
    """
    if instance is None:
        return initialiser()
    return instance

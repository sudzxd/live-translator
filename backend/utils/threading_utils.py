"""Thread-safe containers and synchronisation utilities."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import threading
from collections.abc import Callable
from typing import Generic, TypeVar

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================

T = TypeVar("T")


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class ThreadSafeContainer(Generic[T]):
    """Thread-safe container for a single value with atomic operations.

    This class provides thread-safe storage and retrieval of a single value.
    All operations are protected by a lock to ensure atomicity.

    Example:
        >>> container = ThreadSafeContainer[list[str]]([])
        >>> container.set(["hello", "world"])
        >>> value = container.get()
    """

    def __init__(self, initial_value: T) -> None:
        """Initialise the container with an initial value.

        Args:
            initial_value: The initial value to store.
        """
        self._value: T = initial_value
        self._lock = threading.Lock()

    def get(self) -> T:
        """Get the current value.

        Returns:
            The current value stored in the container.
        """
        with self._lock:
            return self._value

    def set(self, value: T) -> None:
        """Set a new value.

        Args:
            value: The new value to store.
        """
        with self._lock:
            self._value = value

    def update(self, func: Callable[[T], T]) -> T:
        """Update the value using a function.

        Atomically applies a function to the current value and stores the result.

        Args:
            func: Function that takes the current value and returns the new value.

        Returns:
            The new value after applying the function.
        """
        with self._lock:
            self._value = func(self._value)
            return self._value


class ThreadSafeFlag:
    """Thread-safe boolean flag for controlling loops and state.

    This class provides a thread-safe boolean flag commonly used for
    controlling background threads or indicating state.

    Example:
        >>> flag = ThreadSafeFlag(False)
        >>> flag.set()
        >>> if flag.is_set():
        ...     print("Flag is set")
        >>> flag.clear()
    """

    def __init__(self, initial_state: bool = False) -> None:
        """Initialise the flag with an initial state.

        Args:
            initial_state: Initial state of the flag (True or False).
        """
        self._state: bool = initial_state
        self._lock = threading.Lock()

    def set(self) -> None:
        """Set the flag to True."""
        with self._lock:
            self._state = True

    def clear(self) -> None:
        """Set the flag to False."""
        with self._lock:
            self._state = False

    def is_set(self) -> bool:
        """Check if the flag is set.

        Returns:
            True if the flag is set, False otherwise.
        """
        with self._lock:
            return self._state

    def toggle(self) -> bool:
        """Toggle the flag state.

        Returns:
            The new state after toggling.
        """
        with self._lock:
            self._state = not self._state
            return self._state

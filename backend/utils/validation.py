"""Input validation utilities."""


# =============================================================================
# 1. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================
def is_empty_or_whitespace(text: str | None) -> bool:
    """Check if text is None, empty, or whitespace-only.

    Args:
        text: The text to check.

    Returns:
        True if text is None, empty string, or only whitespace.
    """
    return not text or not text.strip()


def validate_positive_int(value: int, name: str) -> None:
    """Validate that an integer is positive.

    Args:
        name: Name of the parameter (for error messages).
        value: The integer to validate.

    Raises:
        ValueError: If value is not positive.
    """
    if value <= 0:
        msg = f"{name} must be positive, got {value}"
        raise ValueError(msg)


def validate_range(
    value: float,
    min_value: float,
    max_value: float,
    name: str,
) -> None:
    """Validate that a value is within a range.

    Args:
        value: The value to validate.
        min_value: Minimum allowed value (inclusive).
        max_value: Maximum allowed value (inclusive).
        name: Name of the parameter (for error messages).

    Raises:
        ValueError: If value is outside the range.
    """
    if not min_value <= value <= max_value:
        msg = f"{name} must be between {min_value} and {max_value}, got {value}"
        raise ValueError(msg)


def validate_non_empty_string(value: str, name: str) -> None:
    """Validate that a string is not empty or whitespace-only.

    Args:
        value: The string to validate.
        name: Name of the parameter (for error messages).

    Raises:
        ValueError: If value is empty or whitespace-only.
    """
    if is_empty_or_whitespace(value):
        msg = f"{name} must not be empty or whitespace-only"
        raise ValueError(msg)

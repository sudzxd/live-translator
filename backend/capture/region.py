"""Region data structures for screen capture optimisation."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
from dataclasses import dataclass

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================


@dataclass(frozen=True)
class Region:
    """Represents a rectangular region on the screen.

    Args:
        x: X coordinate of top-left corner.
        y: Y coordinate of top-left corner.
        width: Width of the region.
        height: Height of the region.
    """

    x: int
    y: int
    width: int
    height: int

    def area(self) -> int:
        """Calculate the area of this region.

        Returns:
            Area in pixels.
        """
        return self.width * self.height

    def intersects(self, other: "Region") -> bool:
        """Check if this region intersects with another.

        Args:
            other: The other region to check against.

        Returns:
            True if regions intersect, False otherwise.
        """
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )

    def contains(self, x: int, y: int) -> bool:
        """Check if a point is within this region.

        Args:
            x: X coordinate of the point.
            y: Y coordinate of the point.

        Returns:
            True if point is inside the region, False otherwise.
        """
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def to_dict(self) -> dict[str, int]:
        """Convert region to dictionary format.

        Returns:
            Dictionary with x, y, width, height keys.
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


def create_region(x: int, y: int, width: int, height: int) -> Region:
    """Create a region with validation.

    Args:
        x: X coordinate of top-left corner.
        y: Y coordinate of top-left corner.
        width: Width of the region (must be positive).
        height: Height of the region (must be positive).

    Returns:
        Validated Region instance.

    Raises:
        ValueError: If width or height is not positive.
    """
    if width <= 0 or height <= 0:
        msg = "Width and height must be positive"
        raise ValueError(msg)

    return Region(x=x, y=y, width=width, height=height)

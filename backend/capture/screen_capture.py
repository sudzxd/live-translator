"""Screen capture with dirty region tracking for optimisation.

This module provides efficient screen capture by only processing regions
that have changed since the last capture, significantly reducing CPU usage.
"""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
from dataclasses import dataclass

# Third-party
import mss
from PIL import Image

from ..utils.constants import CHANGE_THRESHOLD_PERCENT, GRID_SIZE_PIXELS
from ..utils.hashing import hash_image

# Project/local
from .region import Region

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================
# Threshold for detecting region changes (percentage)
CHANGE_THRESHOLD = CHANGE_THRESHOLD_PERCENT

# Grid size for dirty region detection (pixels)
GRID_SIZE = GRID_SIZE_PIXELS


@dataclass
class CaptureResult:
    """Result of a screen capture operation.

    Args:
        image: The captured image.
        region: The region that was captured.
        changed: Whether this region has changed since last capture.
        hash_value: Hash of the image data for change detection.
    """

    image: Image.Image
    region: Region
    changed: bool
    hash_value: str


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class ScreenCapture:
    """Optimised screen capture with dirty region tracking.

    This class captures screen regions and tracks which areas have changed
    to avoid redundant processing of static content.

    Example:
        >>> capture = ScreenCapture()
        >>> region = Region(x=0, y=0, width=800, height=600)
        >>> result = capture.capture_region(region)
        >>> if result.changed:
        ...     # Process the changed region
        ...     process_image(result.image)
    """

    def __init__(self) -> None:
        """Initialise the screen capture system."""
        self._sct = mss.mss()
        self._region_hashes: dict[str, str] = {}
        self._last_full_hash: str | None = None

    def capture_region(self, region: Region) -> CaptureResult:
        """Capture a specific screen region.

        Args:
            region: The region to capture.

        Returns:
            Capture result with image and change detection info.
        """
        # Capture the region
        monitor = {
            "left": region.x,
            "top": region.y,
            "width": region.width,
            "height": region.height,
        }

        screenshot = self._sct.grab(monitor)
        image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        # Calculate hash for change detection
        hash_value = self._calculate_image_hash(image)
        region_key = self._region_to_key(region)

        # Check if changed
        changed = self._has_changed(region_key, hash_value)

        # Update hash
        self._region_hashes[region_key] = hash_value

        return CaptureResult(
            image=image,
            region=region,
            changed=changed,
            hash_value=hash_value,
        )

    def capture_window(self, x: int, y: int, width: int, height: int) -> CaptureResult:
        """Capture a window region with change detection.

        Args:
            x: X coordinate of top-left corner.
            y: Y coordinate of top-left corner.
            width: Width of the window.
            height: Height of the window.

        Returns:
            Capture result with image and change detection info.
        """
        region = Region(x=x, y=y, width=width, height=height)
        return self.capture_region(region)

    def detect_dirty_regions(
        self,
        region: Region,
        grid_size: int = GRID_SIZE,
    ) -> list[Region]:
        """Detect which sub-regions have changed within a larger region.

        This divides the region into a grid and checks each cell for changes,
        returning only the cells that have been modified.

        Args:
            region: The region to analyse.
            grid_size: Size of each grid cell in pixels.

        Returns:
            List of dirty (changed) regions.
        """
        dirty_regions: list[Region] = []

        # Divide region into grid
        for y in range(region.y, region.y + region.height, grid_size):
            for x in range(region.x, region.x + region.width, grid_size):
                # Calculate cell dimensions
                cell_width = min(grid_size, region.x + region.width - x)
                cell_height = min(grid_size, region.y + region.height - y)

                if cell_width <= 0 or cell_height <= 0:
                    continue

                cell_region = Region(
                    x=x,
                    y=y,
                    width=cell_width,
                    height=cell_height,
                )

                # Check if cell has changed
                result = self.capture_region(cell_region)
                if result.changed:
                    dirty_regions.append(cell_region)

        return dirty_regions

    def clear_cache(self) -> None:
        """Clear all cached region hashes.

        This forces all regions to be marked as changed on next capture.
        """
        self._region_hashes.clear()
        self._last_full_hash = None

    def close(self) -> None:
        """Clean up resources."""
        self._sct.close()

    # =============================================================================
    # 4. PRIVATE HELPERS & UTILITIES
    # =============================================================================

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate a hash of the image data.

        Args:
            image: The image to hash.

        Returns:
            SHA256 hash of the image data.
        """
        return hash_image(image)

    def _region_to_key(self, region: Region) -> str:
        """Convert a region to a cache key.

        Args:
            region: The region to convert.

        Returns:
            String key for the region.
        """
        return f"{region.x},{region.y},{region.width},{region.height}"

    def _has_changed(self, region_key: str, current_hash: str) -> bool:
        """Check if a region has changed.

        Args:
            region_key: The region cache key.
            current_hash: Current hash of the region.

        Returns:
            True if changed, False otherwise.
        """
        if region_key not in self._region_hashes:
            return True

        previous_hash = self._region_hashes[region_key]
        return previous_hash != current_hash


# =============================================================================
# 5. UTILITY FUNCTIONS
# =============================================================================


def create_screen_capture() -> ScreenCapture:
    """Create a screen capture instance.

    Returns:
        Configured ScreenCapture instance.
    """
    return ScreenCapture()

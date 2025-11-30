"""Hashing utilities for cache keys and change detection."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import hashlib

# Third-party
import numpy as np
from PIL import Image

# Project/local
from .constants import IMAGE_DOWNSAMPLE_RATE

# =============================================================================
# 2. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


def hash_image(
    image: Image.Image,
    downsample_rate: int = IMAGE_DOWNSAMPLE_RATE,
) -> str:
    """Calculate SHA256 hash of an image for change detection.

    Args:
        image: The image to hash.
        downsample_rate: Factor to downsample by for faster hashing.

    Returns:
        SHA256 hash of the downsampled image data.
    """
    # Convert to numpy array for faster processing
    img_array = np.array(image)

    # Downsample for faster hashing
    downsampled = img_array[::downsample_rate, ::downsample_rate, :]

    # Calculate hash
    hash_obj = hashlib.sha256(downsampled.tobytes())
    return hash_obj.hexdigest()


def hash_text(text: str, encoding: str = "utf-8") -> str:
    """Calculate SHA256 hash of text for cache keys.

    Args:
        text: The text to hash.
        encoding: Text encoding to use.

    Returns:
        SHA256 hash of the text.
    """
    hash_obj = hashlib.sha256(text.encode(encoding))
    return hash_obj.hexdigest()


def create_cache_key(text: str, source_lang: str, target_lang: str) -> str:
    """Create a cache key for translation results.

    Args:
        text: The text to translate.
        source_lang: Source language code.
        target_lang: Target language code.

    Returns:
        SHA256 hash combining text and language pair.
    """
    # Include language pair in hash to avoid collisions
    key_data = f"{source_lang}:{target_lang}:{text}"
    return hash_text(key_data)

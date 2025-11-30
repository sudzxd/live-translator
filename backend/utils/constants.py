"""Application-wide constants and configuration values."""

# =============================================================================
# 1. WINDOW CONFIGURATION
# =============================================================================

DEFAULT_WINDOW_WIDTH: int = 800
DEFAULT_WINDOW_HEIGHT: int = 600
DEFAULT_WINDOW_X: int = 100
DEFAULT_WINDOW_Y: int = 100
WINDOW_MOVE_THRESHOLD: int = 50  # pixels
WINDOW_RESIZE_THRESHOLD: int = 10  # pixels

# =============================================================================
# 2. PROCESSING CONFIGURATION
# =============================================================================

PROCESSING_INTERVAL_SECONDS: float = 1.0

# =============================================================================
# 3. OCR CONFIGURATION
# =============================================================================

MIN_OCR_CONFIDENCE: float = 0.5
DEFAULT_OCR_CACHE_SIZE: int = 1000
DEFAULT_OCR_LANGUAGE: str = "en"

# =============================================================================
# 4. TRANSLATION CONFIGURATION
# =============================================================================
DEFAULT_TRANSLATION_CACHE_SIZE: int = 5000
DEFAULT_SOURCE_LANGUAGE: str = "es"
DEFAULT_TARGET_LANGUAGE: str = "en"

# =============================================================================
# 5. IMAGE PROCESSING
# =============================================================================

IMAGE_DOWNSAMPLE_RATE: int = 4

# =============================================================================
# 6. SCREEN CAPTURE
# =============================================================================

CHANGE_THRESHOLD_PERCENT: float = 5.0
GRID_SIZE_PIXELS: int = 50

# =============================================================================
# 7. LOGGING
# =============================================================================

LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

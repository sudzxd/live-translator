"""API bridge between Python backend and JavaScript frontend.

This module provides the interface for the frontend to communicate with
the backend OCR and translation services.
"""

# =============================================================================
# 1. IMPORTS
# =============================================================================
# Standard library
import threading
import time
import typing as t
from dataclasses import dataclass

# Third-party
import webview

from ..capture.region import Region

# Project/local
from ..capture.screen_capture import ScreenCapture, create_screen_capture
from ..ocr.text_detection import OCREngine, create_ocr_engine
from ..translation.translator import Translator, create_translator
from ..utils.constants import (
    MIN_OCR_CONFIDENCE,
    PROCESSING_INTERVAL_SECONDS,
    WINDOW_MOVE_THRESHOLD,
    WINDOW_RESIZE_THRESHOLD,
)
from ..utils.logging_config import get_logger

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================

logger = get_logger(__name__)


@dataclass
class TranslatedText:
    """Represents a piece of translated text with position.

    Args:
        original: The original detected text.
        translated: The translated text.
        confidence: OCR confidence score.
        bbox: Bounding box coordinates.
    """

    original: str
    translated: str
    confidence: float
    bbox: list[list[float]]

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "original": self.original,
            "translated": self.translated,
            "confidence": self.confidence,
            "bbox": self.bbox,
        }


# Processing interval in seconds
PROCESSING_INTERVAL = 1.0


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================
class TranslatorAPI:
    """API bridge for the live translator application.

    This class provides methods that are exposed to the JavaScript frontend
    via pywebview's JS API. It coordinates OCR, translation, and screen capture.

    Example:
        >>> api = TranslatorAPI(window)
        >>> api.start_processing()
        >>> results = api.get_latest_results()
    """

    def __init__(
        self,
        window: webview.Window | None = None,
        source_lang: str = "en",
        target_lang: str = "es",
    ) -> None:
        """Initialise the translator API.

        Args:
            window: The webview window instance (can be set later).
            source_lang: Source language code.
            target_lang: Target language code.
        """
        self._window = window
        self._source_lang = source_lang
        self._target_lang = target_lang

        # Initialise components (lazy-loaded)
        self._screen_capture: ScreenCapture | None = None
        self._ocr_engine: OCREngine | None = None
        self._translator: Translator | None = None

        # Processing state
        self._is_processing = False
        self._processing_thread: threading.Thread | None = None
        self._latest_results: list[TranslatedText] = []
        self._lock = threading.Lock()
        self._last_window_bounds: tuple[int, int, int, int] | None = None
        self._last_processed_hash: str | None = None
        self._has_processed_current_position = False

    def start_processing(self) -> dict[str, t.Any]:
        """Start the processing loop.

        Returns:
            Status dictionary.
        """
        logger.info("Starting processing loop")

        if self._is_processing:
            logger.warning("Processing already active")
            return {"success": False, "message": "Already processing"}

        logger.debug("Enabling processing flag")
        self._is_processing = True

        # Start processing thread
        logger.debug("Creating background thread")
        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
        )
        self._processing_thread.start()
        logger.info("Thread started (alive=%s)", self._processing_thread.is_alive())

        return {"success": True, "message": "Processing started"}

    def stop_processing(self) -> dict[str, t.Any]:
        """Stop the processing loop.

        Returns:
            Status dictionary.
        """
        self._is_processing = False

        if self._processing_thread is not None:
            self._processing_thread.join(timeout=2.0)

        return {"success": True, "message": "Processing stopped"}

    def get_latest_results(self) -> list[dict[str, t.Any]]:
        """Get the latest translation results.

        Returns:
            List of translated text results.
        """
        with self._lock:
            return [result.to_dict() for result in self._latest_results]

    def set_languages(
        self,
        source_lang: str,
        target_lang: str,
    ) -> dict[str, t.Any]:
        """Change the source and target languages.

        Args:
            source_lang: New source language code.
            target_lang: New target language code.

        Returns:
            Status dictionary.
        """
        try:
            # Create new translator with new languages
            self._translator = create_translator(
                source_lang=source_lang,
                target_lang=target_lang,
            )
            self._source_lang = source_lang
            self._target_lang = target_lang

            return {
                "success": True,
                "message": f"Languages set to {source_lang} -> {target_lang}",
            }
        except ValueError as e:
            return {"success": False, "message": str(e)}

    def get_cache_stats(self) -> dict[str, t.Any]:
        """Get statistics about the caches.

        Returns:
            Dictionary with cache statistics.
        """
        stats: dict[str, t.Any] = {}

        if self._ocr_engine is not None:
            stats["ocr"] = self._ocr_engine.get_cache_stats()

        if self._translator is not None:
            stats["translation"] = self._translator.get_cache_stats()

        return stats

    # =============================================================================
    # 4. PRIVATE HELPERS & UTILITIES
    # =============================================================================
    def _ensure_components_initialised(self) -> None:
        """Ensure all components are initialised (lazy loading)."""
        if self._screen_capture is None:
            self._screen_capture = create_screen_capture()

        if self._ocr_engine is None:
            self._ocr_engine = create_ocr_engine(use_cache=True, cache_size=1000)

        if self._translator is None:
            self._translator = create_translator(
                source_lang=self._source_lang,
                target_lang=self._target_lang,
            )

    def _processing_loop(self) -> None:
        """Main processing loop that captures, OCRs, and translates."""
        logger.info("Processing loop initialized")

        # Ensure components are initialised
        self._ensure_components_initialised()
        logger.debug("Components initialized")

        while self._is_processing:
            try:
                # Get window position and size
                x, y, width, height = self._get_window_bounds()
                logger.debug("Window bounds: x=%d y=%d w=%d h=%d", x, y, width, height)

                # Check if window bounds changed significantly (moved or resized)
                current_bounds = (x, y, width, height)
                if self._last_window_bounds is not None:
                    last_x, last_y, last_w, last_h = self._last_window_bounds
                    # Clear results if window moved or resized beyond threshold
                    if (
                        abs(x - last_x) > WINDOW_MOVE_THRESHOLD
                        or abs(y - last_y) > WINDOW_MOVE_THRESHOLD
                        or abs(width - last_w) > WINDOW_RESIZE_THRESHOLD
                        or abs(height - last_h) > WINDOW_RESIZE_THRESHOLD
                    ):
                        logger.info("Window moved/resized, clearing results")
                        with self._lock:
                            self._latest_results = []
                        # Reset hash so we re-process the new location
                        self._last_processed_hash = None
                        self._has_processed_current_position = False
                        if self._window is not None:
                            self._window.evaluate_js(
                                "window.updateTranslations && "
                                "window.updateTranslations()"
                            )
                self._last_window_bounds = current_bounds

                # Capture the region under the window
                region = Region(x=x, y=y, width=width, height=height)
                capture_result = self._screen_capture.capture_region(region)  # type: ignore[union-attr]
                logger.debug("Capture complete, changed: %s", capture_result.changed)

                # Only process once per window position to avoid capturing own overlays
                if not self._has_processed_current_position and capture_result.changed:
                    logger.debug("Processing new position")
                    self._has_processed_current_position = True
                    # Perform OCR
                    ocr_result = self._ocr_engine.detect_text(  # type: ignore[union-attr]
                        capture_result.image,
                        min_confidence=MIN_OCR_CONFIDENCE,
                    )
                    logger.info("OCR detected %d boxes", len(ocr_result.text_boxes))

                    # Translate detected text
                    results: list[TranslatedText] = []

                    if ocr_result.text_boxes:
                        logger.debug(
                            "Translating %d segments", len(ocr_result.text_boxes)
                        )
                        # Batch translate all text boxes
                        texts = [box.text for box in ocr_result.text_boxes]
                        translations = self._translator.translate_batch(texts)  # type: ignore[union-attr]

                        for box, translation in zip(
                            ocr_result.text_boxes,
                            translations,
                            strict=False,
                        ):
                            logger.debug(
                                "'%s' -> '%s'", box.text, translation.translated_text
                            )
                            results.append(
                                TranslatedText(
                                    original=box.text,
                                    translated=translation.translated_text,
                                    confidence=box.confidence,
                                    bbox=box.bbox,
                                )
                            )

                    # Update results
                    with self._lock:
                        self._latest_results = results
                    logger.info("Updated: %d translations", len(results))

                    # Notify frontend of new results
                    if self._window is not None:
                        self._window.evaluate_js(
                            "window.updateTranslations && window.updateTranslations()"
                        )
                        logger.debug("Frontend notified")

            except (OSError, RuntimeError) as e:
                logger.error("System error: %s", e, exc_info=True)
            except Exception as e:
                logger.exception("Unexpected error: %s", e)

            # Wait before next iteration
            time.sleep(PROCESSING_INTERVAL_SECONDS)

    def set_window(self, window: webview.Window) -> None:
        """Set the window reference after initialization.

        Args:
            window: The webview window instance.
        """
        self._window = window

    def _get_window_bounds(self) -> tuple[int, int, int, int]:
        """Get the current window position and size.

        Returns:
            Tuple of (x, y, width, height).
        """
        if self._window is None:
            return (0, 0, 800, 600)

        # Get window position and size
        x = self._window.x
        y = self._window.y
        width = self._window.width
        height = self._window.height

        return (x, y, width, height)


# =============================================================================
# 5. UTILITY FUNCTIONS
# =============================================================================
def create_translator_api(
    window: webview.Window,
    source_lang: str = "en",
    target_lang: str = "es",
) -> TranslatorAPI:
    """Create a translator API instance.

    Args:
        window: The webview window instance.
        source_lang: Source language code.
        target_lang: Target language code.

    Returns:
        Configured translator API.
    """
    return TranslatorAPI(
        window=window,
        source_lang=source_lang,
        target_lang=target_lang,
    )

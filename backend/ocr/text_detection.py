"""OCR text detection using PaddleOCR with caching optimisation."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import typing as t
from dataclasses import dataclass

# Third-party
import numpy as np
from PIL import Image

# Note: PaddleOCR import is lazy-loaded to avoid startup overhead
# Project/local
from ..cache.lru_cache import LRUCache
from ..utils.caching import CacheMixin
from ..utils.hashing import hash_image
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================


@dataclass
class TextBox:
    """Represents a detected text box.

    Args:
        text: The detected text content.
        confidence: Confidence score (0.0 to 1.0).
        bbox: Bounding box coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]].
    """

    text: str
    confidence: float
    bbox: list[list[float]]

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary representation of the text box.
        """
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": self.bbox,
        }


@dataclass
class OCRResult:
    """Result of OCR processing.

    Args:
        text_boxes: List of detected text boxes.
        full_text: Concatenated text from all boxes.
        cached: Whether this result was retrieved from cache.
    """

    text_boxes: list[TextBox]
    full_text: str
    cached: bool


# Minimum confidence threshold for text detection
MIN_CONFIDENCE = 0.5


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class OCREngine(CacheMixin[OCRResult]):
    """OCR engine with caching and optimisation.

    This engine uses PaddleOCR for text detection and caches results
    to avoid redundant processing of identical images.

    Example:
        >>> engine = OCREngine(use_cache=True)
        >>> image = Image.open("screenshot.png")
        >>> result = engine.detect_text(image)
        >>> for box in result.text_boxes:
        ...     print(f"{box.text} (confidence: {box.confidence})")
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_size: int = 1000,
        lang: str = "en",
    ) -> None:
        """Initialise the OCR engine.

        Args:
            use_cache: Whether to cache OCR results.
            cache_size: Maximum number of results to cache.
            lang: Language for OCR (e.g., "en", "ch", "japan").
        """
        self._ocr = None  # Lazy-loaded
        self._lang = lang
        self._use_cache = use_cache
        self._cache: LRUCache[OCRResult] | None = None

        if use_cache:
            self._cache = LRUCache[OCRResult](max_size=cache_size)

    def detect_text(
        self,
        image: Image.Image,
        min_confidence: float = MIN_CONFIDENCE,
    ) -> OCRResult:
        """Detect text in an image.

        Args:
            image: The image to process.
            min_confidence: Minimum confidence threshold for results.

        Returns:
            OCR result with detected text boxes.
        """
        # Calculate image hash for caching
        image_hash = self._calculate_image_hash(image)

        # Check cache
        if self._use_cache and self._cache is not None:
            cached_result = self._cache.get(image_hash)
            if cached_result is not None:
                return cached_result

        # Perform OCR
        text_boxes = self._perform_ocr(image, min_confidence)

        # Concatenate all text
        full_text = " ".join(box.text for box in text_boxes)

        result = OCRResult(
            text_boxes=text_boxes,
            full_text=full_text,
            cached=False,
        )

        # Cache result
        if self._use_cache and self._cache is not None:
            self._cache.put(image_hash, result)

        return result

    def detect_text_from_array(
        self,
        image_array: np.ndarray,
        min_confidence: float = MIN_CONFIDENCE,
    ) -> OCRResult:
        """Detect text from a numpy array.

        Args:
            image_array: Image as numpy array.
            min_confidence: Minimum confidence threshold for results.

        Returns:
            OCR result with detected text boxes.
        """
        image = Image.fromarray(image_array)
        return self.detect_text(image, min_confidence)

    # clear_cache() and get_cache_stats() are inherited from CacheMixin

    # =============================================================================
    # 4. PRIVATE HELPERS & UTILITIES
    # =============================================================================\

    def _get_ocr_instance(self) -> t.Any:  # noqa: ANN401
        """Get or create PaddleOCR instance (lazy loading).

        Returns:
            PaddleOCR instance.
        """
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self._lang,
            )
        return self._ocr

    def _perform_ocr(
        self,
        image: Image.Image,
        min_confidence: float,
    ) -> list[TextBox]:
        """Perform OCR on an image.

        Args:
            image: The image to process.
            min_confidence: Minimum confidence threshold.

        Returns:
            List of detected text boxes.
        """
        ocr = self._get_ocr_instance()

        # Convert PIL image to numpy array
        img_array = np.array(image)

        # Perform OCR
        results: list[t.Any] | None = ocr.ocr(img_array)

        # Parse results
        text_boxes: list[TextBox] = []

        if results is None or len(results) == 0:
            logger.debug("No OCR results returned")
            return text_boxes

        # Check if this is PaddleX format (dictionary with rec_texts, rec_scores, rec_polys)
        if len(results) > 0 and isinstance(results[0], dict):
            result_dict = results[
                0
            ]  # Type is inferred as dict[Unknown, Unknown] from isinstance check

            # Extract texts, scores, and bounding boxes from PaddleX format
            texts = result_dict.get("rec_texts", [])
            scores = result_dict.get("rec_scores", [])
            polys = result_dict.get("rec_polys", result_dict.get("dt_polys", []))

            # Combine them into TextBox objects
            for i, (text, score) in enumerate(zip(texts, scores, strict=False)):
                if score >= min_confidence:
                    bbox = polys[i].tolist() if i < len(polys) else []
                    text_boxes.append(
                        TextBox(
                            text=str(text),
                            confidence=float(score),
                            bbox=bbox,
                        )
                    )

            return text_boxes

        # Legacy PaddleOCR format (list of [bbox, (text, confidence)])
        for line in results[0] if results[0] is not None else []:  # type: ignore[misc]
            if line is None:
                continue

            # PaddleOCR returns untyped results, so we need to extract with type: ignore
            try:
                # Try to parse the result (format may vary by PaddleOCR version)
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    bbox = line[0]
                    text_data = line[1]

                    # text_data might be a tuple of (text, confidence) or just text
                    if isinstance(text_data, (list, tuple)) and len(text_data) >= 2:
                        text = text_data[0]
                        confidence = float(text_data[1])
                    else:
                        text = str(text_data)
                        confidence = 1.0  # Default confidence

                    # Filter by confidence
                    if confidence >= min_confidence:
                        text_boxes.append(
                            TextBox(
                                text=str(text),
                                confidence=confidence,
                                bbox=list(bbox)
                                if isinstance(bbox, (list, tuple))
                                else [],
                            )
                        )
            except Exception as e:
                logger.warning("Error parsing OCR line: %s", e)

        return text_boxes

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate hash of image for caching.

        Args:
            image: The image to hash.

        Returns:
            SHA256 hash of the image data.
        """
        return hash_image(image)


# =============================================================================
# 5. UTILITY FUNCTIONS
# =============================================================================


def create_ocr_engine(
    use_cache: bool = True,
    cache_size: int = 1000,
    lang: str = "en",
) -> OCREngine:
    """Create an OCR engine instance.

    Args:
        use_cache: Whether to enable caching.
        cache_size: Maximum cache size.
        lang: Language for OCR.

    Returns:
        Configured OCR engine.
    """
    return OCREngine(use_cache=use_cache, cache_size=cache_size, lang=lang)

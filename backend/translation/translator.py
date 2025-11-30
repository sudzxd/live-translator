"""Translation engine using MarianMT with caching optimisation."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
from dataclasses import dataclass

# Note: Transformers imports are lazy-loaded to avoid startup overhead
# Project/local
from ..cache.lru_cache import LRUCache
from ..utils.caching import CacheMixin
from ..utils.hashing import create_cache_key
from ..utils.logging_config import get_logger
from ..utils.validation import is_empty_or_whitespace

logger = get_logger(__name__)


# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================


@dataclass
class TranslationResult:
    """Result of a translation operation.

    Args:
        source_text: The original text.
        translated_text: The translated text.
        source_lang: Source language code.
        target_lang: Target language code.
        cached: Whether this result was from cache.
    """

    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    cached: bool


# Common language pair model mappings
LANGUAGE_MODELS = {
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
    ("en", "ja"): "Helsinki-NLP/opus-mt-en-jap",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("ja", "en"): "Helsinki-NLP/opus-mt-jap-en",
}


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


class Translator(CacheMixin[str]):
    """Translation engine with caching and optimisation.

    This engine uses MarianMT models for translation and caches results
    to avoid redundant processing of identical text.

    Example:
        >>> translator = Translator(source_lang="en", target_lang="es")
        >>> result = translator.translate("Hello, world!")
        >>> print(result.translated_text)
        ¡Hola, mundo!
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        use_cache: bool = True,
        cache_size: int = 5000,
    ) -> None:
        """Initialise the translator.

        Args:
            source_lang: Source language code (e.g., "en").
            target_lang: Target language code (e.g., "es").
            use_cache: Whether to cache translation results.
            cache_size: Maximum number of results to cache.

        Raises:
            ValueError: If language pair is not supported.
        """
        self._source_lang = source_lang
        self._target_lang = target_lang
        self._use_cache = use_cache

        # Get model name for language pair
        lang_pair = (source_lang, target_lang)
        if lang_pair not in LANGUAGE_MODELS:
            msg = f"Unsupported language pair: {source_lang} -> {target_lang}"
            raise ValueError(msg)

        self._model_name = LANGUAGE_MODELS[lang_pair]
        self._model = None  # Lazy-loaded
        self._tokenizer = None  # Lazy-loaded

        # Initialise cache
        self._cache: LRUCache[str] | None = None
        if use_cache:
            self._cache = LRUCache[str](max_size=cache_size)

    def translate(self, text: str) -> TranslationResult:
        """Translate text from source to target language.

        Args:
            text: The text to translate.

        Returns:
            Translation result with source and translated text.
        """
        # Handle empty input
        if is_empty_or_whitespace(text):
            return TranslationResult(
                source_text=text,
                translated_text=text,
                source_lang=self._source_lang,
                target_lang=self._target_lang,
                cached=False,
            )

        # Calculate cache key
        cache_key = create_cache_key(text, self._source_lang, self._target_lang)

        # Check cache
        if self._use_cache and self._cache is not None:
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                return TranslationResult(
                    source_text=text,
                    translated_text=cached_result,
                    source_lang=self._source_lang,
                    target_lang=self._target_lang,
                    cached=True,
                )

        # Perform translation
        translated_text = self._perform_translation(text)

        # Cache result
        if self._use_cache and self._cache is not None:
            self._cache.put(cache_key, translated_text)

        return TranslationResult(
            source_text=text,
            translated_text=translated_text,
            source_lang=self._source_lang,
            target_lang=self._target_lang,
            cached=False,
        )

    def translate_batch(self, texts: list[str]) -> list[TranslationResult]:
        """Translate multiple texts in batch.

        Args:
            texts: List of texts to translate.

        Returns:
            List of translation results in same order as input.
        """
        # Pre-allocate results list to maintain order
        results: list[TranslationResult | None] = [None] * len(texts)

        # Separate cached and non-cached texts
        to_translate: list[tuple[int, str]] = []

        for i, text in enumerate(texts):
            if is_empty_or_whitespace(text):
                results[i] = TranslationResult(
                    source_text=text,
                    translated_text=text,
                    source_lang=self._source_lang,
                    target_lang=self._target_lang,
                    cached=False,
                )
                continue

            cache_key = create_cache_key(text, self._source_lang, self._target_lang)

            # Check cache
            if self._use_cache and self._cache is not None:
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    results[i] = TranslationResult(
                        source_text=text,
                        translated_text=cached_result,
                        source_lang=self._source_lang,
                        target_lang=self._target_lang,
                        cached=True,
                    )
                    continue

            # Need to translate
            to_translate.append((i, text))

        # Batch translate non-cached texts
        if to_translate:
            texts_to_process = [text for _, text in to_translate]
            translated_texts = self._perform_batch_translation(texts_to_process)

            for (idx, original_text), translated_text in zip(
                to_translate, translated_texts, strict=False
            ):
                # Cache result
                if self._use_cache and self._cache is not None:
                    cache_key = create_cache_key(
                        original_text,
                        self._source_lang,
                        self._target_lang,
                    )
                    self._cache.put(cache_key, translated_text)

                results[idx] = TranslationResult(
                    source_text=original_text,
                    translated_text=translated_text,
                    source_lang=self._source_lang,
                    target_lang=self._target_lang,
                    cached=False,
                )

        return [r for r in results if r is not None]  # type: ignore[misc]

    # clear_cache() and get_cache_stats() are inherited from CacheMixin

    # =============================================================================
    # 4. PRIVATE HELPERS & UTILITIES
    # =============================================================================

    def _load_model(self) -> None:
        """Load the translation model and tokenizer (lazy loading)."""
        if self._model is None or self._tokenizer is None:  # type: ignore[has-type]
            logger.info("Loading translation model: %s", self._model_name)
            from transformers import MarianMTModel, MarianTokenizer

            self._tokenizer = MarianTokenizer.from_pretrained(self._model_name)  # type: ignore[assignment]
            self._model = MarianMTModel.from_pretrained(self._model_name)  # type: ignore[misc]
            logger.info("Translation model loaded successfully")

    def _perform_translation(self, text: str) -> str:
        """Perform actual translation using MarianMT.

        Args:
            text: Text to translate.

        Returns:
            Translated text.
        """
        self._load_model()

        # Tokenize
        inputs = self._tokenizer(text, return_tensors="pt", padding=True)  # type: ignore[misc]

        # Translate
        translated = self._model.generate(**inputs)  # type: ignore[union-attr]

        # Decode
        translated_text: str = self._tokenizer.decode(  # type: ignore[union-attr,assignment]
            translated[0],
            skip_special_tokens=True,
        )

        return translated_text  # type: ignore[return-value]

    def _perform_batch_translation(self, texts: list[str]) -> list[str]:
        """Perform batch translation.

        Args:
            texts: List of texts to translate.

        Returns:
            List of translated texts.
        """
        self._load_model()

        # Tokenize batch
        inputs = self._tokenizer(texts, return_tensors="pt", padding=True)  # type: ignore[misc]

        # Translate
        translated = self._model.generate(**inputs)  # type: ignore[union-attr]

        # Decode all
        translated_texts: list[str] = [
            str(self._tokenizer.decode(t, skip_special_tokens=True))  # type: ignore[union-attr]
            for t in translated  # type: ignore[misc]
        ]

        return translated_texts


# =============================================================================
# 5. UTILITY FUNCTIONS
# =============================================================================


def create_translator(
    source_lang: str,
    target_lang: str,
    use_cache: bool = True,
    cache_size: int = 5000,
) -> Translator:
    """Create a translator instance.

    Args:
        source_lang: Source language code.
        target_lang: Target language code.
        use_cache: Whether to enable caching.
        cache_size: Maximum cache size.

    Returns:
        Configured translator.
    """
    return Translator(
        source_lang=source_lang,
        target_lang=target_lang,
        use_cache=use_cache,
        cache_size=cache_size,
    )


def get_supported_language_pairs() -> list[tuple[str, str]]:
    """Get list of supported language pairs.

    Returns:
        List of (source_lang, target_lang) tuples.
    """
    return list(LANGUAGE_MODELS.keys())

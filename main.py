"""Live Translator - Main application entry point.

A transparent overlay window with live OCR and translation capabilities.
"""

# =============================================================================
# 1. IMPORTS
# =============================================================================
# Standard library
import argparse
import sys

# Third-party
import webview

# Project/local
from backend.api.bridge import create_translator_api
from backend.utils.constants import (
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_X,
    DEFAULT_WINDOW_Y,
)
from backend.utils.logging_config import get_logger, setup_logging
from backend.utils.window_manager import WindowManager

logger = get_logger(__name__)


# =============================================================================
# 2. ARGUMENT PARSING
# =============================================================================
def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Live Translator - Transparent overlay with OCR and translation",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "--source-lang",
        default=DEFAULT_SOURCE_LANGUAGE,
        help=f"Source language code (default: {DEFAULT_SOURCE_LANGUAGE})",
    )
    parser.add_argument(
        "--target-lang",
        default=DEFAULT_TARGET_LANGUAGE,
        help=f"Target language code (default: {DEFAULT_TARGET_LANGUAGE})",
    )
    return parser.parse_args()


# =============================================================================
# 3. MAIN ENTRY POINT
# =============================================================================
def main() -> None:
    """Run the Live Translator application."""
    args = parse_arguments()
    setup_logging(verbose=args.verbose)

    logger.info("Starting Live Translator")
    logger.info("Translation: %s -> %s", args.source_lang, args.target_lang)

    try:
        # Create API bridge without window reference (will be set later)
        api = create_translator_api(
            window=None,  # Will be set after window creation
            source_lang=args.source_lang,
            target_lang=args.target_lang,
        )

        # Create the window with the API attached
        window_manager = WindowManager()
        window_manager.create_window(
            width=DEFAULT_WINDOW_WIDTH,
            height=DEFAULT_WINDOW_HEIGHT,
            x=DEFAULT_WINDOW_X,
            y=DEFAULT_WINDOW_Y,
            js_api=api,
        )

        # Get the window instance and set it on the API
        window = window_manager.get_window()
        if window is None:
            logger.error("Failed to create window")
            sys.exit(1)

        api.set_window(window)

        logger.info("Glass window created successfully")
        logger.info("API bridge initialised")
        logger.info("Application ready - move window over text to translate")

        # Start the application event loop
        webview.start(debug=args.verbose)

    except Exception as e:
        logger.exception("Failed to start application: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

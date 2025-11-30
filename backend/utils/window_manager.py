"""Window manager for glass-like transparent overlay window."""

# =============================================================================
# 1. IMPORTS
# =============================================================================
# Standard library
from pathlib import Path

# Third-party
import webview

# Project/local
from .constants import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_X,
    DEFAULT_WINDOW_Y,
)
from .logging_config import get_logger

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================
class WindowManager:
    """Manages the transparent glass overlay window.

    Example:
        >>> manager = WindowManager()
        >>> manager.create_window(width=800, height=600)
        >>> manager.show()
    """

    def __init__(self) -> None:
        """Initialise the window manager."""
        self._window: webview.Window | None = None

    def create_window(
        self,
        width: int = DEFAULT_WINDOW_WIDTH,
        height: int = DEFAULT_WINDOW_HEIGHT,
        x: int = DEFAULT_WINDOW_X,
        y: int = DEFAULT_WINDOW_Y,
        js_api: object | None = None,
    ) -> None:
        """Create the transparent glass window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            x: Window X position.
            y: Window Y position.
            js_api: Optional API object to expose to JavaScript.
        """
        logger.info("Creating glass window: %dx%d at (%d, %d)", width, height, x, y)

        # Get path to frontend HTML
        html_path = self._get_html_path()

        # Create window
        self._window = webview.create_window(  # type: ignore[misc]
            title="Live Translator",
            url=html_path,
            width=width,
            height=height,
            x=x,
            y=y,
            resizable=True,
            frameless=True,  # Frameless for clean glass effect
            easy_drag=True,  # Allow dragging from anywhere
            on_top=True,
            transparent=True,
            js_api=js_api,
        )
        logger.debug("Glass window created successfully")

    def show(self) -> None:
        """Show the window and start the event loop."""
        if self._window is None:
            msg = "Window not created. Call create_window() first."
            raise RuntimeError(msg)

        webview.start(debug=False)

    def get_window(self) -> webview.Window | None:
        """Get the window instance.

        Returns:
            The window instance or None if not created.
        """
        return self._window

    # =============================================================================
    # 4. PRIVATE HELPERS & UTILITIES
    # =============================================================================
    def _get_html_path(self) -> str:
        """Get the path to the frontend HTML file.

        Returns:
            Absolute path to index.html.
        """
        # Get project root (3 levels up from this file)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent

        html_path = project_root / "frontend" / "index.html"

        if not html_path.exists():
            msg = f"Frontend HTML not found at {html_path}"
            raise FileNotFoundError(msg)

        return str(html_path.absolute())


# =============================================================================
# 5. UTILITY FUNCTIONS
# =============================================================================
def create_glass_window(
    width: int = DEFAULT_WINDOW_WIDTH,
    height: int = DEFAULT_WINDOW_HEIGHT,
    x: int = DEFAULT_WINDOW_X,
    y: int = DEFAULT_WINDOW_Y,
) -> WindowManager:
    """Create and configure a glass window.

    Args:
        width: Window width in pixels.
        height: Window height in pixels.
        x: Window X position.
        y: Window Y position.

    Returns:
        Configured window manager.
    """
    manager = WindowManager()
    manager.create_window(width=width, height=height, x=x, y=y)
    return manager

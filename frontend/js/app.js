/**
 * Live Translator Frontend
 *
 * Handles communication with Python backend and displays translations.
 */

// Global state
let isProcessing = false;

/**
 * Initialise the application
 */
function init() {
  console.log("Live Translator initialising...");
  console.log("pywebview available:", typeof pywebview !== "undefined");

  if (typeof pywebview !== "undefined") {
    console.log(
      "pywebview.api available:",
      typeof pywebview.api !== "undefined"
    );
    if (typeof pywebview.api !== "undefined") {
      console.log("API methods:", Object.keys(pywebview.api));
    }
  }

  // Ensure background transparency
  document.documentElement.style.background = "transparent";
  document.body.style.background = "transparent";

  // Apply frosted effect only when dragging
  const glassWindow = document.getElementById("glass-window");
  let isDragging = false;

  document.body.addEventListener("mousedown", () => {
    isDragging = true;
    if (glassWindow) {
      glassWindow.classList.add("dragging");
    }
  });

  document.body.addEventListener("mouseup", () => {
    isDragging = false;
    if (glassWindow) {
      glassWindow.classList.remove("dragging");
    }
  });

  // Also remove dragging class if mouse leaves window
  document.body.addEventListener("mouseleave", () => {
    if (isDragging && glassWindow) {
      glassWindow.classList.remove("dragging");
    }
    isDragging = false;
  });

  // Wait for pywebview to be ready
  window.addEventListener("pywebviewready", () => {
    console.log("pywebview ready event fired");
    startProcessing();
  });

  // Fallback: try starting after a delay if event doesn't fire
  setTimeout(() => {
    if (
      !isProcessing &&
      typeof pywebview !== "undefined" &&
      typeof pywebview.api !== "undefined"
    ) {
      console.log("Fallback: starting processing after timeout");
      startProcessing();
    } else {
      console.log(
        "Fallback check - isProcessing:",
        isProcessing,
        "pywebview:",
        typeof pywebview,
        "api:",
        typeof pywebview !== "undefined" ? typeof pywebview.api : "N/A"
      );
    }
  }, 2000);
}

/**
 * Start the OCR and translation processing
 */
async function startProcessing() {
  if (isProcessing) {
    return;
  }

  try {
    const result = await pywebview.api.start_processing();
    console.log("Processing started:", result);
    isProcessing = true;

    // Start polling for results
    pollForUpdates();
  } catch (error) {
    console.error("Failed to start processing:", error);
  }
}

/**
 * Poll for translation updates
 */
async function pollForUpdates() {
  // Disabled - using push updates from backend instead
  // Polling was causing excessive re-rendering
}

/**
 * Update translations (called from Python)
 */
window.updateTranslations = async function () {
  try {
    const results = await pywebview.api.get_latest_results();
    displayTranslations(results);
  } catch (error) {
    console.error("Failed to update translations:", error);
  }
};

/**
 * Display translations in the UI as positioned overlays
 */
function displayTranslations(results) {
  const container = document.getElementById("translations-container");

  // Always clear first to remove old translations
  container.innerHTML = "";

  if (!results || results.length === 0) {
    return;
  }

  results.forEach((item) => {
    // Skip low confidence or non-Spanish text
    if (item.confidence < 0.7) return;

    // Skip if translation is same as original (likely not Spanish)
    if (item.original.trim() === item.translated.trim()) return;

    // Get bounding box coordinates
    // bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    const bbox = item.bbox;
    if (!bbox || bbox.length < 4) return;

    // Calculate position and size from bounding box
    const x = Math.min(bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0]);
    const y = Math.min(bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1]);
    const width = Math.max(bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0]) - x;
    const height = Math.max(bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1]) - y;

    // Create positioned overlay box
    const div = document.createElement("div");
    div.className = "translation-overlay";
    div.style.left = `${x}px`;
    div.style.top = `${y}px`;
    div.style.width = `${width}px`;
    div.style.height = `${height}px`;

    const textDiv = document.createElement("div");
    textDiv.className = "translation-text";
    textDiv.textContent = item.translated;
    div.appendChild(textDiv);

    // Temporarily add to DOM to measure
    container.appendChild(div);

    // Calculate font size based on bounding box height
    let fontSize = Math.max(8, Math.floor(height * 0.7));
    div.style.fontSize = `${fontSize}px`;
    div.style.lineHeight = `${height}px`;

    // Reduce font size if text doesn't fit horizontally
    const availableWidth = width - 8; // Account for padding
    while (fontSize > 6 && textDiv.scrollWidth > availableWidth) {
      fontSize--;
      div.style.fontSize = `${fontSize}px`;
    }

    console.log(
      `Overlay: "${item.translated}" at (${x}, ${y}), size: ${width}x${height}, fontSize: ${fontSize}px, original: "${item.original}"`
    );
  });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Initialise when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

# Live Translator

A transparent overlay window with live OCR and translation capabilities. Drag and resize the glass-like window over any content to automatically detect and translate text in real-time.

## Features

- **Transparent Glass UI**: iOS-like transparent, draggable, and resizable window
- **Live OCR**: Real-time text detection using PaddleOCR
- **Local Translation**: Privacy-focused translation using MarianMT (runs locally)
- **Optimised Performance**: Smart caching, dirty region tracking, and efficient processing
- **Cross-platform**: Built with Python and web technologies

## Architecture

- **Frontend**: HTML/CSS/JavaScript with glass morphism UI
- **Backend**: Python with optimised processing pipeline
- **OCR**: PaddleOCR with region-based detection
- **Translation**: MarianMT (Hugging Face Transformers)
- **Window**: pywebview for native window management

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install dependencies
uv sync --dev

# Download translation models (first run)
# Models will be downloaded automatically on first use
```

## Development

### Project Structure

```
live-translator/
├── backend/
│   ├── ocr/          # PaddleOCR integration
│   ├── translation/  # MarianMT translation
│   ├── capture/      # Screen capture with optimisation
│   ├── cache/        # LRU cache and optimisations
│   └── utils/        # Utility functions
├── frontend/
│   ├── css/          # Glass UI styles
│   └── js/           # Window interaction logic
└── scripts/          # Development scripts
```

### Development Scripts

```bash
# Format code
./scripts/format.sh

# Lint code
./scripts/lint.sh

# Type check
./scripts/typecheck.sh

# Run tests
./scripts/test.sh

# Run all checks
./scripts/check-all.sh
```

### Code Style

This project follows strict code quality standards:

- **PEP 8** compliance enforced by ruff
- **88 character** line limit
- **British English** spelling throughout
- **Google-style** docstrings
- **Strict type checking** with Pyright/Pylance
- **Type-safe data structures** (dataclasses over dicts)

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed conventions.

## Optimisation Techniques

### Performance Features

1. **LRU Caching**: Translation results and OCR outputs are cached
2. **Dirty Region Tracking**: Only process changed screen regions
3. **Batch Processing**: Multiple text regions processed together
4. **Adaptive Frame Rate**: Reduces capture rate when idle
5. **Spatial Indexing**: Efficient text region management

### Data Structures

- **LRU Cache**: For translation and OCR memoisation
- **Spatial Hash Map**: For region change detection
- **Deque**: For frame buffer management

## Usage

```bash
# Run the application
uv run python main.py
```

## Licence

TBD

## Contributing

Contributions are welcome! Please ensure:

2. Code is formatted (`./scripts/format.sh`)
3. Type checking passes (`./scripts/typecheck.sh`)
4. Follow the style guide

# Project Style Guide

This document outlines the coding style and conventions for this project. All contributors and tools (including GitHub Copilot) must adhere to these standards.

---

## General Coding Standards

### PEP 8 Compliance

We use ruff to enforce PEP compliance throughout the codebase and expect all code to adhere to the following standards:

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines for Python code.

### Line Width

- Maximum line width: **88 characters**.
- Use consistent line breaks to maintain readability.

### Indentation

- Use **4 spaces** per indentation level.
- Do not use tabs.

### Spelling Convention

- Use **British English** spellings throughout the codebase.
- Examples of preferred spellings:
  - `colour` not `color`
  - `behaviour` not `behavior`
  - `realise` not `realize`
  - `organise` not `organize`
  - `favour` not `favor`
  - `honour` not `honor`
  - `labour` not `labor`
  - `neighbour` not `neighbor`
  - `flavour` not `flavor`
  - `centre` not `center`
  - `defence` not `defense`
  - `licence` (noun) / `license` (verb)
  - `practise` (verb) / `practice` (noun)

---

## Docstring Style

### General Docstring Guidelines

- All functions, classes, and modules must have docstrings.
- Use **Google-style** docstrings for documentation.

### Google-Style Docstring Example

```python
def example_function(arg1: int, arg2: str) -> bool:
    """Performs an example operation.

    Args:
        arg1: Description of the first argument.
        arg2: Description of the second argument.

    Returns:
        Description of the return value.
    """
    pass
```

There's no need to include type-hints again in the docstring, as they are already present in the function signature. Do not repeat yourself! The function signature is authoritative.

---

## Type Hints

### Use Primitive Types Where Available

- Use primitive types (`list`, `dict`, `tuple`, `set`) instead of their `typing` module equivalents when the Python version supports it.
- Prefer `list[str]` over `t.List[str]` (Python 3.9+)
- Prefer `dict[str, int]` over `t.Dict[str, int]` (Python 3.9+)
- Prefer `tuple[str, int]` over `t.Tuple[str, int]` (Python 3.9+)

**Good:**

```python
def process_data(items: list[str]) -> dict[str, int]:
    """Process list of items and return counts."""
    return {item: len(item) for item in items}
```

**Avoid:**

```python
import typing as t

def process_data(items: t.List[str]) -> t.Dict[str, int]:
    """Process list of items and return counts."""
    return {item: len(item) for item in items}
```

### Exception: Use `typing` for Complex Types

Continue using `typing` module for complex type constructs that don't have primitive equivalents:

- `t.Optional[str]` (no primitive equivalent)
- `t.Union[str, int]` (no primitive equivalent)
- `t.Any` (no primitive equivalent)
- `t.Callable[[str], bool]` (no primitive equivalent)

---

## Type Safety and Data Structures

### Never Work with Raw Dictionaries in Application Logic

**Rule: Always use typed dataclasses or Pydantic models instead of raw dictionaries for application data.**

Working with raw dictionaries (`dict[str, Any]`) in application logic is not type-safe and should be avoided. Use strongly-typed dataclasses or Pydantic models to ensure:

- Type checking catches errors at development time
- IDE autocomplete and refactoring support
- Clear contracts between components
- Self-documenting code

**Good:**

```python
from dataclasses import dataclass

@dataclass
class UserConfig:
    name: str
    email: str
    age: int

def process_user(user: UserConfig) -> None:
    """Process user configuration with type safety."""
    print(f"{user.name} - {user.email}")  # Type-checked, autocomplete works
```

**Avoid:**

```python
def process_user(user: dict[str, Any]) -> None:
    """Process user configuration without type safety."""
    print(f"{user['name']} - {user['email']}")  # No type checking, typos not caught
```

### Exception: Serialization Boundaries Only

Raw dictionaries are acceptable **only** at serialization boundaries:

- Reading from JSON files
- Deserializing from HTTP requests
- Storing in webview stores
- Writing to databases (when using raw queries)

Immediately convert to typed models after deserialization and before passing to application logic:

```python
import dataclasses
from dataclasses import dataclass
import typing as t

@dataclass
class Config:
    name: str
    value: int

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> "Config":
        """Convert from dict at deserialization boundary."""
        return cls(name=data["name"], value=data["value"])

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to dict at serialization boundary."""
        return dataclasses.asdict(self)

# Usage example:
def handle_config(config_data: dict[str, t.Any] | None) -> dict[str, t.Any]:
    """Handle configuration with type safety internally."""
    # Convert from dict immediately
    config = Config.from_dict(config_data) if config_data else Config(name="", value=0)

    # Work with typed model
    config.value += 1

    # Convert to dict at boundary
    return config.to_dict()
```

---

## Test Naming Conventions

- Test function names must be descriptive and use lowercase with underscores.
- Test names should clearly state the scenario and expected outcome.
- Use the following pattern for test names:

  ```
  test_<unit_of_work>_<scenario>_should_<expected_result>
  ```

  **Examples:**

  - `test_translation_cache_with_existing_key_should_return_cached_value`
  - `test_ocr_engine_with_invalid_image_should_raise_error`
  - `test_screen_capture_dirty_region_only_changed_areas_should_be_captured`

- Avoid generic names like `test_something` or `test_case1`.
- The test name should make it clear what is being tested and what the expected behaviour is.

---

## Module Organisation

### Domain-Driven Module Structure

All modules should follow a consistent organisation that prioritises the "need-to-know" principle. Sections are ordered from most important (public API) to least important (implementation details).

#### Recommended Section Order

```python
"""Module docstring describing domain responsibility."""

# =============================================================================
# 1. IMPORTS
# =============================================================================
# Standard library
import json
import typing as t
from dataclasses import dataclass

# Third-party
from PIL import Image
from transformers import MarianMTModel, MarianTokenizer

# Project/local
from ..cache.lru_cache import LRUCache
from ..types import TranslationResult

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================
@dataclass
class DomainSpecificModel:
    """Domain model for this module."""
    field1: str
    field2: int

# Module-level constants
DEFAULT_CACHE_SIZE = 1000
TRANSLATION_TIMEOUT = 5.0

# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Main entry point - public API for this domain module."""
    return _perform_translation(text, source_lang, target_lang)

# =============================================================================
# 4. CORE LOGIC & COMPONENTS
# =============================================================================
def _perform_translation(text: str, source: str, target: str) -> str:
    """Core translation logic."""
    pass

# =============================================================================
# 5. PRIVATE HELPERS & UTILITIES
# =============================================================================
def _preprocess_text(input_text: str) -> str:
    """Private helper function."""
    pass
```

#### Rationale

- **Need-to-know**: Readers see the module's interface immediately
- **API-driven**: Public functions define what the module does
- **Top-down reading**: Start with high-level concepts, drill down to implementation
- **Maintainability**: Easy to identify what can be refactored vs what's part of the public contract
- **Consistency**: Same pattern across all domain modules

---

## Performance Guidelines

### Optimisation Principles

1. **Measure First**: Always profile before optimising
2. **Cache Intelligently**: Use LRU caches for expensive operations
3. **Batch Operations**: Process multiple items together when possible
4. **Use Appropriate Data Structures**: Choose the right DS for the problem
5. **Avoid Premature Optimisation**: Write clear code first, optimise hotspots later

### Common Patterns

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_operation(param: str) -> str:
    """Use built-in LRU cache for pure functions."""
    pass

# For class methods, use custom cache implementation
class Translator:
    """Translation engine with custom caching."""

    def __init__(self) -> None:
        """Initialise translator with cache."""
        self._cache: dict[str, str] = {}

    def translate(self, text: str) -> str:
        """Translate with caching."""
        if text in self._cache:
            return self._cache[text]

        result = self._do_translation(text)
        self._cache[text] = result
        return result
```

---

## Git Commit Convention

- Use clear, descriptive commit messages
- Follow the format: `<type>: <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Use British English in commit messages

**Examples:**

- `feat: add LRU cache for translation results`
- `fix: correct OCR region detection boundary calculation`
- `refactor: optimise screen capture performance`
- `docs: update style guide with performance guidelines`

---

## Questions?

If you're unsure about any style conventions, check this guide first. When in doubt, follow PEP 8 and prioritise readability and type safety.

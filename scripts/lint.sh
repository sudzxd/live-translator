#!/usr/bin/env bash
# Lint the codebase with ruff

set -e

echo "Running ruff linter..."
uv run ruff check backend/ tests/

echo "Linting complete!"

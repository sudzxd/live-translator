#!/usr/bin/env bash
# Format the codebase with ruff

set -e

echo "Formatting code with ruff..."
uv run ruff format backend/ tests/
uv run ruff check --fix backend/ tests/

echo "Formatting complete!"

#!/usr/bin/env bash
# Type check the codebase with pyright

set -e

echo "Running pyright type checker..."
uv run pyright

echo "Type checking complete!"

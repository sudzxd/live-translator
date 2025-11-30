#!/usr/bin/env bash
# Run all checks: format, lint, typecheck, test

set -e

echo "Running all checks..."
echo ""

./scripts/format.sh
echo ""

./scripts/lint.sh
echo ""

./scripts/typecheck.sh
echo ""

./scripts/test.sh
echo ""

echo "✅ All checks passed!"

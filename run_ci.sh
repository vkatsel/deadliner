#!/usr/bin/env bash
set -euo pipefail

echo "==> Running Pytest..."
pytest tests/

echo "==> Running Ruff Linter..."
ruff check src/ tests/

echo "==> Running Ruff Formatter (dry-run)..."
ruff format --check src/ tests/

echo "==> CI PASS!"

#!/usr/bin/env bash
# Clean unnecessary build/runtime artifacts from the workspace.
# Safe to run anytime; recreates needed temp dirs lazily when pipeline runs.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[clean] Root: $ROOT_DIR"

# Remove __pycache__ directories
echo "[clean] Removing Python __pycache__ directories..."
find backend -type d -name '__pycache__' -prune -exec rm -rf {} + || true

# Remove temp render outputs
if [ -d temp ]; then
  echo "[clean] Purging temp/ directory contents..."
  rm -rf temp/* || true
fi

# Remove stray top-level final video artifact if present
if [ -f final_video.mp4 ]; then
  echo "[clean] Removing stray final_video.mp4"
  rm -f final_video.mp4 || true
fi

# Remove common macOS metadata files
echo "[clean] Removing .DS_Store files..."
find . -name '.DS_Store' -type f -delete || true

# Optional: prune node_modules cache artifacts (keep node_modules itself)
find frontend/node_modules -type f -name '*.log' -delete 2>/dev/null || true

echo "[clean] Done."

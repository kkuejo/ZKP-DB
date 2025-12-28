#!/usr/bin/env bash
set -euo pipefail

# Build provider and purchaser apps and stage them under gh-pages/provider and gh-pages/purchaser
# so you can push the gh-pages branch for GitHub Pages hosting.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building provider app..."
npm --prefix "$ROOT_DIR/frontend/provider-app" run build

echo "Building purchaser app..."
npm --prefix "$ROOT_DIR/frontend/purchaser-app" run build

STAGE_DIR="$ROOT_DIR/gh-pages"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/provider" "$STAGE_DIR/purchaser"

echo "Copying provider dist -> gh-pages/provider"
cp -R "$ROOT_DIR/frontend/provider-app/dist/." "$STAGE_DIR/provider/"

echo "Copying purchaser dist -> gh-pages/purchaser"
cp -R "$ROOT_DIR/frontend/purchaser-app/dist/." "$STAGE_DIR/purchaser/"

echo "Done. Commit/push gh-pages directory to the gh-pages branch and enable Pages."

#!/usr/bin/env sh
# Build the static workbench that Vercel serves alongside src.app's FastAPI function.
set -eu

(cd frontend && npm ci && npm run build)
rm -rf public
mkdir -p public
cp -R frontend/dist/. public/

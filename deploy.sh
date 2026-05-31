#!/usr/bin/env bash
# Build the CSS and deploy the static marketing site to the muros.org server.
set -euo pipefail

SERVER="${MUROS_SITE_SERVER:-152.228.128.167}"
TARGET="${MUROS_SITE_TARGET:-/opt/muros/site}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Render the docs to static HTML, then compile the stylesheet.
npm run build

ssh "$SERVER" "mkdir -p $TARGET"
rsync -az --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'src' \
  --exclude 'build_docs.py' \
  --exclude 'deploy.sh' \
  --exclude 'README.md' \
  --exclude 'package.json' \
  --exclude 'package-lock.json' \
  --exclude 'tailwind.config.js' \
  --exclude '.gitignore' \
  "$HERE"/ "$SERVER:$TARGET/"
ssh "$SERVER" "chown -R root:root $TARGET"

echo "Deployed to $SERVER:$TARGET"

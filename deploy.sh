#!/usr/bin/env bash
set -euo pipefail

SERVER="${MUROS_SITE_SERVER:-debian@10.10.10.10}"
SSH_OPTS="${MUROS_SSH_OPTS:--J proxmox}"
SITE_TARGET="${MUROS_SITE_TARGET:-/opt/muros/site}"
DOWNLOAD_TARGET="${MUROS_DOWNLOAD_TARGET:-/opt/muros/download}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

npm run build

SSH="ssh $SSH_OPTS"

$SSH "$SERVER" "sudo mkdir -p $SITE_TARGET"
rsync -az -e "$SSH" --rsync-path="sudo rsync" --delete \
  --exclude '.git' --exclude 'node_modules' --exclude 'src' \
  --exclude 'build_docs.py' --exclude 'deploy.sh' --exclude 'README.md' \
  --exclude 'package.json' --exclude 'package-lock.json' \
  --exclude 'tailwind.config.js' --exclude '.gitignore' --exclude 'download' \
  "$HERE"/ "$SERVER:$SITE_TARGET/"

$SSH "$SERVER" "sudo mkdir -p $DOWNLOAD_TARGET/assets"
rsync -az -e "$SSH" --rsync-path="sudo rsync" \
  "$HERE"/assets/ "$SERVER:$DOWNLOAD_TARGET/assets/"
rsync -az -e "$SSH" --rsync-path="sudo rsync" \
  "$HERE"/download/index.html "$HERE"/download/robots.txt "$SERVER:$DOWNLOAD_TARGET/"

echo "Deployed muros.org -> $SERVER:$SITE_TARGET"
echo "Deployed download.muros.org landing -> $SERVER:$DOWNLOAD_TARGET"

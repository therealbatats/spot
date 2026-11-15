#!/usr/bin/env bash
# SPOT - commit and republish the site folder to GitHub Pages (branch gh-pages).
# Written with AI assistance under the direction of Ali (team AITHMAC).
set -euo pipefail
cd "$(dirname "$0")"
git add -A
git commit -q -m "${1:-Update SPOT}" || true
for i in 1 2 3; do git push -q origin main && break; sleep 5; done
git branch -D gh-pages >/dev/null 2>&1 || true
git subtree split -q --prefix site -b gh-pages
for i in 1 2 3; do git push -q -f origin gh-pages && break; sleep 5; done
echo "pushed $(git rev-parse --short HEAD) at $(date +%H:%M)"

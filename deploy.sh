#!/usr/bin/env bash
# SPOT - publish to GitHub Pages. Written with AI assistance under the direction of Ali (team AITHMAC).
# Requires: `gh auth login` done. Creates a PUBLIC repo named $REPO (default "spot"), pushes main,
# publishes the site/ folder on branch gh-pages, and turns on GitHub Pages for that branch.
set -euo pipefail
REPO="${1:-spot}"
cd "$(dirname "$0")"
USER="$(gh api user --jq .login)"
ID="$(gh api user --jq .id)"
git config user.email "${ID}+${USER}@users.noreply.github.com"   # GitHub's private no-reply address
git add -A
git commit -q -m "${COMMIT_MSG:-Update SPOT}" || true
# make every local commit carry the real no-reply author address (history is local-only before first push)
if ! git ls-remote --exit-code origin >/dev/null 2>&1; then
  git -c user.email="${ID}+${USER}@users.noreply.github.com" rebase -q --root --exec "git commit -q --amend --no-edit --reset-author" || true
fi
if ! gh repo view "$USER/$REPO" >/dev/null 2>&1; then
  gh repo create "$REPO" --public --description "SPOT — Sky Patches Over Time: blink real NASA SPHEREx infrared images of any patch of sky (NASA Space Apps 2026, Planet X and SPHEREx)" --source . --remote origin
fi
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$USER/$REPO.git"
git push -u origin main
git branch -D gh-pages >/dev/null 2>&1 || true
git subtree split --prefix site -b gh-pages
git push -f origin gh-pages
gh api -X POST "repos/$USER/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null 2>&1 || \
gh api -X PUT "repos/$USER/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null
echo "Repo:  https://github.com/$USER/$REPO"
echo "Site:  https://$USER.github.io/$REPO/"

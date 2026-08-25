#!/usr/bin/env bash
# Mint the per-repo mirror credentials (ADR 0004): for each repo of the drive
# subgroup, an ed25519 keypair whose PUBLIC half becomes a write deploy key on
# github.com/aity-cloud/drive-<repo> and whose PRIVATE half becomes the
# protected file variable GITHUB_MIRROR_KEY on gitlab.com/aity-cloud/drive/<repo>.
# Nothing is written to disk outside a private temp dir that is shredded.
#
# Needs: gh (github.com, org owner or repo admin on aity-cloud), glab
# (maintainer on the subgroup), ssh-keygen. The GitHub org must have deploy
# keys enabled (org setting deploy_keys_enabled_for_repositories).
#
# Usage: scripts/mint-mirror-keys.sh [repo...]   (default: meta android ios desktop)
# Re-running for a repo rotates its key: old deploy key + variable are replaced.
set -euo pipefail
REPOS=("$@"); [ ${#REPOS[@]} -gt 0 ] || REPOS=(meta android ios desktop)
WORK=$(mktemp -d /tmp/mirror-keys.XXXXXX); chmod 700 "$WORK"; trap 'cd /; find "$WORK" -type f -exec shred -u {} +; rm -rf "$WORK"' EXIT
cd "$WORK"
for R in "${REPOS[@]}"; do
  TITLE="gitlab.com CI push mirror (aity-cloud/drive/$R)"
  ssh-keygen -q -t ed25519 -N '' -C "gitlab-ci-mirror:aity-cloud/drive/$R" -f "$R"
  # rotate: drop a previous key of the same title
  for ID in $(gh api "repos/aity-cloud/drive-$R/keys" --jq ".[] | select(.title==\"$TITLE\") | .id"); do
    gh api -X DELETE "repos/aity-cloud/drive-$R/keys/$ID" >/dev/null && echo "  drive-$R: removed old deploy key $ID"
  done
  gh api -X POST "repos/aity-cloud/drive-$R/keys" -f title="$TITLE" -f key="$(cat "$R.pub")" -F read_only=false \
    --jq '"  drive-'"$R"': deploy key \(.id) read_only=\(.read_only)"'
  # glab variable set is the supported way in (glab api cannot POST JSON and
  # its stored OAuth token is not a PRIVATE-TOKEN, so curl gets 401).
  # Rotation = delete + set; delete is allowed to fail on first mint.
  glab variable delete GITHUB_MIRROR_KEY -R "aity-cloud/drive/$R" >/dev/null 2>&1 && VERB=rotated || VERB=created
  glab variable set GITHUB_MIRROR_KEY -R "aity-cloud/drive/$R" --type file --protected --raw < "$R" >/dev/null
  echo "  drive/$R: GITHUB_MIRROR_KEY $VERB (file, protected)"
  shred -u "$R" "$R.pub"
done
echo "done: push to main (or a tag) in each repo now runs mirror:github"

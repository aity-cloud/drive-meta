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
  python3 - "$R" > payload.json <<'PY'
import sys, json
r = sys.argv[1]
print(json.dumps({"key": "GITHUB_MIRROR_KEY", "variable_type": "file", "protected": True, "masked": False, "raw": True,
  "description": "ed25519 private key; write deploy key on github.com/aity-cloud/drive-%s; read only by ci/mirror.yml" % r,
  "value": open(r).read()}))
PY
  # glab api cannot POST a JSON body (--input is sent with the wrong content
  # type -> 415) and exits 0 on a 404, so the variables API is called with curl.
  TOKEN=${GITLAB_TOKEN:-$(glab config get token --host gitlab.com)}
  API="https://gitlab.com/api/v4/projects/aity-cloud%2Fdrive%2F$R/variables"
  CODE=$(curl -s -o /dev/null -w '%{http_code}' -H "PRIVATE-TOKEN: $TOKEN" "$API/GITHUB_MIRROR_KEY")
  if [ "$CODE" = "200" ]; then METHOD=PUT; URL="$API/GITHUB_MIRROR_KEY"; VERB=rotated; else METHOD=POST; URL="$API"; VERB=created; fi
  curl -sf -X "$METHOD" -H "PRIVATE-TOKEN: $TOKEN" -H 'Content-Type: application/json' --data @payload.json "$URL" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print('  drive/$R: GITHUB_MIRROR_KEY $VERB (type=%s protected=%s)'%(d['variable_type'],d['protected']))"
  shred -u "$R" "$R.pub" payload.json
done
echo "done: push to main (or a tag) in each repo now runs mirror:github"

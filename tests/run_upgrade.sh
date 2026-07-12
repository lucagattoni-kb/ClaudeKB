#!/usr/bin/env bash
# Upgrade test (spec §12.2 + §14e): scaffold a fixture from the latest release
# tag, `copier update` it to HEAD, rebuild the wheel from src/, and assert zero
# conflicts + a green gate. Bootstrap: skipped with a notice until the first tag.
set -euo pipefail

BP="$(cd "$(dirname "$0")/.." && pwd)"
COPIER="copier==9.16.0"

LATEST_TAG="$(git -C "$BP" tag --list 'v*' --sort=-version:refname | head -1 || true)"
if [ -z "$LATEST_TAG" ]; then
  echo "no release tag yet — upgrade test skipped (bootstrap, §12.2). Mandatory from v1.0.0."
  exit 0
fi

HEAD_SHA="$(git -C "$BP" rev-parse HEAD)"
WORK="$(mktemp -d)"; FX="$WORK/kb-up"
trap 'rm -rf "$WORK"' EXIT

echo "== scaffold fixture from $LATEST_TAG"
uvx "$COPIER" copy --defaults --vcs-ref "$LATEST_TAG" \
  -d kb_name=upfix -d kb_title="Upgrade Fixture" -d kb_description="Upgrade CI fixture." \
  "$BP" "$FX"
# Commit the fixture faithful to the release tag (NO sync-dir here — that would
# diverge it from the tag's base and force a spurious copier-update conflict).
git -C "$FX" init -q -b main
git -C "$FX" config user.email ci@claudekb.local
git -C "$FX" config user.name "ClaudeKB CI"
git -C "$FX" add -A
git -C "$FX" commit -qm scaffold

echo "== copier update $LATEST_TAG -> HEAD ($HEAD_SHA)"
( cd "$FX" && uvx "$COPIER" update --defaults --vcs-ref "$HEAD_SHA" )
if git -C "$FX" grep -q '^<<<<<<<' -- . 2>/dev/null; then
  echo "FAIL: conflict markers after upgrade"; exit 1
fi

echo "== rebuild wheel from src/ + gate"
python3 "$BP/scripts/release.py" --sync-dir "$FX"
git -C "$FX" add -A
git -C "$FX" commit -qm "post-update" || true
( cd "$FX" && uv lock -q && uv sync -q && uv run kbtool check && uv run kbtool build )
echo "UPGRADE OK"

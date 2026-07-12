#!/usr/bin/env bash
# End-to-end blueprint test (spec §12.1 + §14 a/e). Scaffolds a fixture KB from
# the committed HEAD, rebuilds the wheel from src/ into it, and runs the full
# gate. Also asserts a no-op `copier update` produces zero conflicts (§14e).
#
# Usage: tests/run_e2e.sh   (run from the blueprint repo root; tree must be clean-committed)
set -euo pipefail

BP="$(cd "$(dirname "$0")/.." && pwd)"
COPIER="copier==9.16.0"
REF="$(git -C "$BP" rev-parse HEAD)"
WORK="$(mktemp -d)"
FX="$WORK/kb-fixture"
trap 'rm -rf "$WORK"' EXIT

echo "== scaffold fixture from $REF"
uvx "$COPIER" copy --defaults --vcs-ref "$REF" \
  -d kb_name=fixture -d kb_title="Fixture KB" -d kb_description="CI fixture." \
  "$BP" "$FX"

echo "== rebuild wheel from src/ into fixture (§12.1)"
python3 "$BP/scripts/release.py" --sync-dir "$FX"

echo "== init git + sync"
git -C "$FX" init -q -b main
git -C "$FX" config user.email ci@claudekb.local
git -C "$FX" config user.name "ClaudeKB CI"
git -C "$FX" add -A
git -C "$FX" commit -qm scaffold
( cd "$FX" && uv lock -q && uv sync -q )

echo "== kbtool check + build (green scaffold, F4.5)"
( cd "$FX" && uv run kbtool check && uv run kbtool build )

echo "== add a real content page, re-gate"
mkdir -p "$FX/docs/concepts"
cat > "$FX/docs/concepts/alpha.md" <<'EOF'
---
type: concept
title: Alpha
description: A first real content page.
tags: [fixture]
status: published
---

# Alpha

Prose linking [home](/index.md) and a diagram.

```mermaid
graph TD
  A --> B
```
EOF
# link it from index so it isn't an orphan; add to nav via a glob section
python3 - "$FX" <<'PY'
import sys, pathlib
fx = pathlib.Path(sys.argv[1])
idx = fx / "docs/index.md"
idx.write_text(idx.read_text() + "\n- [Alpha](/concepts/alpha.md)\n")
nav = fx / "nav.yml"
nav.write_text(nav.read_text().replace(
    "  - Change log: log.md",
    '  - Concepts: {glob: "concepts/**.md"}\n  - Change log: log.md'))
PY
( cd "$FX" && git add -A && git commit -qm "add page" \
    && uv run kbtool check && uv run kbtool build )

echo "== parallel log.md appends via union driver (§14d, E3)"
(
  cd "$FX"
  git checkout -q -b sessionA
  printf '\n## 20260712 10:00 ingest | Session A\nA body.\n' >> docs/log.md
  git commit -qam "A"
  git checkout -q main
  printf '\n## 20260712 10:01 ingest | Session B\nB body.\n' >> docs/log.md
  git commit -qam "B"
  git merge -q --no-edit sessionA
  grep -q "Session A" docs/log.md && grep -q "Session B" docs/log.md \
    || { echo "FAIL: a concurrent append was lost"; exit 1; }
  git checkout -q -- . 2>/dev/null || true
)

echo "== no-op copier update → zero conflicts (§14e)"
( cd "$FX" && git checkout -q main && uvx "$COPIER" update --defaults --vcs-ref "$REF" )
if git -C "$FX" grep -q '^<<<<<<<' -- . 2>/dev/null; then
  echo "FAIL: conflict markers after no-op update"; exit 1
fi
echo "E2E OK"

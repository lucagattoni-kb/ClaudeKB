# ClaudeKB (blueprint repo)

**Blueprint repository** for a fleet of 10+ independent, content-agnostic,
docs-as-code knowledge bases — one repo per KB, AI agents as primary
readers/writers via direct git commits. This repo is **not** a KB: it scaffolds
new self-sufficient KB repos and upgrades existing ones (REQUIREMENTS.md §4).

## Canonical context

Read `docs/architecture.md` (the implementation spec) and `REQUIREMENTS.md`
(decisions D1–D18) before any structural change. Do not re-litigate settled
decisions; surface, don't silently resolve, anything genuinely open.

## Working principles

- Prefer **structural guarantees over conventions**; verify empirically.
- Strict gate: frontmatter schema, link/orphan checks, lint, boundary
  checksums — `kbtool check` fails on errors.
- Design for parallel agent writes (git-native, log.md union merge).
- Keep future extensions in mind without building them: unified cross-KB
  search, MCP/RAG retrieval, offline reading.

## Layout

- `src/kbtool/` — the ONLY home of the KB toolchain source (D15). Built to a
  wheel, vendored into each KB. `data/` holds package data (playbooks,
  `site-base.yml`, `frontmatter.schema.json`, `pymarkdown.json`).
- `template/` — the copier template. `.jinja` files are rendered; everything
  else is copied verbatim. `template/vendor/` holds the built wheel;
  `template/blueprint-checksums.json` is generated.
- `playbooks/scaffold-kb.md` — the pre-KB procedure. All other playbooks ship
  inside kbtool (`uv run kbtool playbook <name>`).
- `scripts/release.py` — builds the wheel into the template + regenerates
  checksums. Blueprint-side only (never a kbtool command — D15 anti-whitewash).
- `tests/` — unit tests + the e2e/upgrade harnesses CI runs.

## Working rules

- **After changing `src/kbtool/` or any `template/` static file, run
  `python scripts/release.py`** to rebuild the vendored wheel and regenerate
  checksums; commit the result. CI `--check` (on tags) enforces sync.
- **Verify before committing**: `bash tests/run_e2e.sh` plus
  `uv run --with pytest pytest tests/`.
- **Cross-KB conventions are the public API** (D18): URL scheme, `kb://`
  resolution, `kb.yml` format. Changing any is a MAJOR release + migration.
- **Release** (spec §12.3): finalize CHANGELOG (timestamped `YYYYMMDD HH:MM`,
  breaking/non-breaking separated) → bump `__version__` in
  `src/kbtool/__init__.py` → `python scripts/release.py` → commit → tag
  `vX.Y.Z` → push commit + tag.
- Every change on a timestamped branch/worktree, never a primary checkout
  (user's global rules).

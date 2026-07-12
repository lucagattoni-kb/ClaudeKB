# Changelog

All notable changes to the ClaudeKB blueprint. Format: Keep a Changelog;
Semantic Versioning. Entries timestamped `YYYYMMDD HH:MM` (local).

## [Unreleased]

(nothing yet)

## [0.1.1] - 20260712 16:54

Post-launch fix from KB #1 (kb-sandbox) going live. The live E4 checklist all
passed (private-by-default, `/public` bypass precedence, workers.dev lockdown,
private search index), but surfaced one design gap.

### Fixed

- **Public pages rendered unstyled for anonymous readers.** A `/public`-only
  Access bypass leaves the theme's CSS/JS (served at `/assets/`) behind Access.
  The scaffold/access playbook now adds a third **Bypass app on `/assets`**
  (theme-only namespace — safe; `/search.json` and sitemap stay private, so no
  KB content leaks), and `kb.yml`'s `platform.access_apps` records it.
- **KB media relocated `docs/assets/` → `docs/media/`.** Otherwise the
  wholesale `/assets` bypass would expose images embedded on *private* pages.
  Theme keeps `/assets/` (public); KB media at `/media/` stays private.
  Documented limitation: public pages get text/code/**Mermaid** (renders from
  the now-public JS) but **not** embedded raster images. CLAUDE.md, the ingest
  playbook, and spec §5.5/§5.6/§10.6 updated.

### Verified live (KB #1, resolves the deferred infra assumptions)

- `uv` **is** preinstalled in the Workers Builds image — no installer prepend
  needed; auto-detected, `uv sync` + `uv run kbtool ci` ran clean.
- Full deploy pipeline works untouched: Workers Builds → `kbtool ci` →
  `wrangler deploy` → auto-created custom domain `kb-sandbox.example.com`.
- Access precedence: the `/public` path app wins over the hostname app;
  `workers.dev` does not resolve; the search index requires login.

## [0.1.0] - 20260712 12:44

### Added (non-breaking)

- Initial blueprint implementation (spec `docs/architecture.md`, decisions
  D1–D18):
  - `kbtool` toolchain (source in `src/kbtool/`, D15): `check`, `build`,
    `serve`, `ci`, `push`, `status`, `playbook`.
  - Validators (spec §6.1): frontmatter schema + per-KB vocabulary, intra-KB
    link resolution + `kb://` syntax, index reachability (anti-orphan), log
    append-only, nav coverage, slug-consistency triple, boundary checksums,
    PyMarkdown lint.
  - Preprocessor (spec §6.2): `kb://` and root-absolute link rewriting to
    final URL paths (SSG-independent), git-derived date footers with a
    shallow-clone guard, nav glob expansion, generated `mkdocs.yml`.
  - copier template (`template/`) producing a self-sufficient KB; kbtool
    vendored as a built wheel (D15); playbooks shipped in-package (D16); the
    `platform:` record in `kb.yml` (D17).
  - `scripts/release.py` (wheel build + checksum manifest, blueprint-side only)
    and blueprint CI (`.github/workflows/ci.yml`) with scaffold, upgrade, and
    unit-test jobs.

### Notes / spec deviations resolved during implementation (`[verify-at-impl]`)

- **Wheel filename**: uv rejects a renamed `kbtool.whl` ("must have a version"),
  so the vendored wheel keeps its canonical `kbtool-<ver>-py3-none-any.whl`
  name. `copier update` deletes the old-versioned wheel and adds the new one
  cleanly (verified), so upgrades don't orphan stale wheels.
- **Zensical** honors `docs_dir`/`site_dir` overrides and renders
  frontmatter-less `index.md`/`log.md` correctly (verified via build).
- **Root-absolute link rewrite** targets the final URL path (e.g.
  `/concepts/alpha/`), not a relative path — simplest form that is correct on
  any SSG.
- **PyMarkdown MD025** ("multiple top-level headings") conflicts with our
  deliberate frontmatter-`title` + body-`# H1` convention and is disabled
  (along with MD013 line-length). Remaining rules are active.

### Still unverified (need live infra — deferred to KB #1 launch)

- Cloudflare Access `/public` bypass precedence, `workers.dev` lockdown,
  wildcard-vs-per-KB app consolidation (spec §10.6c live checklist).
- `uv` availability in the Workers Builds image (spec §7); installer-prepend
  fallback documented in `playbooks/scaffold-kb.md`.
- `wrangler deployments list` output parsing for `kbtool status` (spec §7).

# KB agent contract (blueprint-owned)

This file is blueprint-owned and identical across every KB; it is overwritten
on `copier update` and its checksum is enforced. **Do not edit it.** KB-specific
guidance lives in `@CLAUDE-KB.md`.

## Session ritual

**At the start of every session:**

1. Read `docs/index.md` (the catalog) and the tail of `docs/log.md`.
2. Run `uv run kbtool status` — catches a red deploy left by a prior session.
3. Run `uv run kbtool check` — catches a dirty inherited tree.
4. Fix any red state before starting new work.

**Before ending a session that changed content:**

1. Update `docs/index.md` if pages were added, moved, or removed.
2. Append a `docs/log.md` entry (see format below).
3. `uv run kbtool check` — must pass.
4. Commit, then `uv run kbtool push`.

## Conventions

- **Frontmatter** (required on every page except `index.md`/`log.md`):
  `type` (must be in `vocab.yml`), `title`, `description`. Optional, validated:
  `tags` (each in `vocab.yml`), `status` (draft|review|published|archived).
  No date fields — dates come from git history at build time.

  ```yaml
  ---
  type: article
  title: Example Page
  description: One sentence describing the page.
  tags: [example]
  status: published
  ---
  ```

- **Links.** Within this KB, bundle-root-absolute Markdown:
  `[Alpha](/concepts/alpha.md)`. To another KB: `[X](kb://other-kb/path.md)`.
  Images under `docs/media/<page-path>/…`, referenced root-absolute
  (`/media/…`). Do **not** put content under `docs/assets/` — that path is
  reserved for the theme and is world-readable (see the public/private note).

- **log.md** is append-only. One entry per change:

  ```markdown
  ## 20260712 14:30 ingest | Added /concepts/alpha.md
  Short summary of what changed and why.
  ```

- **Public/private.** Only `docs/public/**` is world-readable. Two consequences
  of the shared site build (a split build is the backlog fix):
  - The global nav exposes *page titles* to anonymous readers, so **private
    page titles must not themselves be sensitive.**
  - Public pages render with the theme (CSS/JS at `/assets/`, world-readable)
    and Mermaid diagrams work, but **embedded raster images do not show for
    anonymous readers** — KB media lives at `/media/` and stays private. Use
    Mermaid, text, and code for public content.

- **Ownership.** Do not edit blueprint-owned files (anything with a
  `MANAGED BY BLUEPRINT` marker, plus `vendor/`, `.gitattributes`,
  `.gitignore`, this file). `kbtool check` rejects edits to them.

## Commands

- `uv run kbtool check` — all validators (the deploy gate).
- `uv run kbtool build` — check, preprocess, build the site.
- `uv run kbtool serve` — local preview.
- `uv run kbtool push` — rebase-retry push.
- `uv run kbtool status` — deploy result + working-tree state.
- `uv run kbtool playbook <ingest|lint|upgrade|access-dns-setup>` — procedures.

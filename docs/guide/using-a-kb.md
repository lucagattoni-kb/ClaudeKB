# Using a KB

Day-to-day, a KB is written by an agent (or you) via direct commits to `main`.
The KB's own `CLAUDE.md` is the contract every agent session follows; this page
summarizes it.

## The session ritual

**Start of a session:**

1. Read `docs/index.md` (the catalog) and the tail of `docs/log.md`.
2. `uv run kbtool status` — surfaces a red deploy left by a previous session.
3. `uv run kbtool check` — surfaces a dirty inherited tree.
4. Fix any red state before new work.

**Before ending a session that changed content:**

1. Update `docs/index.md` if pages were added, moved, or removed.
2. Append a `docs/log.md` entry.
3. `uv run kbtool check` — must pass.
4. Commit, then `uv run kbtool push`.

## Writing content

- Pages are Markdown under `docs/`. Every page (except `index.md`/`log.md`)
  needs frontmatter:

  ```yaml
  ---
  type: article          # must be listed in vocab.yml
  title: Example Page
  description: One sentence describing the page.
  tags: [example]        # optional; each must be in vocab.yml
  status: published      # optional: draft | review | published | archived
  ---
  ```

  No date fields — dates come from git history automatically.

- **Every page must be reachable from `docs/index.md`** (directly or via a
  linked page) and **appear in `nav.yml`** (explicitly or via a glob section).
  Orphans fail the gate — this is what keeps a large corpus navigable.

- **Links.** Within the KB: bundle-root-absolute, `[X](/concepts/x.md)`. To
  another KB: `[X](kb://other-kb/page.md)` — resolved to a real URL at build.
  Images under `docs/media/<page>/…`, referenced `/media/…`.

- **Vocabulary.** `type` and `tags` are validated against `vocab.yml`. Add new
  terms there deliberately — the curated list is what prevents tag sprawl.

## Public vs private

Only `docs/public/**` is world-readable. Two things to know:

- The global navigation exposes **page titles** to anonymous readers, so don't
  put secrets in private page titles.
- Public pages render with the theme and **Mermaid diagrams**, but **embedded
  raster images do not show** for anonymous readers (media stays private). Use
  Mermaid, text, and code for public content.

## The change log

`docs/log.md` is append-only and merge-safe (a git union driver), so two
parallel sessions can both append without conflicting. One entry per change:

```markdown
## 20260712 14:30 ingest | Added /concepts/alpha.md
Short note on what changed and why.
```

Never edit earlier entries — `kbtool check` rejects a non-append-only log.

## Commands

| Command | Does |
|---|---|
| `uv run kbtool check` | Run all validators (the deploy gate) |
| `uv run kbtool build` | Check, preprocess, build the site |
| `uv run kbtool serve` | Local live preview |
| `uv run kbtool push` | Rebase-retry push (safe under parallel writes) |
| `uv run kbtool status` | Last deploy result + working-tree state |
| `uv run kbtool playbook <ingest\|lint\|upgrade\|access-dns-setup>` | Print a procedure |

## Maintenance

Periodically (e.g. monthly), run `uv run kbtool playbook lint` — a structural
pass (`kbtool check` + external-link sweep) plus a semantic pass (contradictions,
staleness, missing cross-references). This is how an agent-written KB stays
healthy over time.

Next: [Upgrading KBs](upgrading.md).

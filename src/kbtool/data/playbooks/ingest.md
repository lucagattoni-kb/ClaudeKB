# Playbook: ingest (add knowledge to this KB)

Version-matched to the installed kbtool. See `CLAUDE-KB.md` for this KB's
page types and vocabulary.

1. **Decide create vs extend.** Prefer extending an existing page when the
   knowledge belongs to an existing concept; create a new page for a distinct
   concept. `CLAUDE-KB.md` defines the page types.
2. **Write the page** under `docs/` with required frontmatter — `type`
   (must be in `vocab.yml` types), `title`, `description`. Optional: `tags`
   (each in `vocab.yml` tags), `status`.
   - Links to other pages in this KB: bundle-root-absolute, e.g.
     `/concepts/alpha.md`.
   - Links to another KB: `kb://<kb-name>/<path>.md`.
   - Images: put under `docs/media/<page-path>/…`, reference root-absolute
     (`/media/…`). Not `docs/assets/` — that path is theme-only and public.
     Note images do not render on public pages for anonymous readers.
   - Do **not** add date fields — dates come from git history at build time.
3. **Link it from `docs/index.md`** (directly or via a page already reachable
   from the index) — orphan pages fail `kbtool check`.
4. **Add it to `nav.yml`** — explicitly, or ensure a `{glob: …}` section
   already covers it. A page in neither fails the build.
5. **Append a `docs/log.md` entry**:
   `## <YYYYMMDD HH:MM> ingest | <one-line summary>` followed by a short body.
   Never edit earlier log entries — the log is append-only.
6. `uv run kbtool check` — fix every error.
7. Commit, then `uv run kbtool push`.

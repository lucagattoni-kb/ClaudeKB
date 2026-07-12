# Launch retrospective — adversarial pass over the whole project

> 20260712, after KB #1 (kb-sandbox) went live and the docs/GH-metadata work.
> A fresh, skeptical review of the blueprint code, the live KB, the spec, and
> the docs — testing rather than trusting. Findings ranked; fixes in v0.1.2.

## Method

Attacked from six angles: kbtool correctness (edge cases run empirically),
security/boundary, live-site behaviour (re-probed), spec-vs-implementation-vs-docs
consistency, decision soundness given what launch taught us, and failure modes.

## Findings

### R1 — `kbtool status` red-deploy detection was a no-op locally [MEDIUM] — FIXED

The session-start ritual relies on `kbtool status` to catch a red deploy left
by a prior session (F7.2 — a HIGH finding in the original spec review). The
implementation shelled out to `wrangler deployments list`, which needs
Cloudflare credentials. **Claude Code agents run `gh`-authenticated, not
`wrangler`-authenticated**, so in practice `status` always degraded to
"unknown" — the feature never actually worked in an agent session.

Verified empirically that the Workers Builds result IS exposed, with no
Cloudflare creds, via the GitHub check-runs API:
`gh api repos/<owner>/<repo>/commits/<sha>/check-runs` →
`{name: "Workers Builds: kb-sandbox", conclusion: "success"}`.

Fix: `status` now reads that API first (filtering the
`cloudflare-workers-and-pages` app), falling back to `wrangler`, then a
dashboard nudge. Red-deploy detection now works on the path agents use.

### R2 — preprocessor corrupts links whose text equals the URL [LOW] — FIXED

`_rewrite_links` used `whole.replace(target, new, 1)`, which replaces the first
occurrence in the whole `[text](url)` match. When an author writes
`[/concepts/alpha.md](/concepts/alpha.md)` (visible text == URL), the **text**
was rewritten and the URL left with a dead `.md`. Normal links (text ≠ URL)
were unaffected, which is why it slipped through. Fix: replace only the URL by
its regex-group span. Regression test added.

### R3 — the ownership-boundary checksum is drift-detection, not tamper-proof [LOW] — ACCEPTED, wording tightened

`blueprint-checksums.json` is itself KB-writable, so an agent that edits a
blueprint-owned file *and* regenerates the manifest passes `kbtool check`. The
check reliably catches **accidental** drift (edit a file, forget the manifest),
and the real backstop is the `copier update` conflict that divergence causes
(E2). It is not a security control against a determined editor. Docs/spec that
said "machine-enforced" now note it catches drift with copier-update as the
backstop. Not worth hardening further for a solo, agent-following-CLAUDE.md
threat model.

## Checked and found sound (no change)

- **Live KB** re-probed: `/`→302, `/public/`→200, `/search.json`→302 — still
  correct after the v0.1.1 upgrade.
- **Validators** on edge cases: malformed YAML frontmatter, missing/extra
  fields, kb:// with fragments, deleted seeded files (caught by nav/reachability),
  boundary file missing — all handled.
- **Upgrade machinery**: the real v0.1.0→v0.1.1 fleet upgrade was clean,
  including a directory relocation.
- **Decisions**: nothing launch taught us invalidates D1–D18. The Workers
  Builds deploy model (D5) proved *more* secure than a token-based alternative
  (no managed credential in the deploy path), reinforcing the roadmap decision
  to defer `kbtool provision`.

## Known limitations restated (documented, not bugs)

- Public pages leak private page *titles* via the global nav; public pages
  can't show private raster images. Both trace to the single shared build; the
  split-build backlog item is the real fix.
- `wrangler.jsonc` `compatibility_date` is a fixed date stamped at release, not
  the per-KB scaffold date — functionally harmless (any valid past date works).
- Redirect-on-page-move is manual (`docs/_redirects`); not auto-generated.

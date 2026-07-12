# Antora — analysis for ClaudeKB

> Research doc. Analyzed 20260712 from official docs. Confidence: medium-high;
> not run hands-on (and likely won't be — its lessons matter more than its
> adoption).

## What it is

The multi-repository documentation site generator (AsciiDoc, Node.js).
A central **playbook** repo defines the site; content is pulled by Antora's
built-in git client from any number of repos/branches/tags, organized as
**components** (logical doc units) with **versions** (from git refs).
The canonical answer to "many repos, one docs site" — i.e., a working
implementation of the *aggregation* side of ClaudeKB's future unified layer.

## Mechanics that matter for ClaudeKB

- **Component model**: each repo contributes a named component; pages address
  each other by **resource ID** (`version@component:module:page.adoc`), not
  by URL or filesystem path.
- **Source-to-source references**: xrefs are written against the content
  model and resolved at build time; the site can be re-rooted/republished
  without breaking internal links.
- **Nav is per-component** (curated files listing pages), aggregated by the
  playbook.
- Link validation across components: not explicitly guaranteed by the docs —
  build-time resolution catches dangling xrefs in practice, but we could not
  confirm a hard cross-repo validation promise.

## Findings

- **F5.1 — Stable IDs beat stable URLs.** Antora's core lesson: when content
  addresses content by *logical ID* resolved at build time, hosting scheme
  and file moves stop breaking links. ClaudeKB's cross-KB links are currently
  planned as raw URLs (`kb-<name>.example.com/...`) — fine for v1, but
  the blueprint should reserve a logical form (e.g. `kb://<kb-name>/<path>`
  or OKF-style bundle-absolute with a KB prefix) that a build step resolves
  to URLs. Then a future URL-scheme change is a resolver change, not a
  content migration. Cheap to reserve now, expensive to retrofit.
- **F5.2 — Aggregation-time architecture validates "design for unified
  search, don't build it".** Antora shows the aggregator can be a *separate
  consumer* of N content repos, added later without changing them — provided
  content is addressable and self-describing (frontmatter, stable IDs). Our
  per-KB independence (D3/D4) doesn't foreclose an Antora-style central
  builder over all KBs later.
- **F5.3 — Version-per-component is the one Antora concept to explicitly NOT
  adopt.** KB knowledge is living content with git history, not versioned
  releases; importing docs-style versioning would add cost with no reader
  benefit. (Blueprint *tooling* is versioned — that's copier's job, doc 04.)
- **F5.4 — Per-component curated nav files** (component owns its nav; site
  aggregates) match our hybrid-nav requirement and give the blueprint a
  clean KB-owned artifact: `nav.yml` (or equivalent) is KB-owned, consumed by
  blueprint-owned site config — a concrete instance of the F4.2 file split.

## Adopt / adapt / avoid

- **Adopt**: logical cross-KB link form reserved in conventions (F5.1);
  KB-owned nav file consumed by blueprint-owned config (F5.4).
- **Adapt**: aggregator-as-separate-consumer as the future unified-search
  shape (F5.2).
- **Avoid**: adopting Antora itself (AsciiDoc + Node against our
  Markdown + Python constraints); component versioning (F5.3).

## Gaps / next loop

- None blocking; revisit F5.2 when the unified layer is designed.

## Sources

- https://docs.antora.org/antora/latest/features/
- https://docs.antora.org/antora/latest/organize-content-files/
- https://antora.org/

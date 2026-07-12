# Zensical & the MkDocs ecosystem collapse — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: high on ecosystem facts (multiple
> independent sources), medium on Zensical maturity claims (vendor's own docs,
> not yet tested hands-on).

## Why this doc exists

`REQUIREMENTS.md` D9 set MkDocs Material as the default SSG, with the research
phase instructed to try to falsify it. **It is falsified in its original form.**
The MkDocs ecosystem fractured between late 2025 and early 2026; picking "MkDocs
Material" today means picking a maintenance-mode theme on top of an unmaintained
core. The real decision is now between successors.

## The situation (verified 20260712)

- **MkDocs 1.x is unmaintained**: no meaningful release since 1.6.1 (Aug 2024);
  issues/PRs accumulate; community discussions openly question maintenance.
- **"MkDocs 2.0"** is a ground-up rewrite under new maintainership that is
  hostile to the existing ecosystem: no plugin system, TOML config replacing
  `mkdocs.yml`, navigation passed as pre-rendered HTML (killing theme-level
  customization), contributions discouraged, **no license specified** at the
  time of writing. A March 2026 PyPI ownership transfer incident temporarily
  removed maintainer access. Treat as radioactive.
- **Material for MkDocs is in maintenance mode**: critical bug/security fixes
  only, guaranteed "for at least 12 months" (from ~Feb 2026). Pinned to
  `mkdocs<2`.
- **Zensical** (MIT, by the Material for MkDocs team, announced 2025-11-05) is
  the designated successor: reads `mkdocs.yml` unchanged, same HTML output so
  existing CSS/JS customizations carry over, Rust differential build engine
  (4–5x faster rebuilds), built-in "Disco" search engine with excerpts,
  Mermaid out of the box, tags/blog/versioning/social-cards/offline listed as
  supported on the official feature-parity page. Plugins are NOT compatible; a
  new "module system" replaces them (rollout began early 2026).
- **Community forks** exist as conservative alternatives: `mkdocs-ng`
  (maintained fork of MkDocs 1.7 line, drop-in, keeps `mkdocs` CLI),
  `ProperDocs` (1.x continuation), `MaterialX` (Material theme continuation).
- **Momentum signal**: Backstage has an open RFC (issue #33990) to adopt
  Zensical as the next TechDocs engine. If that lands, Zensical inherits the
  largest institutional docs-as-code user base.

## Findings

- **F1.1 — The "boring default" no longer exists.** Every option now carries
  risk: Zensical (young, plugin story immature), pinned MkDocs Material
  (12-month fuse), forks (small maintainer teams, unproven longevity),
  ecosystem exit to Sphinx/Hugo/Starlight (abandons Python-native preference
  or Material UX).
- **F1.2 — Zensical's compatibility posture fits our blueprint model.** It
  consumes `mkdocs.yml` and emits Material-compatible HTML, so a blueprint
  that starts on pinned MkDocs Material can migrate KBs to Zensical via a
  blueprint upgrade — this is exactly the scenario the blueprint's
  upgrade+migration machinery (§4 of REQUIREMENTS) exists for.
- **F1.3 — Plugin dependency is the real risk surface.** Whatever we need
  beyond core (frontmatter validation, git-derived dates, redirects) should
  live in **our own uv-run scripts outside the SSG**, not as SSG plugins.
  The collapse punished projects glued to the plugin ecosystem; validators
  that run standalone survive any SSG swap. This hardens REQUIREMENTS D5
  (gates as standalone scripts) into a survival property, not just a
  concurrency choice.
- **F1.4 — SSG choice must be encapsulated as a blueprint implementation
  detail.** KB content (Markdown + frontmatter) and validation must not
  depend on SSG specifics; nav config and theme are blueprint-owned files.
  Then the SSG is swappable per blueprint release. The one leak to watch:
  Markdown flavor (Python-Markdown extensions vs CommonMark — Zensical plans
  a CommonMark move; avoid exotic pymdownx syntax in content conventions).
- **F1.5 — git-derived dates need a plan B.** The established
  `mkdocs-git-revision-date-localized` plugin is exactly the category Zensical
  breaks (F1.3): D6's "dates from git" must be implemented as our own build
  step (script emitting a data file consumed by templates/macros) rather than
  that plugin, or it blocks a future Zensical migration.

## Adopt / adapt / avoid

- **Candidate A (recommended for hands-on test): pinned MkDocs Material now,
  Zensical migration as a planned blueprint upgrade.** Battle-tested feature
  set for KB #1; migration path officially supported and gets ~a year of
  runway. Cost: known-EOL start.
- **Candidate B: Zensical from day one.** Cleanest long-term bet; young module
  system, some parity gaps. Cost: risk of hitting a missing feature mid-build.
- **Avoid**: MkDocs 2.0 (governance, license); building anything on MkDocs
  plugins we don't control (F1.3).
- **Test empirically before deciding** (next loop): scaffold the same toy KB
  on both A and B; compare build, search quality, Mermaid, offline output,
  nav config, theming hooks, build time in Workers Builds.

## Gaps / next loop

- Hands-on parity check (above) — the feature-parity page is vendor-authored.
- Zensical versioning: "versioning supported" — verify what that means without
  `mike` (which is MkDocs-specific).
- License/gov check of Disco search index format (matters for future unified
  cross-KB search: can we merge per-KB indexes?).

## Sources

- https://squidfunk.github.io/mkdocs-material/blog/2025/11/05/zensical/
- https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/
- https://fpgmaas.com/blog/collapse-of-mkdocs/
- https://zensical.org/compatibility/features/
- https://github.com/mkdocs-ng/mkdocs · https://github.com/orgs/ProperDocs/discussions/33
- https://github.com/backstage/backstage/issues/33990

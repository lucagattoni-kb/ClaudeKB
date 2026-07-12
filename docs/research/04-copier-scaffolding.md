# Copier (vs cruft/cookiecutter) — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: high on comparison facts
> (copier's own docs + independent posts); update-conflict behavior needs
> hands-on verification.

## Why this doc exists

Open question 1 (scaffold/upgrade mechanism) names "copier/cruft class"
tooling as a candidate. This doc evaluates that class for the blueprint's two
functions: **scaffold** new KB repos and **upgrade** existing ones.

## The landscape

- **cookiecutter**: mature, ubiquitous, **generation-time only** — no update
  story. Ruled out alone.
- **cruft**: bolts update tracking onto cookiecutter (`.cruft.json` records
  template source + commit + answers; diffs template changes onto projects).
  Works, but is a shim over a tool that wasn't designed for lifecycle.
- **copier** (Python, uv-installable): scaffolding **and lifecycle**. Tracks
  template version + answers in `.copier-answers.yml`; `copier update` does
  smart diffs between template git tags; supports **migrations** (scripts run
  when crossing version boundaries) — neither competitor has this; YAML-only
  config; conditional file inclusion; task hooks. Actively positioned (2026)
  as the platform-team pattern: versioned templates, updates propagate.

## Findings

- **F4.1 — Copier's model is a 1:1 match for the blueprint's §4 design
  consequences.** Version tracking → `.copier-answers.yml` (machine-readable
  manifest, already specified by §4). Migrations for breaking changes →
  copier migrations (versioned, scripted — can invoke uv-run Python or
  Claude Code playbooks). Semver template releases → copier's git-tag-based
  updates. We'd be implementing §4 *with* the tool instead of building it.
- **F4.2 — The ownership boundary (open Q2) maps to template design, not a
  separate manifest.** Blueprint-owned files live in the template and get
  regenerated on update; KB-owned paths (content/, nav curation, local
  overrides) are simply *not in the template* or are excluded/skip-if-exists.
  Copier's exclusion and `_skip_if_exists` mechanics express the boundary
  declaratively. Open design question that remains ours: files that are
  *mixed* (e.g. mkdocs.yml carrying blueprint config + KB nav) — must be
  split into blueprint-owned base + KB-owned include so no file has two
  owners. **That splitting principle is the real content of open Q2.**
- **F4.3 — Update conflicts are the weak spot to verify.** Docs don't fully
  specify conflict behavior when a KB locally modified a blueprint-owned file
  (3-way merge? overwrite? .rej files?). Hands-on test required: scaffold →
  diverge → template change → `copier update` — observe. The answer shapes
  how strictly we must forbid KB-side edits of blueprint-owned files
  (convention vs structural guarantee, e.g. CI check that blueprint-owned
  files match the template version's checksums — that check would itself be a
  strong "boundary is machine-readable" enforcement).
- **F4.4 — Claude Code playbooks and copier are complements, not rivals.**
  Copier handles deterministic file mechanics; content migrations (e.g.
  frontmatter schema change across hundreds of articles) are agent work.
  Blueprint upgrade = `copier update` (mechanics) + agent-executed playbook
  shipped by the blueprint release (content). The hybrid predicted by open
  Q1 has a concrete shape now.
- **F4.5 — Blueprint repo layout consequence**: the blueprint repo becomes a
  copier template (template dir + `copier.yml` + migrations/ + playbooks/ +
  its own CI testing scaffold-and-upgrade against a fixture KB). "Blueprint
  CI tests the scaffold" is the structural guarantee that upgrades don't
  break KBs.

## Adopt / adapt / avoid

- **Adopt**: copier as the scaffold/upgrade engine (pending F4.3 hands-on
  verification); `.copier-answers.yml` as the §4 manifest.
- **Adapt**: two-layer upgrades (copier mechanics + agent playbooks, F4.4);
  split mixed-ownership files (F4.2).
- **Avoid**: cruft/cookiecutter (strictly dominated here); hand-rolled
  git-remote merge scheme (rebuilds copier badly).

## Gaps / next loop

- F4.3 conflict-behavior experiment.
- Check copier's answer-file frontmatter vs our repo naming; template tag
  discipline (semver tags = blueprint releases).

## Sources

- https://copier.readthedocs.io/en/stable/comparisons/
- https://github.com/cruft/cruft · https://cruft.github.io/cruft/
- https://www.blenddata.nl/en/blogs/cruft-vs-copier-automating-template-updates-at-scale

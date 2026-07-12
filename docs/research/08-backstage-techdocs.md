# Backstage TechDocs — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: medium — from architecture docs
> and the Zensical RFC; not run hands-on (running Backstage is out of scope).

## What it is

Spotify/CNCF Backstage's "docs-like-code" subsystem: each software component's
repo carries its own MkDocs docs; CI builds them to static HTML into central
cloud storage; the Backstage portal serves and indexes all of them. The
largest-scale institutional implementation of **"N independent repos, each
self-building its docs, aggregated by a thin central layer"** — structurally
the closest system to ClaudeKB's 10+ KB fleet + future unified layer.

## Mechanics that matter for ClaudeKB

- **Per-repo autonomy**: a repo owns `mkdocs.yml` + `docs/`; the platform owns
  the build recipe (standard container/action), storage layout, and serving.
- **Recommended deployment**: docs built in each repo's CI pipeline → static
  files pushed to object storage keyed by entity ID; portal fetches from
  storage. Build and serve are fully decoupled.
- **Central metadata registry**: every entity is described by a small YAML
  manifest (`catalog-info.yaml`) the portal consumes — the fleet is
  discoverable because each member self-describes in a standard format.
- **Engine risk response**: TechDocs is built on MkDocs and is currently
  running an RFC (#33990) to move to Zensical — an institutional confirmation
  of doc 01's analysis and of the value of keeping the SSG swappable (F1.4).

## Findings

- **F8.1 — The fleet needs a registry; make it distributed-then-aggregated.**
  Backstage centralizes fleet metadata in per-repo manifests + a portal that
  reads them. ClaudeKB equivalent: each KB carries a small blueprint-owned
  manifest (name, blueprint version — already required by §4 — plus URL,
  visibility, description). A future fleet index/unified search then *reads*
  manifests instead of hardcoding a KB list. Add to the blueprint now (file
  format only, no consumer yet) — this is the "design for, don't build"
  hook for both future extensions.
- **F8.2 — Standardized build recipe as platform-owned artifact.** TechDocs
  repos don't invent their build; they invoke the platform's. Maps exactly to
  our blueprint-owned Workers Builds config + uv-run validator entry point
  (single `build` command the KB never edits). Reinforces F4.2's split.
- **F8.3 — Build-to-storage decoupling is the future unified-hosting shape,
  not v1.** Our v1 (per-KB Worker serving its own static output) is simpler
  and free; if per-KB Workers ever become limiting (file caps, unified
  search), TechDocs' pattern — builds push to R2, thin portal serves — is
  the known-good evolution. Record as an architecture note, build nothing.
- **F8.4 — Even platform teams with dedicated staff got burned by SSG
  coupling** (MkDocs → Zensical RFC). Our F1.3/F1.4 mitigations (validators
  outside the SSG, SSG as blueprint implementation detail) are the right
  insurance at 1/1000th the scale.

## Adopt / adapt / avoid

- **Adopt**: per-KB manifest file, blueprint-owned schema (F8.1); single
  platform-owned build entry point (F8.2).
- **Adapt**: R2-based decoupled serving as a documented future path (F8.3).
- **Avoid**: running Backstage or any central portal service now — a portal
  is a *consumer* we can add later precisely because manifests exist.

## Gaps / next loop

- Watch RFC #33990 for Zensical adoption signal strength before our SSG
  checkpoint decision.

## Sources

- https://backstage.io/docs/features/techdocs/architecture/
- https://github.com/backstage/backstage/issues/33990

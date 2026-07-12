# Quartz — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: medium — based on docs/search
> results, not hands-on; v5 recently shipped and specifics may have moved.

## What it is

jackyzha0's batteries-included SSG (TypeScript/Node) purpose-built for
publishing personal knowledge gardens, usually from Obsidian vaults. Actively
maintained (v4 → v5 in 2026). The most popular "personal KB as a website"
tool — i.e., the closest existing product to what a single ClaudeKB *reads
like*, even though its stack (TS) and authoring model (human/Obsidian-first)
differ from ours.

## Mechanics that matter for ClaudeKB

- Obsidian-compatible: `[[wikilinks]]`, transclusion, backlinks, graph view,
  popover previews on hover.
- Full-text search out of the box; LaTeX; syntax highlighting; i18n.
- Plugin pipeline in TypeScript (transformers/filters/emitters) — e.g.
  frontmatter handling is just a transformer.
- Single-repo, single-site model; no multi-repo story; no access control
  (public gardens).

## Findings

- **F6.1 — Quartz defines the reader-UX bar for a personal KB.** Backlinks,
  hover previews, and graph-adjacent navigation are what make a KB *feel*
  like a knowledge web rather than a docs site. MkDocs-Material/Zensical
  don't do backlinks/previews natively. Decision input: do we accept
  docs-site UX for v1 (cheap), or does the blueprint add a backlinks build
  step (our own script emitting per-page backlink lists — SSG-agnostic per
  F1.3)? Backlinks data is trivially derivable from the link graph we already
  need for link validation, so the validator can emit it nearly for free.
- **F6.2 — Wikilink ergonomics drove Quartz's adoption; we can get the
  ergonomics without the syntax.** Quartz inherits Obsidian's `[[page]]`
  culture (human-friendly, path-free). Our writers are agents (F3.5): keep
  standard links, but have the KB-CLAUDE.md instruct agents to link via
  bundle-root-absolute paths, and let the link validator suggest targets on
  near-misses. Re-evaluate only if agent link error rates prove high.
- **F6.3 — Confirms the "content-agnostic personal KB" niche is real but
  human-centric.** Nothing in the digital-garden world handles: enforced
  schemas, CI gates, multi-KB fleets, private/public split, or agent
  workflows. ClaudeKB isn't reinventing an existing OSS wheel — the
  differentiators are exactly the parts we're designing. (Also the reason
  adopting Quartz itself was rejected: TS stack, no schema enforcement, no
  multi-repo blueprint story, no access control.)

## Adopt / adapt / avoid

- **Adopt**: backlinks-from-link-graph build step (F6.1) — small, SSG-agnostic,
  big UX payoff.
- **Adapt**: hover-preview/graph features — nice-to-have backlog, not v1.
- **Avoid**: Quartz as the SSG (stack + governance mismatch); wikilink syntax
  (F6.2, revisit on evidence).

## Gaps / next loop

- If backlinks step is approved at checkpoint, prototype against the toy KB
  during the SSG hands-on test (doc 01).

## Sources

- https://quartz.jzhao.xyz/ · https://github.com/jackyzha0/quartz
- https://notes.hamatti.org/technology/building-a-digital-garden-with-obsidian-and-quartz

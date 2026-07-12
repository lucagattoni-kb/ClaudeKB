# llm-wiki pattern (Karpathy) — analysis for ClaudeKB

> Research doc. Analyzed 20260712 from the primary gist. Confidence: high on
> the pattern itself; the referenced implementation (ar9av/obsidian-wiki) not
> yet inspected — next loop.

## What it is

Not a tool — an operating pattern for LLM-maintained knowledge bases, from
Andrej Karpathy's llm-wiki gist. Premise: instead of re-answering questions or
re-running RAG, agents **compile knowledge once** into interconnected Markdown
and keep it current. This is the closest published articulation of ClaudeKB's
actual workload (agents as primary readers AND writers), and OKF (doc 02) is
its formalization.

## The pattern

Three layers:

1. **Raw sources** — immutable inputs (articles, papers, files). Agents never
   modify them.
2. **The wiki** — agent-maintained Markdown: entity pages, concept pages,
   summaries, cross-references (wikilinks), YAML frontmatter.
3. **The schema** — a config doc (e.g. `CLAUDE.md`) encoding page types,
   naming conventions, and the workflows below. The KB documents *itself* to
   its agent writers.

Three operations:

- **Ingest**: process a new source → extract, summarize, update entity pages,
  maintain cross-references, append to `log.md`.
- **Query**: search wiki pages, synthesize with citations; optionally file the
  synthesis back as a new page ("queries compound into content").
- **Lint**: periodic health pass — contradictions, stale claims, orphan pages,
  missing cross-references, gaps.

File conventions: `index.md` catalog (one-line summary per page, by category,
read *before* drilling in), `log.md` append-only with `## [DATE] operation |
Title` entries, wikilinks between pages.

## Findings

- **F3.1 — The KB's CLAUDE.md is a first-class blueprint artifact.** The
  pattern's "schema layer" maps directly onto each KB repo's CLAUDE.md: page
  types, naming rules, ingest/query/lint workflows. The blueprint should ship
  a rich, structured KB-CLAUDE.md template — this file does more work than
  any CI gate to keep agent writes consistent. Split: blueprint-owned
  mechanics (workflows, conventions) vs KB-owned specifics (topic, page
  types, vocabulary) — a concrete instance of the §4 ownership boundary,
  possibly as two files (one overwritten on upgrade, one never touched).
- **F3.2 — "Lint" here is semantic, not syntactic — and it's a scheduled
  agent job, not CI.** Contradiction/staleness/orphan detection can't run in
  Workers Builds; it's a periodic Claude Code session the blueprint should
  define as a maintenance playbook (cadence, checks, how to file findings).
  This is a *new capability class* absent from REQUIREMENTS: KB health
  maintenance. Structural sub-checks (orphan pages, dead wikilinks) CAN run
  as deterministic CI validators — split accordingly.
- **F3.3 — Append-only `log.md` gives agents cheap temporal context** ("what
  changed since I last worked here") without git archaeology, at the cost of
  a merge hotspot: with parallel direct-to-main sessions (D5), simultaneous
  appends to one file will conflict. Mitigations to test: per-month log files
  (`log/2026-07.md`), or git `union` merge driver for the log path —
  `.gitattributes` union merge is the structural fix; verify it behaves sanely
  in rebase-retry flow.
- **F3.4 — index.md as curated catalog vs. auto-generated nav.** The pattern
  wants a *content-oriented* index with one-line summaries (progressive
  disclosure for agents); the SSG nav is presentation-oriented. Keep both:
  nav config (curated, hybrid per requirements) for humans; index catalog
  for agents — and a CI validator asserting every page is reachable from the
  index (kills orphans structurally).
- **F3.5 — Wikilinks vs standard Markdown links is a real fork.** The pattern
  (and Obsidian/Quartz worlds) use `[[wikilinks]]`; MkDocs/Zensical and OKF
  use standard links. Wikilinks are friendlier for agent writing (no path
  bookkeeping) but need resolution tooling in build + validation, and reduce
  portability. Decision needed at the architecture checkpoint; leaning:
  standard bundle-root-absolute links (OKF F2.5) + a validator, since our
  writers are agents that handle paths fine.

## Adopt / adapt / avoid

- **Adopt**: KB-CLAUDE.md as schema layer (F3.1); ingest/query/lint as named,
  documented workflows; index catalog + reachability validator (F3.4).
- **Adapt**: log.md → sharded or union-merged (F3.3); lint split into
  CI-able structural checks vs scheduled semantic passes (F3.2).
- **Avoid**: raw-sources layer as a hard requirement — ClaudeKB content is
  mostly authored knowledge, not source-digestion; keep the sources/ concept
  optional per KB.

## Gaps / next loop

- Inspect ar9av/obsidian-wiki for implementation lessons (what breaks in
  practice).
- Test union merge driver + rebase-retry interaction empirically (F3.3).

## Sources

- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- https://github.com/ar9av/obsidian-wiki (not yet inspected)

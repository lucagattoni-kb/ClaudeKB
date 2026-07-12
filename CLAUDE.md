# ClaudeKB

**Blueprint repository** for a system of 10+ independent, content-agnostic,
docs-as-code knowledge bases (Markdown in git + SSG, MkDocs Material candidate),
one repo per KB, AI agents as primary readers/writers via direct git commits.
This repo is not a KB: it scaffolds new self-sufficient KB repos and upgrades
existing ones to the latest blueprint version (see REQUIREMENTS.md §4).

## Canonical context

Read `REQUIREMENTS.md` before any design or implementation work. It contains
the full requirements, the docs-as-code decision rationale, and the open
questions. Do not re-litigate settled decisions; do not silently resolve open
questions — surface them.

## Working principles

- Prefer **structural guarantees over conventions**; verify empirically before
  adding enforcement.
- Strict CI: frontmatter schema validation, link checking, lint — build fails
  on errors.
- Design for parallel agent write sessions (git-native concurrency).
- Keep future extensions in mind without building them: unified cross-KB
  search, MCP/RAG retrieval layer, offline reading.

## Current phase

Bootstrap. Next milestones:

1. Resolve open questions in `REQUIREMENTS.md` §5 (upgrade/scaffold mechanism first)
2. Architecture spec: stack, blueprint layout, ownership-boundary manifest,
   CI gates, hosting + access
3. Implement the blueprint (scaffold + upgrade paths)
4. Scaffold KB #1 and validate the round trip: scaffold → edit → upgrade

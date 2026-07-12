# Basic Memory — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: medium — from README/directory
> listings; not run hands-on. Shorter doc: relevant to the *future* retrieval
> layer, not to v1.

## What it is

basicmachines-co/basic-memory: local-first, MCP-native agent memory stored as
plain Markdown on disk. Agents and humans write the same files; an MCP server
exposes content tools (write/read/edit/move note), search tools, and
knowledge-graph tools (`build_context` navigating `memory://` URLs). Notes use
wikilinks + structured "observations" that compound into a graph. The closest
existing implementation of ClaudeKB's future extension #2 (MCP/RAG retrieval
layer over Markdown KBs).

## Findings

- **F9.1 — "MCP layer over plain Markdown" is validated as a product
  pattern.** No schema conversion or export step: the server indexes Markdown
  directly. Confirms the REQUIREMENTS bet that plain Markdown = direct
  ingestion, and that the retrieval layer can be added later *without*
  changing content — strengthened if our frontmatter is already
  OKF-conformant (F2.1) since MCP tools then get typed metadata for free.
- **F9.2 — Tool-surface design lesson**: it ships MCP behavior hints
  (readOnly/destructive/idempotent per tool) and both content-level and
  graph-level tools. When we build our MCP layer, mirroring its tool taxonomy
  (read/search/context-build as separate tools, not one mega-search) is the
  proven shape. Possibly we don't build at all: point Basic Memory (or its
  then-equivalent) at KB checkouts and get the layer nearly free — evaluate
  vs. build when the extension is actually scheduled.
- **F9.3 — Divergence to note**: Basic Memory optimizes for conversational
  memory capture (unstructured, high-frequency small writes); ClaudeKB is
  curated long-form articles with enforced schema. Don't import its
  entity/observation micro-format into KB content conventions — different
  workload.

## Adopt / adapt / avoid

- **Adapt**: evaluate reuse of Basic Memory as the MCP layer when that
  extension is scheduled (F9.2); keep its tool taxonomy as the design
  reference if we build our own.
- **Avoid**: observation micro-format in KB articles (F9.3); adding any MCP
  machinery to v1.

## Gaps / next loop

- None for v1. Re-open at retrieval-layer design time.

## Sources

- https://github.com/basicmachines-co/basic-memory
- https://github.com/basicmachines-co/basic-memory-skills

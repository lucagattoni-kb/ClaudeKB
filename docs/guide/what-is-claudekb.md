# What is ClaudeKB

## The problem it solves

You want several independent knowledge bases — notes, references, playbooks,
whatever — that:

- **AI agents read and write** as a first-class workflow, not an afterthought;
- stay **plain Markdown in Git**, so history, diffs, review, and merges are
  native and the content is directly ingestible by future retrieval layers;
- are **private by default** with a real login, but can expose selected public
  sections;
- enforce **quality automatically** (metadata schema, no broken or orphan
  links, lint) so a large agent-written corpus doesn't rot;
- and each stay **independent** — one repo per KB, no shared runtime, no single
  point of failure — while still sharing one consistent toolchain.

Structured KB platforms (Notion, Confluence, Outline) fail several of these at
once: agent writes go through an API with last-write-wins semantics, there is
no build step to enforce a schema, and free private SSO is rare. Docs-as-code
(Markdown + a static site generator) wins on every axis — at the cost of owning
the plumbing. ClaudeKB **is** that plumbing, built once and cloned per KB.

## The blueprint model

ClaudeKB is a **blueprint repository**. It has exactly two jobs, both run by an
agent:

1. **Scaffold** — generate a new, fully self-sufficient KB repo.
2. **Upgrade** — bring an existing KB repo up to the latest blueprint version.

Everything a KB needs to build, validate, and deploy travels *inside the KB*
(config, the toolchain as a vendored wheel, its own agent instructions). A KB
never depends on the blueprint at build or run time — only at scaffold and
upgrade time. That is what "self-sufficient" means here, and it's why losing or
renaming the blueprint can't break a single live KB.

### Ownership boundary

Every file in a KB is either **blueprint-owned** (toolchain, config, CI —
overwritten on upgrade) or **KB-owned** (content, navigation, vocabulary — never
touched by upgrades). The boundary is machine-enforced: blueprint-owned files
are checksummed, and editing one fails the validator. This is what lets an
upgrade confidently overwrite the plumbing without ever clobbering your content.

## What a KB looks like

- **Content** is long-form Markdown under `docs/`, each page carrying a small
  required frontmatter block (`type`, `title`, `description`).
- **Navigation** is a curated `nav.yml` with glob sections — hybrid between
  hand-ordered and auto-listed.
- **Links** are stable: bundle-root-absolute within a KB (`/concepts/x.md`),
  and a logical `kb://other-kb/page.md` form across KBs that resolves to real
  URLs at build time, so the URL scheme can change without rewriting content.
- **A change log** (`docs/log.md`) is append-only and merge-safe, so parallel
  agent sessions can both record what they did without conflict.
- **Publishing**: a single `kbtool build` produces a static site; on push,
  Cloudflare Workers Builds re-runs every check and deploys only if green.
- **Access**: private by default via Cloudflare Access (free SSO), with an
  optional world-readable `docs/public/` subsection.

## The ideas it's built on

ClaudeKB is a synthesis of prior art, not an invention from scratch:

- **[copier](https://copier.readthedocs.io/)** — template scaffolding *with*
  lifecycle updates and migrations (not just one-time generation).
- **The [llm-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  (Karpathy) — a KB that documents its own conventions to the agents that write
  it, with ingest/query/lint as named workflows.
- **[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog)**
  (Google) — a Markdown+frontmatter bundle spec; ClaudeKB's frontmatter is a
  conformant superset, for free interop with a growing agent-tooling ecosystem.
- **Docs-as-code at scale** — GitLab's handbook (tuned lint, feedback at the
  point of write) and Backstage TechDocs (per-repo autonomy, a thin aggregation
  layer added later).

The full survey, with per-project analysis and the experiments that validated
the choices, is in [docs/research/](../research/). The complete design is in the
[architecture spec](../architecture.md); every decision is recorded in
[REQUIREMENTS.md](../../REQUIREMENTS.md).

Next: [Install & prerequisites](install.md).

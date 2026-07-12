# GitLab Handbook — analysis for ClaudeKB

> Research doc. Analyzed 20260712. Confidence: medium — from public handbook
> architecture pages; the repo itself not yet mined.

## What it is

The largest public docs-as-code KB in operation (~2,000+ pages, edited by an
entire company): Hugo + Docsy theme, Markdown in a GitLab monorepo, strict
merge-request flow with automated quality gates. Not a template to copy —
different scale, human writers, monorepo — but the best evidence base for
"what CI gates actually keep a big Markdown KB healthy over years."

## Mechanics that matter for ClaudeKB

- **Hugo + Docsy** with custom theme overrides; SASS; Node toolchain — their
  stack choice trades simplicity for scale/speed.
- **CI gates**: markdownlint with heavily customized rule set; custom lint
  jobs whose output is posted back to the MR as Markdown comments (feedback
  where the writer is); Danger bot for MR conventions; contributors told to
  run lint locally before pushing (same shape as our D5 local-validators
  rule).
- **Content governance in the doc system itself**: contribution guidelines,
  architecture docs, and editing how-tos are pages *in* the handbook —
  self-describing system (same instinct as the llm-wiki schema layer, F3.1).
- Structural history: handbook was split out of the main website repo into
  its own content repo (monolith → focused content site) — content and site
  machinery separated over time; they lived the mixed-ownership problem F4.2
  describes.

## Findings

- **F7.1 — Lint rules must be tuned, not default.** GitLab ships a customized
  markdownlint config; defaults generate noise that trains writers to ignore
  CI. Blueprint consequence: our markdownlint config is a blueprint-owned,
  versioned artifact, expected to evolve via blueprint releases — with agent
  writers, every rule we can make deterministic is a prompt-token we don't
  spend explaining style.
- **F7.2 — Feedback belongs at the point of write.** GitLab pushes lint
  results into MR comments. Our direct-to-main flow (D5) has no MR; the
  equivalent is (a) validators run locally by the agent pre-push — fast and
  in-session — and (b) deploy-gate failures must reach the *next* agent
  session legibly. Design consequence: a standard `BUILD_STATUS`/health
  location (file, badge, or API the KB-CLAUDE.md tells agents to check at
  session start) so a red deploy is discovered at the next write, not never.
- **F7.3 — Handbook-first works only with maintenance investment.** GitLab
  budgets real engineering for handbook plumbing. Our counterweight is the
  blueprint: plumbing is built once and upgraded centrally (copier, doc 04),
  and KB counts of pages-per-writer are tiny by comparison. Scale risks that
  bite them (build times, nav sprawl) are monitorable per-KB rather than
  designed against up front.
- **F7.4 — Hugo remains the escape hatch if the Python-adjacent SSG world
  keeps degrading** (doc 01): GitLab proves Markdown KBs of arbitrary size on
  Hugo. Cost: Go templates, no Python plugin surface, our validators stay
  external anyway (F1.3 makes this cheaper than it sounds). Keep as plan C,
  not a current candidate.

## Adopt / adapt / avoid

- **Adopt**: tuned, blueprint-owned markdownlint config (F7.1); build-status
  surfacing convention for agent sessions (F7.2).
- **Adapt**: self-describing governance — contribution/editing rules are KB
  pages + KB-CLAUDE.md, not external wiki (F7.3 lite).
- **Avoid**: monorepo handbook model (contradicts repo-per-KB isolation);
  Docsy/Hugo stack for v1 (F7.4: plan C only).

## Gaps / next loop

- Mine their markdownlint config for a starting rule set when building the
  blueprint's lint config.

## Sources

- https://handbook.gitlab.com/docs/development/architecture/
- https://handbook.gitlab.com/docs/development/
- https://about.gitlab.com/blog/five-fast-facts-about-docs-as-code-at-gitlab/

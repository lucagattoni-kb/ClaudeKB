# Research synthesis — KB-as-code OSS landscape → ClaudeKB plan impacts

> Loop 1 synthesis, 20260712. Inputs: docs 01–09 in this directory. Findings
> are cited as F<doc>.<n>. Everything here is proposal until Luca decides at
> the checkpoint (§5).

## 1. Method & survey disposition

Surveyed ~18 candidates across five angles (docs-as-code SSGs, digital
gardens/PKM, multi-repo docs systems, agent-KB patterns/specs, template
lifecycle tooling). Shortlisted 9 for analysis docs; the rest were dispatched:

| Candidate | Disposition |
|---|---|
| Zensical / MkDocs ecosystem | **Doc 01** — SSG decision core |
| Open Knowledge Format (Google) | **Doc 02** — frontmatter/bundle spec |
| llm-wiki pattern (Karpathy) | **Doc 03** — agent workflows |
| copier (vs cruft/cookiecutter) | **Doc 04** — scaffold/upgrade engine |
| Antora | **Doc 05** — multi-repo linking lessons |
| Quartz | **Doc 06** — personal-KB reader UX bar |
| GitLab Handbook | **Doc 07** — CI gates at scale |
| Backstage TechDocs | **Doc 08** — fleet architecture |
| Basic Memory | **Doc 09** — future MCP layer |
| Docusaurus | Rejected: React/JS stack, product-docs shape; strong but off-constraint (Python/uv) |
| Astro Starlight | Rejected: same stack reason; healthiest JS docs SSG — noted as ecosystem-exit option behind Hugo (F7.4) |
| Sphinx | Rejected for v1: Python-native but reST-cultured, heavier authoring; weak fit for agent-written Markdown KBs (MyST exists; complexity tax) |
| Hugo (+Docsy) | Plan C escape hatch (F7.4), not v1 |
| mkdocs-ng / ProperDocs / MaterialX | Covered in doc 01 as conservative forks |
| Dendron | Rejected: effectively unmaintained since ~2023; its schema-enforced hierarchy idea survives in our frontmatter+vocabulary design |
| Foam | Rejected: VS-Code-bound human tool, no build/CI story |
| Emanote | Rejected: Haskell stack, niche; no advantage over shortlist |
| Outline / Wiki.js | Rejected: platform/DB paradigm — the class REQUIREMENTS already decided against |

## 2. Top findings, ranked by plan impact

1. **D9 falsified: "MkDocs Material" is no longer a pickable default** —
   core unmaintained, Material in maintenance mode, successor (Zensical) young
   but credible, forks conservative. New SSG decision required (F1.1–F1.2).
   → Checkpoint item C1.
2. **Validators must be SSG-independent, own-code, Python/uv** (F1.3, F8.4).
   The ecosystem collapse punished plugin coupling. Frontmatter schema, link
   check, lint orchestration, git-derived dates, backlinks: all standalone
   scripts the SSG merely consumes. (Concretely: JSON-Schema/pydantic
   validation in our own uv scripts, not remark-JS or SSG plugins; lychee and
   markdownlint as external binaries orchestrated by our runner.)
3. **copier is the §4 blueprint engine, nearly verbatim** (F4.1–F4.4):
   `.copier-answers.yml` = version manifest; template inclusion/exclusion =
   ownership boundary; copier migrations + agent playbooks = breaking-change
   machinery. Open Q1 and Q2 now have concrete shapes pending one hands-on
   test (update-conflict behavior, F4.3).
4. **The KB-CLAUDE.md is the highest-leverage artifact in the blueprint**
   (F3.1, F7.3): the llm-wiki "schema layer" — page types, naming, ingest/
   query/lint workflows — does more for write consistency than CI. Split
   blueprint-owned mechanics from KB-owned specifics (F4.2 instance).
5. **OKF conformance is nearly free and buys agent-ecosystem interop**
   (F2.1–F2.5): add required `type` to D6's schema; reserve `index.md`/
   `log.md`; bundle-root-absolute links. → Checkpoint item C2.
6. **New capability class: KB health maintenance** (F3.2): scheduled agent
   lint sessions (contradictions, staleness, orphans) defined as blueprint
   playbooks; structural subset (orphans, dead links, index reachability)
   runs as deterministic CI validators (F3.4).
7. **Fleet self-description: per-KB manifest** (F8.1): tiny blueprint-owned
   file (name, blueprint version, URL, visibility, description) that future
   unified search/portal consumes. Design-for-don't-build, made concrete.
8. **Reserve logical cross-KB link form now** (F5.1): content writes
   `kb://<kb>/<path>`-style (or equivalent) resolved at build time; URL
   scheme changes become resolver changes. Cheap now, migration later.
9. **Reader-UX gap vs digital gardens: backlinks** (F6.1): derivable from the
   link graph the validator already builds; small SSG-agnostic emitter step.
   → Checkpoint item C4 (scope).
10. **Feedback-at-the-point-of-write for a no-PR flow** (F7.2): standard
    build-status surface agents check at session start; log.md merge hotspot
    needs union-merge or sharding (F3.3) — both to empirical test.

## 3. What survived falsification attempts

- **Docs-as-code choice itself**: nothing surfaced suggesting platforms
  (Outline class) beat git+SSG for agent-written KBs; agent-KB movement (OKF,
  llm-wiki, Basic Memory) is converging on plain Markdown + git (F9.1).
- **Repo-per-KB with thin aggregation later**: validated by TechDocs (F8.3)
  and Antora (F5.2).
- **D5 direct-to-main + deploy gate**: GitLab's lint-locally-first culture and
  TechDocs' decoupled builds are consistent with it; no evidence against.
- **Python/uv toolchain**: every needed validator exists as Python lib or
  external binary; no JS toolchain required.

## 4. Revised plan shape (proposal)

Blueprint repo = copier template containing: KB skeleton (content/, nav file,
manifest, KB-CLAUDE.md pair), blueprint-owned validators (uv scripts),
tuned lint configs, Workers Builds config with single build entry point,
Access/DNS setup playbook, maintenance playbooks (ingest/lint), migrations/
directory, and blueprint CI that scaffolds+upgrades a fixture KB on every
release. KB #1 scaffolds greenfield after C1–C4 land.

## 5. Checkpoint — decisions for Luca

- **C1 (SSG)**: pinned MkDocs Material with planned Zensical migration vs
  Zensical now vs decide-after-hands-on-test (both candidates on a toy KB).
- **C2 (schema)**: adopt required `type` (OKF conformance) into frontmatter
  v1? (Amends D6.)
- **C3 (links)**: standard bundle-root-absolute links + validator (rec) vs
  wikilinks + resolution tooling (F3.5/F6.2); plus reserve logical cross-KB
  form (F5.1)?
- **C4 (v1 scope adds)**: backlinks emitter (F6.1); log.md convention with
  union-merge/sharding (F3.3); per-KB manifest (F8.1); maintenance playbooks
  (F3.2). Which go into v1 vs backlog?

## 6. Next loop (after checkpoint)

1. Hands-on SSG test per C1 (toy KB on both candidates; measure in Workers
   Builds sandbox if feasible).
2. copier update-conflict experiment (F4.3).
3. Empirical Cloudflare checks from REQUIREMENTS §6 (Access wildcard, /public
   bypass, workers.dev lockdown).
4. Union-merge/log-sharding test (F3.3).
5. Then: architecture spec draft + adversarial review loop.

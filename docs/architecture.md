# ClaudeKB Blueprint — Architecture Spec v1

Status: preliminary — under adversarial review

> Implements the decision record `REQUIREMENTS.md` D1–D14 using research
> findings `docs/research/` (cited F<doc>.<n>) and loop-2 experiment results
> (E1–E4, `docs/research/10-loop2-experiments.md`). Every load-bearing claim
> below is tagged **[verified]** (observed/confirmed this project),
> **[docs]** (vendor docs, not yet exercised), or **[verify-at-impl]**
> (must be checked during implementation before anything depends on it).

## 1. Goal and non-goals

**Goal**: specify the blueprint repo (this repo) and the KB repos it
generates, precisely enough that implementation is mechanical: file layouts,
formats, commands, pipelines, deploy/access configuration, and the playbooks
agents execute.

**Non-goals (deliberately not decided here)**: unified cross-KB search
implementation; MCP/RAG retrieval layer (evaluate Basic Memory reuse first,
F9.2); offline reading packaging; backlinks emitter (deferred, D13); identity
provider beyond the default (Cloudflare one-time PIN); wildcard-vs-per-KB
Access application consolidation (resolve during live setup, E4); the exact
Zensical version pin (chosen at implementation time, then managed by blueprint
releases).

## 2. System overview

```
ClaudeKB blueprint repo (copier template, semver-tagged releases)
   │  copier copy @vX.Y.Z          copier update + migrations + playbooks
   ▼                                ▲
kb-<name> repo (GitHub org, private) ──── agents write via direct commits
   │  push to main                        (rebase-retry, D5)
   ▼
Workers Builds:  uv run kbtool ci  →  wrangler deploy      (deploy gate)
   ▼
Cloudflare Worker "kb-<name>" (static assets) at kb-<name>.example.com
   └─ Cloudflare Access: private by default; Bypass on /public/* (D7)
```

Every KB repo is self-sufficient (REQUIREMENTS §4): it builds, validates, and
deploys with no reference to the blueprint except at scaffold/upgrade time.

## 3. Blueprint repo layout

```
ClaudeKB/
├── copier.yml                  # questions, _subdirectory, _skip_if_exists,
│                               # _migrations, _tasks
├── template/                   # the KB skeleton (everything below §4)
├── playbooks/                  # agent-executed procedures (§10, §11)
│   ├── scaffold-kb.md
│   ├── upgrade-kb.md
│   ├── access-dns-setup.md
│   ├── maintain-ingest.md
│   └── maintain-lint.md
├── docs/                       # blueprint's own docs (this spec, research)
├── tests/                      # blueprint CI fixtures (§12)
├── CHANGELOG.md                # semver; entries timestamped `YYYYMMDD HH:MM`
├── CLAUDE.md                   # blueprint repo agent instructions
└── REQUIREMENTS.md
```

`copier.yml` core (per E2 findings — all three gotchas are requirements):

```yaml
_subdirectory: template
_skip_if_exists:            # KB-owned: seeded once, never overwritten (E2)
  - docs/**
  - nav.yml
  - kb.yml
  - CLAUDE-KB.md
  - vocab.yml
kb_name:                    # slug; becomes repo name kb-<kb_name>, Worker
  type: str                 # name, and hostname kb-<kb_name>.example.com
  validator: "{% if not (kb_name | regex_search('^[a-z0-9][a-z0-9-]{1,30}$')) %}invalid slug{% endif %}"
kb_title:
  type: str
kb_description:
  type: str
```

Scaffolding is always from a git URL at a semver tag (`copier copy --vcs-ref
vX.Y.Z gh:… `), never from a local path — relative `_src_path` breaks
`copier update` **[verified E2]**.

## 4. KB repo layout (generated)

```
kb-<name>/
├── .copier-answers.yml         # BP-owned, machine-updated: blueprint version
│                               # (_commit) + answers. The §4 version manifest.
├── kb.yml                      # KB-owned identity manifest (§5.3)
├── CLAUDE.md                   # BP-owned agent contract (§9); imports ↓
├── CLAUDE-KB.md                # KB-owned specifics (topic, page types, vocab
│                               # notes) — seeded once
├── docs/                       # KB-owned content (all of it)
│   ├── index.md                # curated catalog (F3.4); seeded
│   ├── log.md                  # append-only change log (E3); seeded
│   └── public/                 # world-readable subtree (D7); seeded empty
├── nav.yml                     # KB-owned curated nav (F5.4)
├── vocab.yml                   # KB-owned controlled vocabulary (§5.2)
├── config/
│   └── site-base.yml           # BP-owned SSG config base (§6.2)
├── schema/
│   └── frontmatter.schema.json # BP-owned (§5.1)
├── tools/kbtool/               # BP-owned validator/build package (§6)
├── pyproject.toml              # BP-owned; pins zensical + deps; uv-managed
├── uv.lock                     # generated at scaffold (copier task), then
│                               # updated only by blueprint upgrades
├── wrangler.jsonc              # BP-owned deploy config (§7)
├── .markdownlint.yml           # BP-owned tuned lint rules (F7.1)
├── .gitattributes              # BP-owned: `docs/log.md merge=union` (E3)
├── .gitignore                  # BP-owned: `.build/`, `.venv/`, `site/`
└── blueprint-checksums.json    # BP-owned boundary manifest (§8)
```

Ownership rule (resolves open Q2): **a path is KB-owned iff it is listed in
`_skip_if_exists` (seeded once) or absent from the template; everything else
is blueprint-owned and will be overwritten by upgrades.** No file has mixed
ownership; the historical mixed file (`mkdocs.yml`) is eliminated by
generating it at build time (§6.2). KB-side edits to blueprint-owned files
cause recurring update conflicts **[verified E2]** and are rejected by the
boundary validator (§8).

## 5. Content conventions and formats

### 5.1 Frontmatter (D6 + D11)

Required on every `docs/**/*.md` except `index.md` and `log.md` (OKF reserved
files, F2.3): `type`, `title`, `description`. Optional but validated when
present: `tags` (list), `status` (enum: `draft | review | published |
archived`). Unknown extra keys are allowed and preserved (OKF permissive-
producer rule, F2.1). No date fields — dates come from git (D6).

`schema/frontmatter.schema.json` (JSON Schema draft 2020-12) encodes the
above; `type` and `tags` values are additionally checked against `vocab.yml`:

```yaml
# vocab.yml (KB-owned; validated non-empty)
types: [article, reference, playbook, concept]
tags: [example-tag]
```

### 5.2 Links (D12)

- Intra-KB: standard Markdown, **bundle-root-absolute** (`/concepts/alpha.md`).
- Cross-KB: `kb://<kb-name>/<path>` — resolved at build time to
  `https://kb-<kb-name>.example.com/<path-as-url>`.
- Both forms are rewritten by the preprocessor (§6.1); Zensical never sees
  them **[verified E1: Zensical emits root-absolute links broken]**.
- External links: plain URLs; checked by lychee in scheduled maintenance,
  not in the deploy gate (external-site flakiness must not block deploys).

### 5.3 Manifests

- `.copier-answers.yml` (blueprint-owned): records `_commit` (blueprint
  semver tag) and answers. Machine-updated by copier only. Exists because the
  template ships `{{ _copier_conf.answers_file }}.jinja` **[verified E2]**.
- `kb.yml` (KB-owned, seeded from answers):

```yaml
name: <kb_name>            # slug; must match repo/Worker/hostname suffix
title: <kb_title>
description: <kb_description>
url: https://kb-<kb_name>.example.com
visibility: private        # private | public — drives Access playbook
```

Future fleet consumers (unified search/portal, F8.1) read `kb.yml` +
`.copier-answers.yml`; nothing else is promised to them.

### 5.4 log.md (D13, E3)

Append-only; union merge driver **[verified E3 in merge and rebase]**.
Entry format (self-contained block, tolerant of blank-line collapse):

```markdown
## 20260712 11:31 ingest | Added page /concepts/alpha.md
One-line-or-few summary. Optional links.
```

Validator: previous content must be a prefix (modulo trailing whitespace) of
the new content — mid-file edits fail the gate (union merge is only safe for
appends, E3).

### 5.5 Public split (D7)

`docs/public/**` is the only world-readable subtree. Structural consequences
enforced by validators: search index and sitemap stay at site root (private);
pages under `/public/` must not intra-link to private pages (broken for
anonymous readers) — warning, not error. Moving a page across the boundary
requires a redirect entry in `_redirects` (Workers static assets, 2,000
static redirects on free plan **[verified: platform limits]**); the lint
playbook checks for orphaned inbound links on moves.

## 6. kbtool — validator suite and build pipeline

`tools/kbtool/` is a small blueprint-owned Python package; all commands run
via `uv run kbtool <cmd>`. Everything is SSG-independent (F1.3/F1.4) — the
SSG is invoked only as the last step of `build`.

### 6.1 Commands

| Command | What it does | Exit ≠ 0 when |
|---|---|---|
| `kbtool check` | All validators: frontmatter schema + vocab; intra-KB link targets exist (including kb:// syntax shape); index reachability (every content page reachable from `docs/index.md` — kills orphans, F3.4); log append-only (§5.4); boundary checksums (§8); markdownlint (invoked as subprocess); nav.yml entries exist | any validator fails |
| `kbtool build` | `check` → preprocess (§6.2) → `zensical build -f .build/mkdocs.yml -s` → post-build assertions (search index exists; `_redirects` copied) | any step fails |
| `kbtool serve` | preprocess → `zensical serve` on `.build/` | — |
| `kbtool push` | `git pull --rebase --autostash` → `git push`, retried ×3 with backoff (D5 rebase-retry) | push still rejected |
| `kbtool ci` | alias of `build`; the single platform-owned entry point (F8.2) used by Workers Builds | — |

### 6.2 Preprocess step (the D12/D14 keystone)

1. Copy `docs/` → `.build/docs/` (gitignored).
2. Rewrite links in the copies: `kb://<kb>/<path>` → absolute https URL;
   root-absolute `/a/b.md` → correct relative path. Content on disk stays
   logical; any SSG can consume the output **[verified E1 rationale]**.
3. Inject per-page footer line `*Last updated: <date> · from git history*`
   using `git log -1 --format=%as -- <file>` (D6; build-time timestamp
   injection satisfies OKF `timestamp` recommendation, F2.4).
4. Generate `.build/mkdocs.yml` = `config/site-base.yml` (blueprint-owned:
   theme, markdown extensions incl. Mermaid superfences, strict validation
   flags, search) + `nav` from `nav.yml` (KB-owned) + `site_name`/`site_url`
   from `kb.yml`. This eliminates the mixed-ownership `mkdocs.yml` (F4.2);
   Zensical accepts `-f <path>` **[verified E1 --help]**.

### 6.3 SSG pinning and fallback (D14)

`pyproject.toml` pins `zensical==<exact>`. The Material fallback is a
blueprint release that swaps `site-base.yml` + the pinned dependency to
`mkdocs==1.6.1` + `mkdocs-material==9.7.6` and changes the build invocation;
content and validators are untouched by design. Fallback trigger: a Zensical
regression or missing feature that blocks a KB and has no workaround within
one working session.

## 7. Deploy — Workers Builds + wrangler

`wrangler.jsonc` (blueprint-owned, values templated at scaffold):

```jsonc
{
  "name": "kb-<name>",
  "compatibility_date": "<scaffold date>",
  "assets": { "directory": ".build/site" },
  "workers_dev": false,          // [docs] direct URL disabled
  "preview_urls": false,         // [docs] explicit despite 4.44 default
  "routes": [{ "pattern": "kb-<name>.example.com", "custom_domain": true }]
}
```

Workers Builds configuration (per KB, set once at scaffold):
- Build command: `uv run kbtool ci`
- Deploy command: `npx wrangler deploy`
- Root directory: `/`; build on push to `main`.
- **[verify-at-impl]** uv availability in the Workers Builds image; if
  absent, prepend the documented installer
  (`curl -LsSf https://astral.sh/uv/install.sh | sh`) to the build command.

Budget check (D5): 3,000 build-min/mo free, 1 concurrent build, 20-min
timeout **[verified]**; toy builds ≈ seconds (E1). Queued builds are
acceptable — publish latency is explicitly irrelevant (REQUIREMENTS §3).
Deploy-gate property: a red commit lands in git but never deploys; the next
agent session discovers it via the session-start ritual (§9, F7.2).

## 8. Ownership boundary enforcement

`blueprint-checksums.json` is generated at blueprint release time and shipped
in the template. It lists sha256 for **static** blueprint-owned files
(`tools/**`, `schema/**`, `config/site-base.yml`, `.markdownlint.yml`,
`.gitattributes`). Files whose rendered content varies per KB
(`wrangler.jsonc`, `pyproject.toml`, `CLAUDE.md`) instead carry a first-line
marker `# MANAGED BY BLUEPRINT vX.Y.Z — do not edit` whose presence and
version `kbtool check` asserts. Residual drift in templated files is caught
as conflicts at the next `copier update` **[verified E2]** — accepted for v1.

## 9. The CLAUDE.md pair (F3.1)

- `CLAUDE.md` (blueprint-owned, overwritten on upgrade): the agent contract —
  frontmatter/link/log conventions with one example each; the command table
  (§6.1); the session ritual: **start** = read `docs/index.md`, tail of
  `docs/log.md`, run `kbtool check`; **before ending** = update `index.md`
  if pages were added/moved, append a `log.md` entry, `kbtool check`, commit,
  `kbtool push`. Imports the KB-owned half via `@CLAUDE-KB.md`.
- `CLAUDE-KB.md` (KB-owned, seeded once): what this KB is about, its page
  types and when to create each, vocabulary rationale, KB-specific rules.

## 10. Scaffold playbook (playbooks/scaffold-kb.md)

1. `gh repo create <org>/kb-<name> --private` (org per D1).
2. `uvx copier copy --vcs-ref v<X.Y.Z> gh:<org>/ClaudeKB kb-<name>` —
   answers: slug, title, description.
3. Copier post-task: `uv lock` (creates `uv.lock`), `git init -b main`,
   initial commit.
4. `uv run kbtool check && uv run kbtool build` locally — must pass before
   any remote exists.
5. Push; connect Workers Builds to the repo (dashboard; **[docs]** GitHub app
   flow) with §7 settings; first deploy creates the custom domain + DNS
   record automatically (**[docs]** `custom_domain: true`).
6. Run `playbooks/access-dns-setup.md`:
   a. Access app "kb-<name>" — domain `kb-<name>.example.com`, policy
      Allow, include: Luca's email; IdP: one-time PIN (default).
   b. Access app "kb-<name>-public" — domain
      `kb-<name>.example.com/public`, policy **Bypass**, include:
      Everyone **[docs: documented pattern, E4]**.
   c. Verification checklist (LIVE, first scaffold only — resolves E4's
      remaining unknowns): anonymous request to `/` → Access login;
      anonymous to `/public/…` → 200; `kb-<name>.<account>.workers.dev` →
      404/blocked; search index URL unauthenticated → login. Record results
      in `docs/research/` and, if wildcard app consolidation is preferred,
      test `kb-*.example.com` as one app here.
7. Append scaffold entry to KB's `log.md`; register nothing centrally —
   the fleet is discoverable via `kb.yml` in each repo (F8.1).

## 11. Upgrade machinery (D10)

- Blueprint releases: semver tags. CHANGELOG.md separates breaking /
  non-breaking (REQUIREMENTS §4); entries timestamped `YYYYMMDD HH:MM`.
- Per-KB upgrade = `playbooks/upgrade-kb.md`:
  1. Read CHANGELOG between `.copier-answers.yml:_commit` and target tag.
  2. `uvx copier update --vcs-ref v<target>` — conflicts expected **only** if
     the boundary was violated (E2); resolve favoring the blueprint, then fix
     the KB-side need properly (usually: move the customization to a KB-owned
     file or file a blueprint issue).
  3. Copier `_migrations` run automatically for crossed versions (mechanical
     changes); CHANGELOG lists **content playbooks** (agent-executed, e.g.
     frontmatter migrations across articles) the agent runs now (F4.4).
  4. `uv run kbtool check && uv run kbtool build`; commit with the blueprint
     version in the message; `kbtool push`; append `log.md` entry.
- Fleet upgrades are per-KB and independent — no orchestration in v1.

## 12. Blueprint CI (GitHub Actions, blueprint repo only)

On PR + main push (budget: well under D1's 2,000 min/mo — one small job):
1. Scaffold a fixture KB from the working tree (`copier copy .`), run
   `uv run kbtool ci` inside it — the scaffold must always produce a green
   KB (F4.5).
2. Upgrade test: scaffold from the **latest release tag**, then
   `copier update` to the working tree; assert zero conflicts and green
   `kbtool ci` — guarantees released upgrades don't break clean KBs.
3. On release tag: regenerate `blueprint-checksums.json`, verify CHANGELOG
   has an entry for the tag, then tag.

KB repos get **no** GitHub Actions in v1 — the deploy gate is Workers Builds
(D5); forge CI minutes stay unspent.

## 13. Maintenance playbooks (D13, F3.2)

- `maintain-ingest.md`: how agents add knowledge — where pages go, when to
  create vs extend (defer to CLAUDE-KB.md specifics), always: frontmatter,
  index.md entry, log.md entry, `kbtool check`, push.
- `maintain-lint.md` (scheduled agent session, e.g. monthly per KB):
  structural pass (`kbtool check` + lychee external-link sweep) then semantic
  pass (contradictions, staleness, orphan-in-spirit pages, missing
  cross-references — F3.2); findings fixed directly or filed as `status:
  review` pages; session logged in log.md.

## 14. Success criteria

Blueprint v1 is done when: (a) blueprint CI (§12) is green including the
upgrade test; (b) KB #1 scaffolds via §10 in ≤ 1 hour of agent time with
zero manual file edits; (c) the live checklist in §10.6c passes — all four
Access/workers.dev probes behave as specified; (d) two parallel agent
sessions writing to KB #1 both land (D5 + E3 mechanics) with no lost writes;
(e) a no-op `copier update` on KB #1 produces zero conflicts.

## 15. Risks and mitigations

| Risk | Class | Mitigation |
|---|---|---|
| Zensical 0.0.x churn breaks a build | when | version pin; upgrades only via blueprint releases tested by §12; Material fallback (§6.3) |
| Workers Builds image lacks uv | if | §7 verify-at-impl; installer prepend is the known fallback |
| Access misconfig exposes private content | if | §10.6c live checklist is a launch gate per KB; `visibility` in kb.yml drives the playbook; search/sitemap stay behind Access (§5.5) |
| Agent violates boundary/conventions | when | §8 validator + CLAUDE.md contract + E2's recurring-conflict pain surfacing at upgrade |
| log.md union-merge corruption via mid-file edit | if | append-only validator (§5.4) fails the gate before damage lands |
| Blueprint upgrade breaks all KBs at once | if | §12 upgrade test on every release; per-KB independent upgrades allow halting after the first bad one |

## Iteration log

- pass 0 (20260712 11:31): preliminary draft written.

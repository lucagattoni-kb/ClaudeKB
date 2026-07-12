# ClaudeKB Blueprint — Architecture Spec v1

Status: implemented (20260712 12:37) — blueprint built and verified end-to-end
against this spec; `[verify-at-impl]` items resolved (see CHANGELOG
"spec deviations resolved during implementation"). Prior: reviewed after 9
adversarial passes (D1–D18).

v0.1.1 (20260712): live launch of KB #1 (kb-sandbox) resolved every E4
assumption (see §10.6c) and surfaced one design gap — public pages need the
theme's `/assets/` bypassed too, and KB media therefore relocates to
`/media/` (§5.5, §5.6).

Implementation deltas from this text (full detail in CHANGELOG):
the vendored wheel keeps its **canonical versioned filename**
(`vendor/kbtool-<ver>-py3-none-any.whl`), not a fixed `kbtool.whl` — uv
rejects a renamed wheel, and `copier update` deletes the old-versioned wheel
cleanly. Root-absolute links rewrite to the **final URL path**. PyMarkdown
**MD025** is disabled (conflicts with our frontmatter-title + body-H1
convention). Zensical `docs_dir`/`site_dir` overrides and frontmatter-less
home rendering: confirmed working.

> Implements the decision record `REQUIREMENTS.md` D1–D18 using research
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
├── src/kbtool/                 # THE ONLY HOME of kbtool source (D15) —
│                               # validators, preprocessor, and as package
│                               # data: playbooks (D16), site-base.yml,
│                               # frontmatter.schema.json, pymarkdown config
├── template/                   # the KB skeleton (everything below §4),
│                               # incl. vendor/kbtool.whl built from src/
├── playbooks/
│   └── scaffold-kb.md          # the one playbook that runs before a KB
│                               # exists; all others ship in the package (D16)
├── docs/                       # blueprint's own docs (this spec, research)
├── tests/                      # kbtool unit tests + CI harness scripts (§12;
│                               # fixtures are scaffolded into tmp dirs at run)
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
│                               # (_commit) + answers — the REQUIREMENTS §4
│                               # version manifest.
├── kb.yml                      # KB-owned identity manifest (§5.3)
├── CLAUDE.md                   # BP-owned agent contract (§9); imports ↓
├── CLAUDE-KB.md                # KB-owned specifics (topic, page types, vocab
│                               # notes) — seeded once
├── docs/                       # KB-owned content (all of it)
│   ├── index.md                # curated catalog (F3.4); seeded
│   ├── log.md                  # append-only change log (E3); seeded
│   ├── assets/                 # in-repo media (§5.6); seeded w/ .gitkeep
│   └── public/                 # world-readable subtree (D7); seeded with a
│                               # placeholder page (git can't track empty dirs)
├── nav.yml                     # KB-owned curated nav w/ glob sections (§6.2)
├── vocab.yml                   # KB-owned controlled vocabulary (§5.2)
├── vendor/
│   └── kbtool-<ver>-py3-none-any.whl  # BP-owned built artifact (D15) —
│                               # carries validators, preprocessor, playbooks
│                               # (D16), site-base.yml, frontmatter schema, and
│                               # lint config as package data. Canonical
│                               # versioned filename (uv requires it); the
│                               # pyproject pin references it exactly.
├── pyproject.toml              # BP-owned; pins kbtool==X.Y.Z (uv source →
│                               # vendor/kbtool.whl) + zensical + deps
├── uv.lock                     # generated at scaffold (copier task), then
│                               # updated only by blueprint upgrades
├── wrangler.jsonc              # BP-owned deploy config (§7)
├── .gitattributes              # BP-owned: `docs/log.md merge=union` (E3)
├── .gitignore                  # BP-owned: `.build/`, `.venv/`
└── blueprint-checksums.json    # BP-owned boundary manifest (§8)
```

The KB repo therefore contains **no blueprint code or blueprint config as
editable files** (D15/D16): content, identity, nav, vocabulary, and pinned
artifacts only, plus the root files external tools require in place
(wrangler.jsonc, pyproject/uv.lock, git dotfiles, CLAUDE.md).

Ownership rule (resolves open Q2): **a path is KB-owned iff it is listed in
`_skip_if_exists` (seeded once) or absent from the template; everything else
is blueprint-owned and will be overwritten by upgrades.** No file has mixed
ownership; the historical mixed file (`mkdocs.yml`) is eliminated by
generating it at build time (§6.2). KB-side edits to blueprint-owned files
cause recurring update conflicts **[verified E2]** and are rejected by the
boundary validator (§8).

## 5. Content conventions and formats

### 5.1 Frontmatter (D6 + D11)

Required fields on every `docs/**/*.md`: **`type`, `title`, `description`**
— except any `index.md` and any `log.md`, which are exempt entirely: OKF
reserves both filenames in any directory (F2.3; this resolves the question
doc 02 left open), marks `index.md` explicitly as frontmatter-free, and we
extend the same rule to `log.md` for symmetry — both carry **no
frontmatter**, their H1 is the title. **[verify-at-impl]** Zensical renders
a frontmatter-less home page correctly. Optional but validated when present:
`tags` (list), `status` (enum: `draft | review | published | archived`).
Unknown extra keys are allowed and preserved (OKF permissive-producer rule,
F2.1). No date fields — dates come from git (D6).

`frontmatter.schema.json` (JSON Schema draft 2020-12, shipped as kbtool
package data — D15) encodes the above; `type` and `tags` values are
additionally checked against `vocab.yml`:

```yaml
# vocab.yml (KB-owned; validated non-empty)
types: [article, reference, playbook, concept]
tags: [example-tag]
```

### 5.2 Links (D12)

- Intra-KB: standard Markdown, **bundle-root-absolute** (`/concepts/alpha.md`).
- Cross-KB: `kb://<kb-name>/<path>.md` — resolved at build time to
  `https://kb-<kb-name>.example.com/<url-path>`.
- **Source-path → URL mapping rule** (used by both rewrites, matches
  directory-URL output): strip the `.md` suffix and append `/`
  (`/concepts/alpha.md` → `/concepts/alpha/`); any `index.md` maps to its
  directory root (`/concepts/index.md` → `/concepts/`).
- Both forms are rewritten by the preprocessor (§6.2); Zensical never sees
  them **[verified E1: Zensical emits root-absolute links broken]**.
- Cross-KB targets are **not** resolvable at validation time (independent
  repos); `kbtool check` validates syntax only, and broken cross-KB links are
  tolerated at read time (OKF consumer stance, F2.2) — the lint playbook
  (§13) sweeps them with lychee instead.
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
visibility: private        # private | public — drives Access playbook.
                           # Seeded private; to flip, edit this field and
                           # re-run `kbtool playbook access-dns-setup` (§5.5).
platform:                  # D17: intended values for state that necessarily
  workers_builds:          # lives in Cloudflare/GitHub, not in files. The
    build_command: uv run kbtool ci      # repo is the source of truth; the
    deploy_command: npx wrangler deploy  # dashboard is a cache of it. §10.6c
    branch: main                         # verifies record == reality at
  access_apps:                           # launch; format is designed for a
    - name: kb-<kb_name>                 # future `kbtool provision` to
      policy: allow-owner                # consume unchanged.
    - name: kb-<kb_name>-public
      policy: bypass-everyone
      path: /public
```

`kbtool check` asserts internal consistency of the triple {`kb.yml:name`,
`kb.yml:url`, `wrangler.jsonc` worker name + route pattern} — the three
places the slug appears cannot drift. When a blueprint release changes a
canonical platform value (e.g. the build command), the CHANGELOG instructs
updating both the dashboard **and** the `platform:` record — kb.yml is
KB-owned, so upgrades never rewrite it silently.

Future fleet consumers (unified search/portal, F8.1) read `kb.yml` +
`.copier-answers.yml`; nothing else is promised to them.

### 5.4 log.md (D13, E3)

Append-only; union merge driver **[verified E3 in merge and rebase]**.
Entry format (self-contained block, tolerant of blank-line collapse):

```markdown
## 20260712 11:31 ingest | Added page /concepts/alpha.md
One-line-or-few summary. Optional links.
```

Validator (append-only check, precise semantics): the working-tree `log.md`
must have `git show HEAD:docs/log.md` as a prefix (modulo trailing
whitespace); new file (no HEAD version) passes trivially. The check runs
pre-commit (the §9 ritual runs `kbtool check` before committing), so **every
individual commit's log change is append-only vs its parent** — and since
union merge preserves append-only inputs **[verified E3]**, append-only-ness
holds inductively across concurrent sessions. What the check cannot catch:
an agent that edits mid-file *and* commits without running `kbtool check`
(contract violation); the deploy-gate re-run then sees working tree == HEAD
and passes vacuously. Accepted residual risk — the damage is a garbled log,
not lost content, and git history retains every prior state.

### 5.5 Public split (D7)

`docs/public/**` is the only world-readable subtree. The search index and
sitemap live at the site root and are therefore private automatically (no
validator needed — placement is structural). Validator-enforced: pages under
`/public/` must not intra-link to private pages (broken for anonymous
readers) — warning, not error.

**Shared-build consequences, accepted for v1** (a split build is the real
fix — backlog). Because public and private pages share one site build:

1. **Theme assets must be bypassed too.** The theme's CSS/JS live at
   `/assets/` (site root), not under `/public/`, so a `/public` bypass alone
   leaves public pages unstyled and non-functional for anonymous readers.
   The Access setup therefore adds a **third Bypass app on `/assets`**
   (§10.6). This is safe: `/assets/` holds only generic theme files; KB media
   lives at `/media/` (§5.6) and stays private, and the search index
   (`/search.json`) and sitemap stay private, so no KB content leaks.
   Mermaid diagrams render client-side from the now-public JS, so they work
   on public pages; embedded **raster images do not** (they're at `/media/`,
   private). Stated for authors in CLAUDE.md.
2. **Nav title leak.** The one global nav exposes *page titles* (not content)
   of private pages to anonymous readers, so **private page titles must not
   themselves be sensitive.** Stated in CLAUDE.md. Listed in §15.

Discovered live on KB #1 (20260712): the original design bypassed only
`/public`, which under-specified the asset-namespace problem; fixed in
blueprint v0.1.1.

Moving a page across the boundary
requires a redirect entry in `_redirects` (Workers static assets, 2,000
static redirects on free plan **[verified: platform limits]**); the lint
playbook checks for orphaned inbound links on moves.

**Fully-public KB variant**: `kb.yml: visibility: public` → the Access
playbook (§10.6) creates **no** applications for the hostname; the `/public/`
subtree convention still exists but is redundant. Flipping a KB
public↔private later is an Access-configuration change only — URLs are
unaffected.

### 5.6 Media (in-repo images)

Images live under `docs/media/<path-of-owning-page>/…` (mirroring the
owning page's path prevents slug collisions) and are referenced with the
same bundle-root-absolute form (`/media/alpha/diagram.png`). **Not
`docs/assets/`** — that path is the SSG theme's output namespace, made
world-readable by the assets-bypass (§5.5); KB media at `/media/` stays
private. The
preprocessor rewrites them identically (asset paths keep their extension —
the §5.2 `.md` mapping applies only to `.md` targets). Soft limit 2 MiB per
file (validator warning), hard limit 20 MiB (error; Workers static assets
cap is 25 MiB/file **[verified: platform limits]**). Mostly-external media
stays the norm (REQUIREMENTS §3); no git-LFS in v1.

## 6. kbtool — validator suite and build pipeline

kbtool is a small Python package whose **source lives only in the
blueprint's `src/kbtool/`** (D15); each KB installs it from its in-repo
`vendor/kbtool.whl` via the pyproject pin, so `uv run kbtool <cmd>` works
with no blueprint access and no credentials. Version integrity is
structural: uv resolves the pin against the wheel's metadata and the lock
records its hash, so a half-applied upgrade (wheel and pin out of step)
fails the very next `uv run` loudly — no custom validator needed
(**[verify-at-impl]** exact uv error behavior on wheel-content change under
a fixed filename). Everything is SSG-independent (F1.3/F1.4) — the SSG is
invoked only as the last step of `build`. Toolchain boundary: the
**validate/build path is Python/uv-only** (works with no Node installed);
Node is required solely by the deploy-adjacent paths — `wrangler` for
deploys (CI) and, when available locally, for `kbtool status` (§7).

### 6.1 Commands

| Command | What it does | Exit ≠ 0 when |
|---|---|---|
| `kbtool check` | All validators: frontmatter schema + vocab; intra-KB link targets exist (including kb:// syntax shape); index reachability (every content page reachable from `docs/index.md` — kills orphans, F3.4); log append-only (§5.4); boundary checksums (§8); slug-consistency triple (§5.3); Markdown lint via **PyMarkdown** (`pymarkdown` — Python/uv, keeps the toolchain Node-free; tuned config shipped as kbtool package data, rule parity with the GitLab-mined set **[verify-at-impl]**); nav.yml entries and globs resolve to existing files | any validator fails |
| `kbtool build` | `check` → preprocess (§6.2) → `zensical build -f .build/mkdocs.yml -s` → post-build assertions (search index exists; `_redirects` copied) | any step fails |
| `kbtool serve` | preprocess → `zensical serve -f .build/mkdocs.yml` (preview serves the preprocessed copy — re-run to pick up source edits) | — |
| `kbtool push` | `git pull --rebase --autostash` → `git push`, retried ×3 with backoff (D5 rebase-retry) | push still rejected |
| `kbtool status` | reports last deployment result (§7) + working-tree cleanliness; used by the session-start ritual (§9) | never (informational) |
| `kbtool playbook <name>` | prints the version-matched procedure shipped as package data (D16): `upgrade`, `ingest`, `lint`, `access-dns-setup` | unknown name |
| `kbtool ci` | alias of `build`; the single platform-owned entry point (F8.2) used by Workers Builds | — |

### 6.2 Preprocess step (the D12/D14 keystone)

1. Copy `docs/` → `.build/docs/` (gitignored).
2. Rewrite links in the copies: `kb://<kb>/<path>.md` (the §5.2 source
   form) → absolute https URL; root-absolute `/a/b.md` → correct relative
   path. Content on disk stays logical; any SSG can consume the output
   **[verified E1 rationale]**.
3. Inject per-page footer line `*Last updated: <date> · from git history*`
   (appended as a `\n\n---\n` separated block) using
   `git log -1 --format=%as -- docs/<original-path>` — always the original
   source path, never the `.build/` copy (D6; build-time timestamp injection
   satisfies OKF `timestamp` recommendation, F2.4).
   **Shallow-clone guard**: if `git rev-parse --is-shallow-repository` is
   true (CI clones may be shallow **[verify-at-impl]** for Workers Builds),
   dates would be silently wrong — the preprocessor must then either
   `git fetch --unshallow` (preferred, if the build environment allows) or
   omit the footer for that build. Never emit a date derived from a shallow
   history.
4. Expand `nav.yml` into an explicit nav tree — this is how the "hybrid
   navigation" requirement (REQUIREMENTS §3) is met without SSG nav plugins:
   `nav.yml` entries are either explicit (`- Home: index.md`) or glob
   sections (`- Concepts: {glob: "concepts/**.md"}`), globs expanded at
   build time to explicit lists sorted by page title (frontmatter `title`,
   H1 fallback for frontmatter-free files). With the nav always complete,
   `validation.nav.omitted_files` can stay fatal-in-strict — a page missing
   from both nav and any glob is a build failure, closing the
   curated-vs-actual drift hole. The **seeded** `nav.yml` must itself
   satisfy this from the first build:

   ```yaml
   - Home: index.md
   - Public: {glob: "public/**.md"}
   - Change log: log.md
   ```

   (New top-level sections are the KB's to add; the seed covers every
   seeded page so scaffold step §10.4 is green out of the box. The seeded
   `docs/index.md` likewise links every seeded page — the public
   placeholder and the change log — so the index-reachability validator
   is also green from the first build.)
5. Generate `.build/mkdocs.yml` = `site-base.yml` (blueprint-owned, shipped
   as kbtool package data — D15: theme, markdown extensions incl. Mermaid
   superfences, strict validation flags, search) + the expanded nav +
   `site_name`/`site_url` from `kb.yml`,
   plus explicit `docs_dir: docs` and `site_dir: site` (both relative to the
   generated file's location, i.e. `.build/docs` and `.build/site`).
   Zensical accepts `-f <path>` **[verified E1 --help]**; that it honors
   `docs_dir`/`site_dir` overrides is **[verify-at-impl]** (E1 used defaults
   only). This generated-config approach eliminates the mixed-ownership
   `mkdocs.yml` (F4.2).

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
Deploy-gate property: a red commit lands in git but never deploys. **Red
deploys must be actively detected**, not assumed noticed: the session-start
ritual (§9) includes `kbtool status`, which reports the latest deployment
result via `npx wrangler deployments list` (exact command/output parsing
**[verify-at-impl]**) and falls back to instructing a dashboard check if the
API is unavailable. This implements F7.2's feedback-at-the-point-of-write for
a no-PR flow.

## 8. Ownership boundary enforcement

`blueprint-checksums.json` is generated at blueprint release time by a
release script that lives in the blueprint repo only (deliberately **not** a
kbtool command — a KB must not be able to casually regenerate its own
boundary manifest and whitewash drift) and is shipped in the template.
With D15/D16 most blueprint-owned material lives *inside the wheel*, so the
checksummed set shrinks to: `vendor/kbtool-<ver>-py3-none-any.whl`,
`.gitattributes`,
`.gitignore`, `CLAUDE.md` (the agent contract is deliberately written
KB-agnostic so it stays static and checksummable; KB specifics live in
`CLAUDE-KB.md`). Files whose rendered content varies per KB
(`wrangler.jsonc`, `pyproject.toml`) instead carry a first-line managed
marker — `// MANAGED BY BLUEPRINT vX.Y.Z — do not edit` in JSONC,
`# MANAGED BY BLUEPRINT vX.Y.Z — do not edit` in TOML/YAML — whose presence
and version `kbtool check` asserts. Residual drift in templated files is
caught as conflicts at the next `copier update` **[verified E2]** — accepted
for v1.

## 9. The CLAUDE.md pair (F3.1)

- `CLAUDE.md` (blueprint-owned, overwritten on upgrade): the agent contract —
  frontmatter/link/log conventions with one example each; the command table
  (§6.1); the session ritual: **start** = read `docs/index.md`, tail of
  `docs/log.md`, run `kbtool status` (catches red deploys from prior
  sessions, §7) and `kbtool check` (catches a dirty inherited tree) — fix
  red state before new work; **before ending** = update `index.md` if pages
  were added/moved, append a `log.md` entry, `kbtool check`, commit,
  `kbtool push`. Imports the KB-owned half via `@CLAUDE-KB.md`.
- `CLAUDE-KB.md` (KB-owned, seeded once): what this KB is about, its page
  types and when to create each, vocabulary rationale, KB-specific rules.

## 10. Scaffold playbook (playbooks/scaffold-kb.md)

**One-time prerequisites** (first scaffold only): create the GitHub org
(D1); transfer `ClaudeKB` (this repo) into it — one home for the whole
fleet, GitHub auto-redirects the old URL, and the Workers Builds GitHub app
then scopes to a single org; install/authorize that app for the org;
complete Cloudflare Zero Trust onboarding (pick the team name — required
once before any Access app can exist).

1. `gh repo create <org>/kb-<name> --private` (org per D1).
2. `uvx copier==<pinned> copy --vcs-ref v<X.Y.Z> gh:<org>/ClaudeKB
   kb-<name>` — answers: slug, title, description (same copier pin as §11.2).
3. Copier post-tasks: `uv lock` (creates `uv.lock`), `git init -b main` +
   initial commit.
4. `uv run kbtool check && uv run kbtool build` locally — must pass before
   the first push.
5. `git remote add origin … && uv run kbtool push`; connect Workers Builds
   to the repo (dashboard; **[docs]** GitHub app flow) with §7 settings;
   first deploy creates the custom domain + DNS record automatically
   (**[docs]** `custom_domain: true`).
6. Run `uv run kbtool playbook access-dns-setup` (D16; skip 6a–6b2 entirely
   when `kb.yml: visibility: public` — §5.5). Every platform-side value set
   here must match the `platform:` record in `kb.yml` (D17):
   a. Access app "kb-<name>" — domain `kb-<name>.example.com`, policy
      Allow, include: Luca's email; IdP: one-time PIN (default).
   b. Access app "kb-<name>-public" — domain
      `kb-<name>.example.com/public`, policy **Bypass**, include:
      Everyone. **[verified live on KB #1 20260712: path app takes
      precedence over the hostname app]**
   b2. Access app "kb-<name>-assets" — domain
      `kb-<name>.example.com/assets`, policy **Bypass**, include:
      Everyone. Required whenever (b) is used, so public pages render styled
      (§5.5). Safe — theme-only namespace; KB media at `/media/` stays
      private.
   c. Verification checklist (LIVE — **all passed on KB #1 kb-sandbox,
      20260712, resolving E4**): `/` → Access login (302 ✓); `/public/` →
      200 ✓ (bypass wins over hostname app); `/assets/…css` → 200 ✓ (public
      pages render styled); `workers.dev` → not resolvable ✓ (workers_dev
      false); `/search.json` → login ✓ (private index, no content leak).
      Record results in `docs/research/`; if wildcard app consolidation is
      preferred, test `kb-*.example.com` as one app.
7. Append scaffold entry to KB's `log.md`; register nothing centrally —
   the fleet is discoverable via `kb.yml` in each repo (F8.1).

## 11. Upgrade machinery (D10)

- Blueprint releases: semver tags. CHANGELOG.md separates breaking /
  non-breaking (REQUIREMENTS §4); entries timestamped `YYYYMMDD HH:MM`.
- Per-KB upgrade = `uv run kbtool playbook upgrade` (D16 — the *installed*
  version prints it, so procedure changes arrive one version late; accepted:
  the procedure is stable, and any special per-release instructions live in
  the CHANGELOG read in step 1):
  1. Read CHANGELOG between `.copier-answers.yml:_commit` and target tag.
  2. `uvx copier==<pinned> update --vcs-ref v<target>` — copier itself is
     version-pinned in the playbooks (a copier major could change update
     semantics mid-fleet; the pin moves only via blueprint releases).
     Conflicts expected **only** if
     the boundary was violated (E2); resolve favoring the blueprint, then fix
     the KB-side need properly (usually: move the customization to a KB-owned
     file or file a blueprint issue).
  3. Copier `_migrations` run automatically for crossed versions (mechanical
     changes; v1 ships none — the mechanism is first exercised, under the
     §12 upgrade test, by whichever release first needs one); CHANGELOG
     lists **content playbooks** (agent-executed, e.g. frontmatter
     migrations across articles) the agent runs now (F4.4).
  4. `uv run kbtool check && uv run kbtool build`; commit with the blueprint
     version in the message; `kbtool push`; append `log.md` entry.
- Fleet upgrades are per-KB and independent — no orchestration in v1.

## 12. Blueprint CI (GitHub Actions, blueprint repo only)

On PR + main push (budget: well under D1's 2,000 min/mo — one small job):
1. Scaffold a fixture KB from the CI checkout (committed `HEAD`, not a dirty
   tree — copier needs a git ref); **rebuild the wheel from `src/kbtool/`
   into the fixture's `vendor/`** and **regenerate
   `blueprint-checksums.json` inside the fixture** (mid-development, the
   template's shipped wheel and checksums legitimately lag `src/`), then run
   `uv run kbtool ci` — the scaffold must always produce a green KB (F4.5).
2. Upgrade test: scaffold a second fixture from the **latest release tag**
   (template source = the runner's absolute checkout path — absolute local
   paths work for update, relative ones don't **[verified E2]**), then
   `copier update --vcs-ref <CI HEAD sha>` (a sha is a valid ref; copier
   updates between any two template refs), then rebuild the wheel from
   `src/kbtool/` into the updated fixture (the template's shipped wheel
   lags `src/` mid-development, same as job 1); assert zero conflicts and
   green `kbtool ci` — guarantees released upgrades don't break clean KBs.
   **Bootstrap**: skipped (with a visible notice) while no release tag
   exists yet; mandatory from v1.0.0 on.
3. Release procedure (ordered, breaking the checksum circularity): finalize
   CHANGELOG entry (timestamped, breaking/non-breaking separated) → build
   the wheel from `src/kbtool/` into `template/vendor/kbtool.whl` and bump
   the template's pyproject pin → regenerate `blueprint-checksums.json`
   from the template → commit → tag `vX.Y.Z` → push commit + tag. CI on the
   tag asserts wheel version == pyproject pin == tag, checksums match the
   tagged tree, and the CHANGELOG has the version's entry.

KB repos get **no** GitHub Actions in v1 — the deploy gate is Workers Builds
(D5); forge CI minutes stay unspent.

## 13. Maintenance playbooks (D13, D16, F3.2)

Delivered inside the kbtool package; agents fetch the version-matched
procedure with `uv run kbtool playbook <name>`:

- `ingest`: how agents add knowledge — where pages go, when to create vs
  extend (defer to CLAUDE-KB.md specifics), always: frontmatter, index.md
  entry, log.md entry, `kbtool check`, push.
- `lint` (scheduled agent session, e.g. monthly per KB): structural pass
  (`kbtool check` + lychee external-link sweep) then semantic pass
  (contradictions, staleness, orphan-in-spirit pages, missing
  cross-references — F3.2); findings fixed directly or filed as `status:
  review` pages; session logged in log.md.

## 14. Success criteria

Blueprint v1 is done when: (a) blueprint CI (§12) is green including the
upgrade test; (b) KB #1 scaffolds via §10 in ≤ 1 hour of agent time with
zero manual **file edits** (the dashboard steps in §10.5–10.6 are expected
manual actions, scripted where the API allows); (c) the live checklist in
§10.6c passes — all four Access/workers.dev probes behave as specified;
(d) two parallel agent sessions writing to KB #1 both land (D5 + E3
mechanics) with no lost writes; (e) a no-op `copier update` on KB #1
produces zero conflicts.

## 15. Risks and mitigations

| Risk | Class | Mitigation |
|---|---|---|
| Zensical 0.0.x churn breaks a build | when | version pin; upgrades only via blueprint releases tested by §12; Material fallback (§6.3) |
| Workers Builds image lacks uv | if | §7 verify-at-impl; installer prepend is the known fallback |
| Access misconfig exposes private content | if | §10.6c live checklist is a launch gate per KB; `visibility` in kb.yml drives the playbook; search/sitemap stay behind Access (§5.5) |
| Public pages leak private page *titles* via global nav | accepted | documented in §5.5 + CLAUDE.md rule (titles must not be sensitive); split build is the backlog fix |
| Agent violates boundary/conventions | when | §8 validator + CLAUDE.md contract + E2's recurring-conflict pain surfacing at upgrade |
| log.md union-merge corruption via mid-file edit | if | pre-commit append-only validator (§5.4); residual bypass (commit without check) accepted per §5.4 — damage is cosmetic, git retains history |
| Blueprint upgrade breaks all KBs at once | if | §12 upgrade test on every release; per-KB independent upgrades allow halting after the first bad one |

## Iteration log

- pass 0 (20260712 11:31): preliminary draft written.
- pass 1 (20260712 11:38): 2 HIGH, 10 MEDIUM, 6 LOW — all fixed. H: red-deploy
  detection was claimed but unimplemented (added `kbtool status` + ritual);
  git-date footer silently wrong under shallow clones (guard added). M: empty
  `public/` dir untrackable (placeholder); index.md/log.md frontmatter policy
  resolved (none, OKF-aligned, all directories); path→URL mapping rule
  specified; `docs_dir`/`site_dir` overrides made explicit + verify-at-impl;
  org + blueprint-repo-transfer prerequisites added; CI upgrade-test refs
  made concrete (sha as ref); checksum staleness in CI fixed (regenerate in
  fixture); log append-only baseline defined (`HEAD` version is prefix);
  media conventions added (§5.6); fully-public KB variant added. L: stale
  `site/` gitignore entry; cross-KB broken-link tolerance stated; Access
  path-precedence assumption tagged as probe #2; release ordering made
  explicit; success-criterion wording (manual dashboard steps vs file
  edits); `_migrations` v1 status noted.
- pass 2 (20260712 11:47): 6 MEDIUM, 8 LOW — all fixed. M: hybrid-nav vs
  strict `omitted_files` conflict resolved via nav.yml glob-expansion DSL;
  log append-only semantics made precise (pre-commit baseline, inductive
  guarantee, stated residual risk); public pages leak private titles via
  global nav — surfaced as accepted v1 risk + CLAUDE.md authoring rule;
  markdownlint (Node) replaced with PyMarkdown (uv-native, parity
  verify-at-impl); Zero Trust one-time onboarding added to prerequisites;
  slug-consistency triple validator added. L: REQUIREMENTS-§4 reference
  disambiguated; footer git-log path pinned to original source; managed
  markers per file syntax; CLAUDE.md made static + checksummed; scaffold
  remote/push sequencing; CI upgrade-test template source path; assets
  organized by owning-page path; §5.5 validator-enforcement overclaim
  trimmed.
- pass 3 (20260712 11:56): 4 MEDIUM, 7 LOW — all fixed. M: seeded nav.yml
  now specified (covers log.md + public placeholder, else first build fails
  strict); Node-free claim scoped precisely (validate/build Python-only;
  wrangler for deploy/status); CI upgrade-test bootstrap rule (skip until
  first tag); copier itself version-pinned in playbooks. L: any-log.md
  frontmatter exemption consistency; OKF frontmatter-free claim precision
  (explicit for index.md, extended by us to log.md); serve command config
  flag + staleness note; Access playbook branches on visibility; glob sort
  defined (title, H1 fallback); tests/ dir comment; §15 log-risk row aligned
  with §5.4 residual.
- pass 4 (20260712 12:01): 2 MEDIUM, 2 LOW — all fixed. M: seeded index.md
  must link all seeded pages (reachability green on first build); checksum
  regeneration confined to a blueprint-side release script, not kbtool
  (whitewash prevention). L: copier pin applied to scaffold step too;
  visibility flip procedure noted in kb.yml.
- pass 5 (20260712 12:06): 1 HIGH, 1 LOW, 1 cosmetic — all fixed. H: the
  pass-3 edit of §5.1 had dropped the required-field list (`type`, `title`,
  `description`) from the schema definition — restored. L: kb:// notation
  aligned between §5.2 and §6.2.2. Cosmetic: §8 splice line-wrap.
- pass 6 (20260712 12:10): 1 LOW — fixed. `.gitignore` was the only
  blueprint-owned static file protected by neither checksum nor marker;
  added to the checksummed set.
- pass 7 (20260712 12:12): zero findings at any severity — exit. Status
  flipped to reviewed.
- pass 8 (20260712 12:05, checkpoint 3 amendment): Luca's self-definition
  principle adversarially validated → D15–D18 recorded in REQUIREMENTS and
  applied here: kbtool distributed as an in-repo wheel (source only in
  blueprint `src/kbtool/`); playbooks + site-base.yml + frontmatter schema +
  lint config become package data (`kbtool playbook <name>`); KB layout
  loses `tools/`, `config/`, `schema/`, `pymarkdown.json`, gains
  `vendor/kbtool.whl`; kb.yml gains the `platform:` record (D17); §8
  checksummed set shrinks accordingly; CI + release build the wheel.
- pass 10 (20260712 16:54, post-launch fix, blueprint v0.1.1): live KB #1
  surfaced that a `/public`-only Access bypass leaves public pages unstyled
  (theme CSS/JS at `/assets/` stay gated). Fix: add a third `/assets` Bypass
  app (safe — theme-only) and relocate KB media `docs/assets/` → `docs/media/`
  so the wholesale `/assets` bypass can't expose private-page images. §5.5,
  §5.6, §10.6, playbooks, kb.yml, CLAUDE.md updated. All other E4 assumptions
  verified live and marked resolved.
- pass 9 (20260712 12:10, re-review of the amendment): 3 findings fixed —
  playbook names unified (`ingest`/`lint` vs old file names); platform-record
  drift on upgrades handled via CHANGELOG instruction (kb.yml is KB-owned,
  never silently rewritten); CI upgrade test also rebuilds the wheel
  post-update (template wheel lags src/ mid-development). Second sweep of
  the amended sections: zero findings — exit.

# Loop 2 — empirical verification results

> Executed 20260712 11:05–11:13 locally (macOS, uv, git 2.x). Every claim below
> was observed, not read. Fixture: 4-page toy KB (frontmatter per D6+D11,
> Mermaid, relative + bundle-root-absolute links, /public/ page).

## E1 — SSG bake-off: pinned MkDocs Material vs Zensical

Same content, same `mkdocs.yml`, separate uv venvs.

| Check | A: MkDocs 1.6.1 + Material 9.7.6 | B: Zensical **0.0.50** |
|---|---|---|
| Build (toy scale) | ~0.14 s | ~0.24 s (plus first-run cache init) |
| Strict mode fails on dead link | ✅ exit 1 | ✅ exit 1 (`-s` flag) |
| Bundle-root-absolute links (D12) | ✅ **native**: `validation.links.absolute_links: relative_to_docs` validates AND rewrites to correct relative hrefs | ❌ "page does not exist" warning; emitted **broken** as literal `href="/concepts/alpha.md"`; strict build fails |
| Mermaid via superfences | ✅ | ✅ |
| Search index | ✅ `search/search_index.json` | ✅ `search.json` + worker JS ("Disco") |
| Admonitions, Material theme | ✅ | ✅ (same lineage) |
| Output size (files) | 51 | 16 (leaner) |
| Reads unknown frontmatter (`type`) silently | ✅ | ✅ |
| Notes | Prints a red MkDocs-2.0 ecosystem warning banner on every run | Pre-1.0 version number; CLI: `new`/`build`/`serve` |

**E1 verdict**: both candidates build the KB correctly except D12 handling.
The Zensical gap is neutralized by a step we already committed to for other
reasons: the `kb://` resolver (D12) runs as our own preprocessor before the
SSG; extending it to also rewrite root-absolute → relative makes the *content*
build correctly on **any** SSG (doctrine F1.3/F1.4 made concrete). With that
step in the pipeline, the SSG choice stops being gated on link handling.
→ Decision for the maintainer at checkpoint 2 (see §5 below).

## E2 — copier update-conflict behavior (F4.3, gates D10)

Local template repo (tags v1/v2/v3) + scaffolded project repo.

- **Conflict handling**: `copier update` performs a 3-way merge and leaves
  **inline git conflict markers** with the working tree in unmerged (`UU`)
  state. Nothing is lost silently. ✅ acceptable for agent resolution.
- **Granularity is hunk-level**: template and KB edits to *different but
  nearby* lines of the same file still conflict. Expect conflicts as the norm
  when boundaries are violated, not the exception.
- **KB edits to blueprint-owned files are a RECURRING tax**: the same local
  divergence re-conflicts on every subsequent update. Consequence: the
  boundary must be machine-enforced — blueprint ships a validator asserting
  blueprint-owned files match their template-version checksums (ownership
  boundary becomes structural, resolving the enforcement half of open Q2).
- **`_skip_if_exists` works as the KB-owned shield**: with `content/**`
  listed, template changes to seed content no longer touch or conflict with
  KB files. ✅ KB-owned paths = `_skip_if_exists` (seeded once) or absent
  from the template entirely.
- **Gotchas for the blueprint**: (1) `.copier-answers.yml` exists only if the
  template ships `{{ _copier_conf.answers_file }}.jinja` — must be in the
  blueprint template; (2) `_src_path` must be a stable git URL — relative
  paths break `copier update` (observed: `ValueError: Local template must be
  a directory`); (3) answers file records `_commit: v<tag>` — semver tag
  discipline on blueprint releases is what update targeting runs on.

**E2 verdict: D10 confirmed** — copier is the scaffold/upgrade engine.
Upgrade playbook shape: `copier update` → agent resolves conflicts (rare if
boundary enforced) → validators → commit.

## E3 — log.md union-merge (F3.3, gates D13 contingency)

`.gitattributes: log.md merge=union`; two sessions appending concurrently.

- **Merge flow**: both entries survive, no conflict. ✅
- **Rebase flow (the actual D5 rebase-retry path)**: union driver applies
  during rebase too; both entries survive; fast-forward push-equivalent
  clean. ✅
- **Caveats observed**: blank line between concurrent entries collapsed —
  entry format must be a self-contained block tolerant of adjacency (each
  entry starts `## <timestamp> <op> | <title>`). Union merge is only safe
  for append-only usage; mid-file edits could merge wrongly and silently —
  add a cheap validator: previous log content must be a prefix-modulo-
  whitespace of the new content.
- Invalid first attempt (default branch name mismatch) caught and redone —
  recorded here because the *passing-looking* output of a broken test is
  exactly what "verify empirically" exists to catch.

**E3 verdict: D13 contingency resolved — log.md is IN** (union driver +
append-only validator + self-contained entry blocks).

## E4 — Cloudflare assumptions (docs-level; live test still pending)

| Assumption (REQUIREMENTS §6) | Status |
|---|---|
| `/public/*` Bypass inside a private site | **Confirmed in docs**: second Access app scoped to `host/path` with Bypass+Everyone is Cloudflare's documented pattern for exactly this. Caveat: bypassed traffic is not logged. |
| `workers.dev` lockdown | **Confirmed in docs**: `workers_dev = false` in wrangler config; since wrangler 4.44 preview URLs default to matching that setting — blueprint sets both explicitly anyway. |
| One Access app covers `kb-*.example.com` via wildcard | **Still unverified** — but demoted from blocker to convenience: multi-domain single app and templated per-KB apps (Terraform/API examples in docs) are both confirmed patterns. Resolve during live setup. |

Live-zone verification (real Access apps against a deployed toy Worker)
remains queued — needs the maintainer's Cloudflare auth; do during architecture phase.

## 5. Checkpoint 2 input — the SSG decision

With the preprocessor in the pipeline (needed for `kb://` regardless), both
candidates are viable and mutually fallback-able, since content stays
SSG-independent:

- **Zensical now**: no known-EOL foundation for brand-new KBs; Backstage RFC
  momentum; leaner output; risk = 0.0.x churn/parity gaps → mitigated by
  blueprint-pinned versions and cheap fallback to A.
- **Pinned Material now, migrate later**: maximum today-maturity; native D12
  handling; risk = guaranteed migration work inside ~12-month fuse, and the
  first blueprint upgrade is also the riskiest kind (SSG swap).

Recommendation (adversarially argued in session): **Zensical, version-pinned,
with pinned Material as the documented fallback** — but this is the maintainer's call.

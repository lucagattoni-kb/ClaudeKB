# Roadmap

Where the project stands and what's next. This is a living document; the
design and its decisions (D1–D18) are recorded in the
[architecture spec](../architecture.md).

## Done

- **Blueprint v0.1.x** — `kbtool` toolchain, copier template, validators, build
  pipeline, release + CI machinery. Verified end-to-end.
- **KB #1 (`kb-sandbox`) live** — scaffolded, gated, deployed to Cloudflare
  Workers, private-by-default behind Cloudflare Access with a working public
  subsection. Every deferred infra assumption (E4) resolved on the live site.
- **First fleet upgrades** — `kb-sandbox` upgraded v0.1.0 → v0.1.1 → v0.1.2
  → v0.2.0, all zero-conflict.
- **`kbtool verify-access`** (v0.2.0) — the launch checklist as a no-credential
  command: anonymous probes asserted against the `kb.yml` record.
- **Domain parameterization** (v0.3.0) and the **blueprint published** as an
  open repository with a rewritten, sanitized history.
- **Public-KB guardrails** (v0.4.0) — secret scan in `kbtool check` (error on
  public KBs, warning on private) + publish-safe commit identity in the
  scaffold; see [Public vs private KBs](public-and-private-kbs.md).

## Next (near-term)

1. **Second real KB.** Exercise scaffold + Access on a KB you'll actually keep;
   confirm the per-KB dashboard steps are as quick as expected at n=2.
2. **Docs polish / MkDocs preview** of this guide (dogfood the SSG on the
   blueprint's own docs).

## Deferred (deliberate)

- **Platform write-provisioning (`kbtool provision`).** Automating the
  Cloudflare Access/DNS/deploy setup would need a broadly-scoped account API
  token — a real security liability, and notably *less* safe than the current
  Workers Builds model, where no token we manage touches the deploy path.
  Access is the security boundary; scripting it adds a failure mode (a policy
  bug exposing private content). **Revisit only if** the fleet grows enough that
  the per-KB dashboard toil justifies it — and if so, scope the token minimally
  (single zone: DNS + Access edit, not account-wide) and keep it in a secret
  manager, never the repo. The `kb.yml` `platform:` record was designed so this
  can be added later without changing any KB.

## Future extensions (designed for, not built)

- **Unified cross-KB search** — an aggregator that reads each KB's `kb.yml` and
  merges per-KB search indexes.
- **MCP / RAG retrieval layer** over the Markdown — evaluate reusing an existing
  local-first tool (e.g. Basic Memory) before building.
- **Offline reading.**
- **Backlinks emitter** — derive per-page backlinks from the link graph the
  validator already builds (Quartz-style reader UX).
- **Split public/private build** — the real fix for the two shared-build
  limitations (public pages leak private *titles* via the global nav; public
  pages can't show private raster images). Would let public sections ship with
  their own assets and nav.
